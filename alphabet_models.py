"""Fixed acoustic baselines and reusable probability exports. No context decoding."""
import csv
import hashlib
import inspect
import json
import pickle
from pathlib import Path

import lightgbm
import numpy as np
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, log_loss
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from dataset_pilot import features, save_json


def lightgbm_model():
    return lightgbm.LGBMClassifier(n_estimators=150, learning_rate=.05, num_leaves=7,
                                  max_depth=3, min_child_samples=5, reg_lambda=1,
                                  random_state=42, n_jobs=2, verbosity=-1)


def baseline_models(calibration_folds=5):
    return {
        'SVM': CalibratedClassifierCV(make_pipeline(StandardScaler(), SVC(C=1, kernel='rbf')),
                                      method='sigmoid', cv=calibration_folds, ensemble=False),
        'RandomForest': RandomForestClassifier(n_estimators=200, max_depth=5,
                                               min_samples_leaf=2, random_state=42, n_jobs=2),
        'LightGBM': lightgbm_model(),
    }


def read_examples(path, labels, count):
    saved = json.loads(Path(path).read_text(encoding='utf-8'))
    rows = [saved[key] for key in sorted(saved, key=int)]
    targets = [row['label'] for row in rows]
    if len(rows) != len(labels)*count or any(targets.count(label) != count for label in labels):
        raise ValueError('Expected the complete balanced session for all labels.')
    paths = [row['path'] for row in rows]
    if len(set(paths)) != len(paths):
        raise ValueError('A recording appears more than once.')
    X = np.asarray([row['features'] for row in rows], dtype=float)
    if X.shape != (len(rows), 72) or not np.isfinite(X).all():
        raise ValueError('Feature vectors must contain 72 finite values.')
    return rows, X, np.asarray(targets)


def probability_report(model, X, y, rows, labels):
    classes = list(model.classes_)
    if set(classes) != set(labels):
        raise ValueError('Model class vocabulary differs from the experiment.')
    probabilities = model.predict_proba(X)[:, [classes.index(label) for label in labels]]
    return report_probabilities(probabilities, y, rows, labels)


def report_probabilities(probabilities, y, rows, labels):
    probabilities = np.asarray(probabilities, dtype=float)
    if probabilities.shape != (len(rows), len(labels)) or not np.isfinite(probabilities).all():
        raise ValueError('Invalid probability matrix.')
    if np.any(probabilities < 0) or not np.allclose(probabilities.sum(axis=1), 1):
        raise ValueError('Probabilities must be nonnegative and sum to one.')
    ranks = np.argsort(-probabilities, axis=1, kind='stable')
    predictions = np.asarray(labels)[ranks[:, 0]]
    top3 = np.asarray(labels)[ranks[:, :min(3, len(labels))]]
    exports = []
    for row, actual, predicted, scores, rank in zip(rows, y, predictions, probabilities, ranks):
        exports.append(dict(recording=row['path'], recording_id=row.get('recording_id'),
                            actual=str(actual), predicted=str(predicted),
                            probabilities=dict(zip(labels, scores.tolist())),
                            top3=[labels[index] for index in rank[:3]]))
    return dict(accuracy=float(accuracy_score(y, predictions)),
                top3_accuracy=float(np.mean([actual in choices for actual,choices in zip(y, top3)])),
                log_loss=float(log_loss(y, probabilities[:, np.argsort(labels)], labels=sorted(labels))),
                labels=labels, n=len(rows), prediction_rule='argmax of class probabilities',
                per_class=classification_report(y, predictions, labels=labels, output_dict=True, zero_division=0),
                confusion_matrix=confusion_matrix(y, predictions, labels=labels).tolist(), predictions=exports)


def feature_hash():
    return hashlib.sha256(inspect.getsource(features).encode()).hexdigest()


def freeze_training(project, config, labels):
    project = Path(project)
    bundle_path = project/'models.pkl'
    if bundle_path.exists():
        bundle = pickle.loads(bundle_path.read_bytes())
        if bundle['config'] != config or bundle['features_sha256'] != feature_hash() or bundle['training_sha256'] != hashlib.sha256((project/'train_accepted.json').read_bytes()).hexdigest():
            raise ValueError('Frozen training inputs or configuration changed.')
        save_json(project/'training_fit.json', bundle['training_fit'])
        write_predictions(project, 'training', bundle['training_fit'])
        write_run_readme(project, bundle['training_fit'], None, config)
        return bundle
    rows, X, y = read_examples(project/'train_accepted.json', labels, config.get('train_per_label',10))
    models = baseline_models(config.get('calibration_folds',5))
    reports = {}
    for name, model in models.items():
        model.fit(X, y)
        reports[name] = probability_report(model, X, y, rows, labels)
    # The model and its provenance travel together in one atomic file.
    bundle = dict(models=models, config=config, labels=labels, features_sha256=feature_hash(),
                  training_sha256=hashlib.sha256((project/'train_accepted.json').read_bytes()).hexdigest(),
                  versions=dict(sklearn=sklearn.__version__, lightgbm=lightgbm.__version__, numpy=np.__version__),
                  training_fit=reports)
    temporary = project/'models.tmp'
    temporary.write_bytes(pickle.dumps(bundle))
    temporary.replace(bundle_path)
    save_json(project/'training_fit.json', reports)
    write_predictions(project, 'training', reports)
    write_run_readme(project, reports, None, config)
    return bundle


def evaluate_frozen(project, config, labels):
    project = Path(project)
    destination = project/'evaluation.json'
    # Only load application-created local pilot artifacts.
    bundle = pickle.loads((project/'models.pkl').read_bytes())
    if bundle['config'] != config or bundle['labels'] != labels or bundle['features_sha256'] != feature_hash():
        raise ValueError('The frozen configuration or feature implementation changed.')
    if bundle['training_sha256'] != hashlib.sha256((project/'train_accepted.json').read_bytes()).hexdigest():
        raise ValueError('Training examples changed after model freezing.')
    if destination.exists():
        results = json.loads(destination.read_text(encoding='utf-8'))
        write_evaluation_reports(project, bundle, results)
        return results
    rows, X, y = read_examples(project/'test_accepted.json', labels, config.get('test_per_label',5))
    train, _, _ = read_examples(project/'train_accepted.json', labels, config.get('train_per_label',10))
    if {r['path'] for r in train} & {r['path'] for r in rows}:
        raise ValueError('Training and test recordings overlap.')
    results = {name:probability_report(model, X, y, rows, labels) for name,model in bundle['models'].items()}
    save_json(destination, results)
    write_evaluation_reports(project, bundle, results)
    return results


def write_evaluation_reports(project, bundle, results):
    write_predictions(project, 'test', results)
    config = bundle['config']
    groups = None
    if config.get('group_mapping'):
        specification = config['group_mapping']
        groups = {name:grouped_report(result, specification['letter_to_group']) for name,result in results.items()}
        save_json(project/'group_mapping.json', specification)
        save_json(project/'grouped_evaluation.json', groups)
        write_predictions(project, 'test_groups', groups)
    write_run_readme(project, bundle['training_fit'], results, config, groups)


def write_predictions(project, split, reports):
    for name, result in reports.items():
        with (project/f'{split}_{name}_probabilities.csv').open('w', newline='', encoding='utf-8') as handle:
            fields = ['recording', 'actual', 'predicted'] + ['p_'+label for label in result['labels']]
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for row in result['predictions']:
                writer.writerow(dict(recording=row['recording'], actual=row['actual'], predicted=row['predicted'],
                                     **{'p_'+label:value for label,value in row['probabilities'].items()}))


def write_run_readme(project, training, test, config=None, groups=None):
    gesture = config and config.get('task') == 'deliberate_gestures'
    title = '# Deliberate mouth-sequence classification' if gesture else '# Direct letter classification'
    description = ('User-specified silent movement sequences and a neutral SILENCE class. B/P is one shared movement.' if gesture else
                   'English letter names, A–Z.')
    lines = [title, '', description+' Features come from baseline-corrected 8 kHz IQ measurements.', '',
             '| Model | Training fit | Held-out top-1 | Held-out top-3 |',
             '|---|---:|---:|---:|']
    for name, result in training.items():
        held = test.get(name) if test else None
        first = f'{held["accuracy"]:.1%}' if held else 'Pending collection'
        third = f'{held["top3_accuracy"]:.1%}' if held else 'Pending collection'
        lines.append(f'| {name} | {result["accuracy"]:.1%} | {first} | {third} |')
    lines += ['', 'Training fit measures the examples used to fit the model. It can overstate generalization.',
              'Each held-out sitting follows natural headset repositioning. Recording blocks are parts of that sitting.',
              'All three models use predefined settings. Model selection or tuning using these test results requires a fresh final test.',
              'Probability values are model estimates. Calibration has not been validated.', '',
              '## Grouping approaches', '',
              'The frozen configuration records any user-supplied grouping. Original letter labels remain in the manifest.',
              'Group scores can be computed by summing saved letter probabilities within each group.',
              'Training a group classifier is a separate future experiment and requires a versioned mapping.', '',
              '## Contextual decoding', '',
              'Deferred. Saved per-letter probability vectors can later feed a bounded beam-search decoder.',
              'A language prior must be evaluated separately from acoustic recognition.',
              'The guided trials provide segmentation. Continuous spelling and word boundaries remain untested.', '']
    if gesture:
        # Keep speech-decoding plans out of this deliberately controlled gesture report.
        lines = lines[:lines.index('## Grouping approaches')]
        lines += ['## Gesture definitions', '', '| Class | Ordered movement |', '|---|---|']
        for label, sequence in config['gesture_sequences'].items():
            lines.append(f'| {label} | {sequence} |')
        lines += ['', 'The raw WAVs retain the full time series. These definitions are prompted actions, not independently verified articulation labels.',
                  'User-marked missed actions remain in the raw data with separate rejection records. Three held-out examples per class provide only a preliminary estimate.', '']
    if config and config.get('group_mapping'):
        specification = config['group_mapping']
        lines += ['## Supplied group mapping', '',
                  f'Mapping version {specification["version"]} is frozen with the training configuration.', '',
                  '| Group | Letters |', '|---|---|']
        mapping = specification['letter_to_group']
        for group in sorted(set(mapping.values())):
            letters = ', '.join(letter for letter in sorted(mapping) if mapping[letter] == group)
            lines.append(f'| {group} | {letters} |')
        lines += ['', 'These broad categories are user-supplied hypotheses. Their acoustic separability remains to be measured.', '']
    if groups:
        lines += ['## Grouped results from summed letter probabilities', '',
                  '| Model | Group accuracy | Macro precision | Macro recall | Majority baseline |', '|---|---:|---:|---:|---:|']
        for name,result in groups.items():
            macro = result['per_class']['macro avg']
            lines.append(f'| {name} | {result["accuracy"]:.1%} | {macro["precision"]:.1%} | {macro["recall"]:.1%} | {result["majority_class_baseline"]:.1%} |')
        lines += ['', 'These results aggregate a 26-letter model. A directly trained nine-group model would be a separate experiment.',
                  'Full group precision/recall, confusion matrices and per-recording probabilities are saved in grouped_evaluation.json.', '']
    if test:
        for name, result in test.items():
            lines += [f'## {name} held-out confusion matrix', '',
                      'Rows are actual classes. Columns follow the saved label order.', '',
                      '| Actual | '+' | '.join(result['labels'])+' |',
                      '|---|'+'---:|'*len(result['labels'])]
            for label, row in zip(result['labels'], result['confusion_matrix']):
                lines.append('| '+label+' | '+' | '.join(map(str,row))+' |')
            lines.append('')
    (project/'README.md').write_text('\n'.join(lines), encoding='utf-8')


def grouped_report(letter_result, mapping):
    labels = letter_result['labels']
    if set(mapping) != set(labels) or any(not isinstance(v,str) or not v.strip() for v in mapping.values()):
        raise ValueError('A mapping must assign every letter exactly one nonempty group name.')
    groups = sorted(set(mapping.values()))
    probabilities = np.zeros((len(letter_result['predictions']), len(groups)))
    rows, actual = [], []
    for index, row in enumerate(letter_result['predictions']):
        for letter in labels:
            probabilities[index, groups.index(mapping[letter])] += row['probabilities'][letter]
        rows.append(dict(path=row['recording'], recording_id=row.get('recording_id')))
        actual.append(mapping[row['actual']])
    result = report_probabilities(probabilities, actual, rows, groups)
    result.update(method='sum of direct-letter probabilities', mapping=mapping,
                  majority_class_baseline=max(actual.count(g) for g in groups)/len(actual))
    return result
