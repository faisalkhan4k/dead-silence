"""Train a non-deployed breath model using weak, automatically marked clips."""
import hashlib,json,pickle,uuid
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score,balanced_accuracy_score,confusion_matrix
from breath_live import DATA,HERE,MODEL,N,RATE,LABELS,examples,feature

ROOT=HERE/'breath_noise_dataset'

def windows(split, selected=None):
    xs,ys=[],[];counts=Counter();hashes=set();clips=0
    for meta_file in sorted(ROOT.glob('*/metadata.json')):
        meta=json.loads(meta_file.read_text(encoding='utf-8-sig'))
        if meta.get('split')!=split or meta.get('clipped') or meta.get('audio_flags'):continue
        if selected is not None and meta_file.parent.name not in selected:continue
        path=meta_file.parent/'mic.wav';ann=meta_file.parent/'annotations.json'
        if not ann.exists() or not path.exists():continue
        data=path.read_bytes();digest=hashlib.sha256(data).hexdigest();hashes.add(digest)
        rate,x=wavfile.read(path)
        if rate!=RATE or x.ndim!=1:raise ValueError('Unexpected audio format')
        if np.issubdtype(x.dtype,np.integer):x=x.astype(float)/np.iinfo(x.dtype).max
        markers=json.loads(ann.read_text(encoding='utf-8'))
        if markers['sample_rate']!=rate or markers['total_samples']!=len(x):raise ValueError('Annotation mismatch')
        if selected is not None and meta.get('category') in ('INHALE','EXHALE') and markers.get('review_status')=='PROVISIONAL_AUTOMATIC':raise ValueError('Selected breath marker has not been reviewed')
        clips+=1
        for seg in markers['segments']:
            label='SILENCE' if seg['label']=='NO_BREATH' else seg['label']
            if label not in LABELS:raise ValueError('Unexpected label')
            start,end=seg['start_sample'],seg['end_sample']
            if not 0<=start<end<=len(x):raise ValueError('Invalid marker')
            for i in range(start,end-N+1,N):xs.append(feature(x[i:i+N]));ys.append(label);counts[label]+=1
    if not xs:raise ValueError('No labeled windows for '+split)
    return np.asarray(xs),np.asarray(ys),dict(counts),hashes,clips

def score(model,X,y):
    pred=model.predict(X)
    return {'window_accuracy':float(accuracy_score(y,pred)),'balanced_accuracy':float(balanced_accuracy_score(y,pred)),
            'labels':LABELS,'confusion_matrix':confusion_matrix(y,pred,labels=LABELS).tolist(),'windows':len(y)}

def main():
    old_train,old_y=examples('train');old_test,old_test_y=examples('test')
    selection=json.loads((ROOT/'annotation_subset.json').read_text(encoding='utf-8'))['clips']
    selected={item['folder'] for item in selection if item['split']=='train'}
    train,y,train_counts,train_hashes,train_clips=windows('train',selected)
    if train_clips!=len(selected):raise ValueError('Some selected training clips are missing or unusable')
    test,yt,test_counts,test_hashes,test_clips=windows('held-out')
    if train_hashes & test_hashes:raise ValueError('Identical audio exists in train and held-out; resolve before training.')
    original=pickle.loads((DATA/'window50_model.pkl').read_bytes())
    active=pickle.loads(MODEL.read_bytes())
    candidate=RandomForestClassifier(n_estimators=100,max_depth=8,min_samples_leaf=4,random_state=42,n_jobs=2,class_weight='balanced')
    candidate.fit(np.vstack([old_train,train]),np.r_[old_y,y])
    out=ROOT/'experiments'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
    (out/'candidate.pkl').write_bytes(pickle.dumps(candidate))
    results={'warning':'Original action-window labels and unreviewed noisy held-out amplitude markers are weak. No-breath training clips have whole-clip intended labels. Held-out metrics are proxies, not verified accuracy. Windows from one clip are correlated. Candidate is not deployed.',
             'training_selection':'reviewed 16 breath clips and 8 clip-level no-breath labels plus original training','train_clips':train_clips,'test_clips':test_clips,'new_train_windows_by_label':train_counts,'new_test_windows_by_label':test_counts,
             'old_holdout':{'original':score(original,old_test,old_test_y),'candidate':score(candidate,old_test,old_test_y)},
             'noisy_holdout_weak':{'original':score(original,test,yt),'active':score(active,test,yt),'candidate':score(candidate,test,yt)}}
    (out/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    try:
        import mlflow
        mlflow.set_tracking_uri('sqlite:///'+(HERE/'breath_mlflow.db').as_posix());mlflow.set_experiment('breath-live')
        with mlflow.start_run(run_name='reviewed-breath-candidate'):
            mlflow.log_params({'window_ms':50,'model':'random_forest','training':'original+reviewed_subset','test_labels':'provisional_amplitude_markers','candidate_deployed':'false'})
            for dataset in ('old_holdout','noisy_holdout_weak'):
                for name in results[dataset]:
                    for metric in ('window_accuracy','balanced_accuracy'):
                        mlflow.log_metric(f'{dataset}_{name}_{metric}',results[dataset][name][metric])
            mlflow.log_artifact(str(out/'results.json'))
        results['mlflow']='logged'
    except Exception as exc: results['mlflow']='failed: '+str(exc)
    print('Experiment:',out)
    print(json.dumps(results,indent=2))

if __name__=='__main__':main()
