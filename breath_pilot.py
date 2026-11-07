"""Guided microphone-only inhale/exhale data collection and classification."""
from pathlib import Path
import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier
from PySide6 import QtWidgets as Q
import alphabet_models
from airflow_pilot import AirflowPilot, RATE

LABELS = ['INHALE', 'EXHALE']
ROOT = Path(__file__).resolve().parent/'breath_dataset'
CONFIG = dict(task='breath_binary', rate=RATE, labels=LABELS, train_per_label=20,
              test_per_label=10, block_size=10, feature_version=1, speaker=None,
              models=['SVM', 'RandomForest', 'XGBoost', 'LightGBM'])

class BreathXGBoost(ClassifierMixin, BaseEstimator):
    def fit(self, X, y):
        self.encoder_ = LabelEncoder().fit(y)
        self.classes_ = self.encoder_.classes_
        self.model_ = XGBClassifier(n_estimators=150, max_depth=3, learning_rate=.05,
                                    random_state=42, n_jobs=2, eval_metric='logloss')
        self.model_.fit(X, self.encoder_.transform(y))
        return self
    def predict_proba(self, X):
        return self.model_.predict_proba(X)
    def predict(self, X):
        return self.encoder_.inverse_transform(np.argmax(self.predict_proba(X), axis=1))

_original_models = alphabet_models.baseline_models
def breath_models(calibration_folds=5):
    models = _original_models(calibration_folds)
    models['XGBoost'] = BreathXGBoost()
    return models
alphabet_models.baseline_models = breath_models

def report_readme(project, training, test, config=None, groups=None):
    lines = ['# Inhale/exhale pilot', '', 'Microphone-only; six broadband energy bands across 12 time bins.',
             'Guided trials; training fit is not independent validation. Held-out trials follow headset repositioning.',
             'A balanced two-class chance baseline is 50%.', '', '| Model | Training fit | Held-out accuracy |', '|---|---:|---:|']
    for name, result in training.items():
        held = test.get(name) if test else None
        score = f'{held["accuracy"]:.1%}' if held else 'Pending'
        lines.append(f'| {name} | {result["accuracy"]:.1%} | {score} |')
    lines += ['', 'See evaluation.json for class metrics, confusion matrices and prediction probabilities.',
              'Top-3 accuracy is not meaningful for two classes. Continuous breathing, segmentation and alphabet decoding are not tested.']
    (Path(project)/'README.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
alphabet_models.write_run_readme = report_readme

class BreathPilot(AirflowPilot):
    def __init__(self):
        super().__init__(labels=LABELS, root=ROOT, config=CONFIG, block_size=10)
        self.setWindowTitle('Breath dataset • inhale and exhale')
        self.prompt.setText('Select the boom mic, enter notes, then check the microphone.')
        self.counter.setText('20 training and 10 test examples per class; blocks of 10 trials.')
        self.notes.setPlaceholderText('Record mic position, gain, enhancements, room and breathing technique')
    def action_prompt(self, label):
        return 'Inhale once, gently and audibly' if label == 'INHALE' else 'Exhale once, gently and audibly'
    def begin_check(self):
        super().begin_check()
        if self.cap is not None:
            self.prompt.setText('Gently inhale and exhale near the boom mic for this check')
    def models_finished(self, result):
        super().models_finished(result)
        if self.role == 'test' and (self.project/'evaluation.json').exists():
            self.prompt.setText('\n'.join(f'{name} • held-out accuracy {value["accuracy"]:.1%}' for name,value in result.items()))

if __name__ == '__main__':
    app = Q.QApplication([])
    window = BreathPilot()
    window.show()
    app.exec()
