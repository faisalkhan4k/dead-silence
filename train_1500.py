"""Train a non-deployed 1.5-second breath classifier on whole recording splits."""
import hashlib
import json
import pickle
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix
import breath_live as live

ROOT = live.HERE / 'breath_noise_dataset'
SOURCE = ROOT / 'experiments/20261108T102800Z-cfc08b43/results.json'
FRAMES = 30
LENGTH = live.N * FRAMES


def read_audio(path):
    rate, x = wavfile.read(path)
    if rate != live.RATE or x.ndim != 1:
        raise ValueError(f'Unexpected audio format: {path}')
    if np.issubdtype(x.dtype, np.integer):
        x = x.astype(float) / np.iinfo(x.dtype).max
    return np.asarray(x, dtype=np.float32)


def features(samples):
    if len(samples) != LENGTH:
        raise ValueError('Expected exactly 1.5 seconds')
    frames = np.asarray([live.feature(samples[i:i+live.N]) for i in range(0, LENGTH, live.N)])
    return np.concatenate((frames.mean(axis=0), frames.std(axis=0)))


def original(split):
    role = 'train' if split == 'train' else 'test'
    data = json.loads((live.DATA / f'{role}_accepted.json').read_text())
    result = []
    for row in data.values():
        path = Path(row['path'])
        x = read_audio(path)
        # Select 1.5 seconds within the original 1.1 to 2.9 second action-cue region.
        start = int(1.1 * live.RATE)
        segment = x[start:start+LENGTH]
        if len(segment) != LENGTH:
            raise ValueError(f'Incomplete original recording: {path}')
        result.append((segment, row['label'], 'original', row['recording_id'], hashlib.sha256(path.read_bytes()).hexdigest()))
    return result


def fresh(split):
    items = json.loads(SOURCE.read_text(encoding='utf-8'))['manifest']
    # Add the later dedicated no-breath collection, preserving its recorded split.
    seen = {item['clip'] for item in items}
    for meta_path in sorted(ROOT.glob('*/metadata.json')):
        meta = json.loads(meta_path.read_text(encoding='utf-8-sig'))
        if (meta_path.parent.name not in seen and meta.get('utc', '') > '2026-11-08T10:27:03'
                and meta.get('category') == 'NO_BREATH' and meta.get('split') in ('train', 'held-out')
                and not meta.get('clipped') and not meta.get('audio_flags')):
            audio_path = meta_path.parent / 'mic.wav'
            items.append({'clip': meta_path.parent.name, 'split': meta['split'], 'label': 'SILENCE',
                          'sha256': hashlib.sha256(audio_path.read_bytes()).hexdigest()})
    result, skipped = [], Counter()
    for item in items:
        if item['split'] != split:
            continue
        path = ROOT / item['clip'] / 'mic.wav'
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != item['sha256']:
            raise ValueError(f'Audio changed since manifest: {path}')
        x = read_audio(path)
        if len(x) < LENGTH:
            skipped[item['label']] += 1
            continue
        start = (len(x) - LENGTH) // 2
        result.append((x[start:start+LENGTH], item['label'], 'fresh', item['clip'], digest))
    return result, dict(skipped)


def report(model, rows, baseline):
    if not rows:
        return None
    y = [row[1] for row in rows]
    X = np.asarray([features(row[0]) for row in rows])
    predicted = model.predict(X)
    # Aggregate the existing 50 ms model across the exact same 1.5-second segment.
    baseline_y = []
    for audio, *_ in rows:
        vectors = np.asarray([live.feature(audio[i:i+live.N]) for i in range(0, LENGTH, live.N)])
        votes = baseline.predict(vectors)
        counts = Counter(votes)
        baseline_y.append(max(live.LABELS, key=lambda label: counts[label]))
    def score(p):
        return {'accuracy': float(accuracy_score(y,p)),
                'balanced_accuracy_present_classes': float(balanced_accuracy_score(y,p)),
                'confusion_matrix': confusion_matrix(y,p,labels=live.LABELS).tolist(),
                'clip_counts': dict(Counter(y)), 'clips': len(y)}
    return {'model_1500':score(predicted),'baseline_50ms_majority':score(baseline_y)}


def main():
    old_train, old_test = original('train'), original('held-out')
    new_train, skipped_train = fresh('train')
    new_test, skipped_test = fresh('held-out')
    train, test = old_train + new_train, old_test + new_test
    if {x[4] for x in train} & {x[4] for x in test}:
        raise ValueError('Duplicate recording across training and held-out splits')
    if set(row[1] for row in train) != set(live.LABELS):
        raise ValueError('Training is missing a class')
    X = np.asarray([features(row[0]) for row in train])
    y = [row[1] for row in train]
    model = RandomForestClassifier(n_estimators=200,max_depth=8,min_samples_leaf=2,
                                   random_state=42,n_jobs=1,class_weight='balanced')
    model.fit(X,y)
    baseline = pickle.loads(live.BASELINE_MODEL.read_bytes())
    result = {'warning':'Clip labels are weak; 1.5-second segments can contain pauses or noise. Fresh held-out recordings were collected near training. Long clips only; original held-out has no silence and fresh held-out has only two inhale clips. Clip-level offline metrics do not measure live accuracy or latency.',
              'window_ms':1500,'hop_for_future_live_ms':50,'feature':'mean and standard deviation of six 50 ms log-band energies across 30 consecutive frames',
              'labels':live.LABELS,'train_counts':dict(Counter(row[1] for row in train)),
              'skipped_fresh_shorter_than_1500ms':{'train':skipped_train,'held-out':skipped_test},
              'original_held_out':report(model,old_test,baseline),
              'fresh_held_out':report(model,new_test,baseline),
              'manifest':[{'split':split,'source':r[2],'id':r[3],'label':r[1],'sha256':r[4]} for split,rows in [('train',train),('held-out',test)] for r in rows]}
    out = ROOT/'experiments'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-1500ms-'+uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    (out/'candidate.pkl').write_bytes(pickle.dumps({'model':model,'window_ms':1500,'frame_ms':50,'feature':'mean_std_6band_v1','classes':live.LABELS}))
    (out/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    try:
        import mlflow
        mlflow.set_tracking_uri('sqlite:///'+(live.HERE/'breath_mlflow.db').as_posix())
        mlflow.set_experiment('breath-live')
        with mlflow.start_run(run_name='candidate-1500ms'):
            mlflow.log_params({'window_ms':1500,'frame_ms':50,'model':'random_forest','label_quality':'weak_clip_level','deployed':False,'training_clips':len(train)})
            for group in ('original_held_out','fresh_held_out'):
                if result[group]:
                    for name,metrics in result[group].items():
                        for metric in ('accuracy','balanced_accuracy_present_classes'):
                            mlflow.log_metric(f'{group}_{name}_{metric}',metrics[metric])
            mlflow.log_artifact(str(out/'results.json'))
        print('MLflow: logged')
    except Exception as exc:
        print('MLflow failed:',exc)
    print('EXPERIMENT:',out)
    print(json.dumps({k:v for k,v in result.items() if k != 'manifest'},indent=2))


if __name__ == '__main__':
    main()
