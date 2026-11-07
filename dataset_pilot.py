"""Guided, session-separated command pilot. Audio callbacks reuse Capture."""
import csv
import hashlib
import json
import pickle
import random
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np
from scipy.io.wavfile import write
from PySide6 import QtCore, QtWidgets as Q
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from analysis import tone_iq
from audio_io import Capture, devices
from protocol import build
from reception import measure
from storage import session_id

RATE = 48000
HZ = 8000
LABELS = ['YES', 'NO', 'STOP', 'STILL', 'HEAD']
ROOT = Path(__file__).resolve().parent / 'dataset'
CONFIG = dict(rate=RATE, frequency=HZ, peak=.005, channel='Left',
              feature_version=1, clipping=.999, min_probe_floor_db=10,
              max_prompt_delay_s=.25)


def save_json(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2), encoding='utf-8')
    temporary.replace(path)


def trial_order(count, seed, labels=None):
    rng = random.Random(seed)
    values = list(LABELS if labels is None else labels) * count
    while True:
        rng.shuffle(values)
        if all(not values[i] == values[i-1] == values[i-2] for i in range(2, len(values))):
            return values


def features(x):
    size, hop = 2048, 1024
    z = tone_iq(x, RATE, HZ, size)
    times = (np.arange(len(z)) * hop + size / 2) / RATE
    z *= np.exp(-2j * np.pi * HZ * np.arange(len(z)) * hop / RATE)
    baseline = (times >= .15) & (times <= .85)
    action = (times >= 1.05) & (times <= 2.95)
    amplitude = abs(z)
    reference = max(float(np.median(amplitude[baseline])), 1e-12)
    phase = np.unwrap(np.angle(z))
    slope, intercept = np.polyfit(times[baseline], phase[baseline], 1)
    residual = phase - (slope * times + intercept)
    phase_valid = bool(np.min(amplitude[action]) > .1 * reference and
                       np.std(residual[baseline]) < .3)
    amp = amplitude / reference - 1
    phase_values = residual if phase_valid else np.zeros_like(residual)
    grid = np.linspace(1.05, 2.95, 32)
    sequences = [np.interp(grid, times[action], v[action]) for v in (amp, phase_values)]
    summaries = [number for v in sequences for number in
                 (np.mean(v), np.std(v), np.ptp(v), np.mean(np.diff(v)**2))]
    return np.r_[sequences[0], sequences[1], summaries], phase_valid


def quality(x, faults=False, late=False):
    reasons = []
    if len(x) != 4 * RATE:
        return ['incomplete']
    if np.max(abs(x)) >= CONFIG['clipping']:
        reasons.append('clipping')
    if measure(x[int(.15*RATE):int(.85*RATE)], RATE, HZ)['peak_floor_db'] < CONFIG['min_probe_floor_db']:
        reasons.append('missing probe in baseline')
    if faults:
        reasons.append('audio fault')
    if late:
        reasons.append('late visual prompt')
    return reasons


class Pilot(Q.QWidget):
    def __init__(self, labels=None, root=ROOT, config=None, block_size=None):
        super().__init__()
        self.labels = list(LABELS if labels is None else labels)
        self.root = Path(root)
        self.config = dict(CONFIG if config is None else config)
        self.block_size = block_size
        self.setWindowTitle('Wired headset • command dataset pilot')
        self.resize(920, 560)
        self.cap = None
        self.unsaved_capture = None
        self.project_lock = None
        self.project = None
        self.role = 'train'
        self.accepted = {}
        self.models = None
        self.check_passed = False
        self.inventory = devices()
        self.mic = next((d for d in self.inventory if d['name']=='Microphone (Realtek(R) Audio)' and d['host']=='MME'), None)
        self.speaker = next((d for d in self.inventory if d['name']=='Headphones (Realtek(R) Audio)' and d['host']=='MME'), None)
        layout = Q.QVBoxLayout(self)
        self.status = Q.QLabel('8 kHz • 48 kHz • peak 0.005 • left earcup → wired boom')
        layout.addWidget(self.status)
        self.notes = Q.QLineEdit()
        self.notes.setPlaceholderText('Record system volume, mic gain/enhancements and headset placement')
        layout.addWidget(self.notes)
        self.confirm = Q.QCheckBox('Boom unmuted; headset fixed around neck; volume low; settings checked')
        layout.addWidget(self.confirm)
        self.prompt = Q.QLabel('Start with the brief reception check')
        self.prompt.setWordWrap(True)
        self.prompt.setStyleSheet('font-size: 30px; font-weight: bold;')
        layout.addWidget(self.prompt, 1)
        self.counter = Q.QLabel('')
        layout.addWidget(self.counter)
        bar = Q.QHBoxLayout()
        layout.addLayout(bar)
        self.check = Q.QPushButton('1. Check reception')
        self.start = Q.QPushButton('2. Record training')
        self.stop = Q.QPushButton('Stop and save')
        self.resume = Q.QPushButton('Open saved pilot')
        for button in (self.check, self.start, self.stop, self.resume):
            bar.addWidget(button)
        self.check.clicked.connect(self.begin_check)
        self.start.clicked.connect(self.begin_session)
        self.stop.clicked.connect(lambda: self.finish(False))
        self.resume.clicked.connect(self.open_project)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(30)
        self.notes.textChanged.connect(self.invalidate_check)
        if not self.mic or not self.speaker:
            self.status.setText('Required wired microphone/headphones missing. Connect headset and reopen.')
            self.check.setEnabled(False)
            self.start.setEnabled(False)

    def controls(self, active):
        for widget in (self.check, self.start, self.resume, self.notes, self.confirm):
            widget.setEnabled(not active)

    def invalidate_check(self):
        self.check_passed = False

    def claim_project(self, path):
        if self.project == path and self.project_lock is not None:
            return True
        lock = QtCore.QLockFile(str(path/'.collection.lock'))
        if not lock.tryLock(0):
            self.status.setText('This pilot is open in another collection window. Close that window first.')
            return False
        if self.project_lock is not None:
            self.project_lock.unlock()
        self.project_lock = lock
        return True

    def target_count(self):
        return len(self.labels) * self.repetitions()

    def repetitions(self):
        return self.config.get(self.role+'_per_label', 10 if self.role == 'train' else 5)

    def extra_exclusions(self, trial):
        return []

    def make_order(self, count, seed):
        return trial_order(count, seed, self.labels)

    def action_prompt(self, label):
        return {'STILL':'Remain still', 'HEAD':'Turn head gently • mouth still'}.get(label, f'Silently mouth {label} once')

    def open_project(self):
        folder = Q.QFileDialog.getExistingDirectory(self, 'Choose pilot folder', str(self.root))
        if not folder:
            return
        path = Path(folder)
        if not (path/'config.json').exists() or json.loads((path/'config.json').read_text()) != self.config:
            self.status.setText('Choose a compatible pilot folder.')
            return
        if not self.claim_project(path):
            return
        self.project = path
        if (path/'evaluation.json').exists():
            self.status.setText('This pilot has already been evaluated. See evaluation.json.')
            self.start.setEnabled(False)
            return
        self.role = 'test' if (path/'models.pkl').exists() else 'train'
        accepted_path = path/(self.role+'_accepted.json')
        saved = json.loads(accepted_path.read_text()) if accepted_path.exists() else {}
        self.accepted = {int(key):value for key,value in saved.items()}
        self.check_passed = False
        self.start.setText('2. Record held-out test' if self.role == 'test' else '2. Record training')
        self.status.setText('Reposition headset, then run reception check before held-out collection.')
        self.start.setEnabled(True)

    def launch(self, tx):
        if self.unsaved_capture is not None:
            self.status.setText('Use Stop and save to retry saving the previous capture first.')
            return False
        if self.cap is not None:
            return False
        if not self.mic or not self.speaker:
            self.status.setText('Required wired endpoints missing. Reconnect and reopen.')
            return False
        if not self.confirm.isChecked() or not self.notes.text().strip():
            self.status.setText('Enter placement/volume notes and confirm setup first.')
            return False
        cap = Capture(tx, RATE)
        try:
            cap.open(self.mic['id'], self.speaker['id'])
        except Exception as error:
            cap.close()
            self.status.setText(str(error))
            return False
        self.cap = cap
        self.started = datetime.now(timezone.utc).isoformat()
        self.deadline = time.monotonic() + len(tx)/RATE + 5
        self.controls(True)
        return True

    def begin_check(self):
        self.checking = True
        tx, self.check_events = build(RATE, 2, 'Band check', HZ, HZ, .005, 1, 'Left', 0)
        if self.launch(tx):
            self.prompt.setText('Keep mouth closed and still • checking 8 kHz reception')

    def begin_session(self):
        if self.project is not None and (self.project/'evaluation.json').exists():
            self.start.setEnabled(False)
            self.status.setText('This pilot has already been evaluated. Open a fresh window to create a new pilot.')
            return
        if not self.check_passed:
            self.status.setText('Run a passing reception check first.')
            return
        if self.role == 'test' and not self.accepted:
            answer = Q.QMessageBox.question(self, 'Held-out session', 'Have you removed and naturally repositioned the headset? Keep the same volume and device settings.')
            if answer != Q.QMessageBox.StandardButton.Yes:
                return
        if self.project is None:
            project = self.root/session_id()
            project.mkdir(parents=True)
            if not self.claim_project(project):
                return
            self.project = project
            save_json(self.project/'config.json', self.config)
        target = self.target_count()
        if len(self.accepted) == target:
            self.complete_session()
            return
        count = self.repetitions()
        self.seed = random.SystemRandom().randrange(2**32)
        order_path = self.project/(self.role+'_order.json')
        if not order_path.exists():
            save_json(order_path, self.make_order(count, self.seed))
        order = json.loads(order_path.read_text())
        self.pending = [(i, label) for i,label in enumerate(order, 1) if i not in self.accepted]
        if self.block_size:
            self.pending = self.pending[:self.block_size]
        if not self.pending:
            return
        self.checking = False
        # Two seconds of settling before exact four-second trials.
        length = (2 + 4*len(self.pending) + 1)*RATE
        tx = np.zeros((length, 2), np.float32)
        tx[:,0] = .005*np.sin(2*np.pi*HZ*np.arange(length)/RATE)
        ramp = np.linspace(0, 1, int(.015*RATE))**2
        tx[:len(ramp),0] *= ramp
        tx[-len(ramp):,0] *= ramp[::-1]
        self.observations = []
        self.last_stage = None
        self.late = set()
        if self.launch(tx):
            self.status.setText(f'{self.role.upper()} • {len(self.pending)} trials • visual instructions only')

    def tick(self):
        if self.cap is None:
            return
        cap = self.cap
        seconds = cap.nin/RATE
        if not self.checking:
            index = int((seconds-2)//4)
            if seconds < 2:
                self.prompt.setText('Get ready • remain still')
            elif index < len(self.pending):
                trial, label = self.pending[index]
                within = (seconds-2) % 4
                stage = 0 if within < 1 else (1 if within < 3 else 2)
                key = (index, stage)
                if key != self.last_stage:
                    boundary = 2 + index*4 + (0,1,3)[stage]
                    if seconds-boundary > .25:
                        self.late.add(trial)
                    if self.last_stage is not None:
                        old_index, old_stage = self.last_stage
                        if index*3+stage > old_index*3+old_stage+1:
                            for skipped in range(old_index, index+1):
                                self.late.add(self.pending[skipped][0])
                    self.observations.append(dict(trial=trial, stage=stage, input_frame=cap.nin))
                    self.last_stage = key
                action = self.action_prompt(label)
                instruction = ('Neutral • stay still', action, 'Return to neutral')[stage]
                self.prompt.setText(f'{label}\n{instruction}')
                stage_end = (1,3,4)[stage]
                total = self.target_count()
                self.counter.setText(f'Trial {trial}/{total} • next cue in {stage_end-within:.1f} s')
        if cap.nin == len(cap.rx) and cap.nout == len(cap.tx):
            self.finish(True)
        elif cap.errors or time.monotonic() > self.deadline or any(not s.active for s in cap.streams):
            self.finish(False)

    def finish(self, complete):
        if self.cap is None and self.unsaved_capture is None:
            return
        if self.unsaved_capture is None:
            cap, self.cap = self.cap, None
            cap.close()
            folder = (self.project or self.root/'checks')/session_id()
            self.unsaved_capture = (cap, complete, folder)
        cap, complete, folder = self.unsaved_capture
        try:
            self.save_capture(cap, complete, folder)
        except Exception as error:
            self.controls(True)
            self.stop.setEnabled(True)
            self.status.setText(f'Save/analysis failed: {error}. Use Stop and save to retry. The capture remains in memory.')
            return
        self.unsaved_capture = None

    def save_capture(self, cap, complete, folder):
        self.controls(False)
        folder.mkdir(parents=True, exist_ok=True)
        rx, tx = cap.rx[:cap.nin], cap.tx[:cap.nout]
        write(folder/'mic.wav', RATE, rx)
        write(folder/'output.wav', RATE, tx)
        metadata = dict(session_id=folder.name, role='check' if self.checking else self.role,
                        utc=self.started, input=self.mic, output=self.speaker, config=self.config,
                        notes=self.notes.text(), complete=complete, audio_flags=cap.errors,
                        stream_mode=cap.mode, timing=cap.timing)
        save_json(folder/'session.json', metadata)
        if self.checking:
            from analysis import report
            result = report(rx, tx, dict(mode='Band check', rate=RATE, frequency=HZ,
                            events=self.check_events, status='complete' if complete else 'stopped',
                            audio_flags=cap.errors, stream_mode=cap.mode, setup='A'))
            self.check_passed = bool(result['band_gate'])
            save_json(folder/'report.json', result)
            self.prompt.setText('Reception passed • ready to collect' if self.check_passed else 'Reception failed • check mute, routing and volume')
            return
        metadata.update(seed=self.seed, trial_order=self.pending, prompt_observations=self.observations)
        save_json(folder/'session.json', metadata)
        rows = []
        for index, (trial,label) in enumerate(self.pending):
            start = (2+index*4)*RATE
            if start >= len(rx):
                break
            x = rx[start:start+4*RATE]
            stages_seen = {o['stage'] for o in self.observations if o['trial'] == trial}
            reasons = quality(x, bool(cap.errors), trial in self.late or stages_seen != {0,1,2})
            reasons.extend(self.extra_exclusions(trial))
            filename = f'{trial:03}_{label}.wav'
            write(folder/filename, RATE, x)
            row = dict(filename=filename, label=label, trial=trial, session_id=folder.name,
                       recording_id=f'{folder.name}/{filename}',
                       utc=self.started, start_offset_s=start/RATE, start_sample=start, end_sample=start+4*RATE,
                       trial_timestamp=(datetime.fromisoformat(self.started)+timedelta(seconds=start/RATE)).isoformat(),
                       action_start_s=1, action_end_s=3,
                       action_start_sample=RATE, action_end_sample=3*RATE,
                       rate=RATE, frequency=HZ, microphone_id=self.mic['id'], speaker_id=self.speaker['id'],
                       accepted=not reasons, exclusions='; '.join(reasons))
            if self.config.get('task') == 'deliberate_gestures':
                row['gesture_sequence'] = self.config['gesture_sequences'][label]
            if self.config.get('task') == 'alphabet':
                row.update(letter_label=label, pronunciation=self.config['pronunciation'])
                if self.config.get('group_mapping'):
                    mapping = self.config['group_mapping']
                    row.update(group_label=mapping['letter_to_group'][label], group_mapping_version=mapping['version'])
            if not reasons:
                vector, valid = features(x)
                row['phase_valid'] = valid
                self.accepted[trial] = dict(label=label, features=vector.tolist(), path=str(folder/filename),
                                           recording_id=row['recording_id'], phase_valid=valid)
                if self.config.get('task') == 'alphabet':
                    self.accepted[trial]['letter_label'] = label
            rows.append(row)
        with (folder/'metadata.csv').open('w', newline='', encoding='utf-8') as handle:
            fields = sorted({key for row in rows for key in row})
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        save_json(self.project/(self.role+'_accepted.json'), self.accepted)
        target = self.target_count()
        if len(self.accepted) < target:
            self.prompt.setText(f'Saved {len(self.accepted)}/{target} accepted trials. Take a break, then press Record to continue. Faulty trials are retried.')
            return
        self.complete_session()

    def complete_session(self):
        ordered = [self.accepted[key] for key in sorted(self.accepted)]
        X = np.array([item['features'] for item in ordered])
        y = [item['label'] for item in ordered]
        if self.role == 'train':
            self.models = dict(SVM=make_pipeline(StandardScaler(), SVC(C=1, kernel='rbf')),
                               RandomForest=make_pipeline(StandardScaler(), RandomForestClassifier(n_estimators=200, max_depth=5, min_samples_leaf=2, random_state=42)))
            for model in self.models.values():
                model.fit(X, y)
            with (self.project/'models.pkl').open('wb') as handle:
                pickle.dump(self.models, handle)
            save_json(self.project/'frozen.json', dict(config=CONFIG, model_sha256=hashlib.sha256((self.project/'models.pkl').read_bytes()).hexdigest()))
            self.role, self.accepted, self.check_passed = 'test', {}, False
            self.start.setText('2. Record held-out test')
            self.prompt.setText('Training saved and models frozen. Reposition headset, then run reception check for the test session.')
        else:
            destination = self.project/'evaluation.json'
            if destination.exists():
                self.status.setText('Evaluation already exists. It will not be replaced.')
                return
            frozen = json.loads((self.project/'frozen.json').read_text())
            data = (self.project/'models.pkl').read_bytes()
            if hashlib.sha256(data).hexdigest() != frozen['model_sha256'] or frozen['config'] != CONFIG:
                raise ValueError('Frozen model/configuration changed')
            models = pickle.loads(data)
            results = {}
            for name, model in models.items():
                predictions = model.predict(X)
                results[name] = dict(accuracy=accuracy_score(y,predictions),
                                     per_class=classification_report(y,predictions,labels=LABELS,output_dict=True,zero_division=0),
                                     labels=LABELS, confusion_matrix=confusion_matrix(y,predictions,labels=LABELS).tolist(),
                                     predictions=[dict(recording=item['path'], actual=label, predicted=str(pred)) for item,label,pred in zip(ordered,y,predictions)])
            save_json(destination, results)
            self.start.setEnabled(False)
            self.prompt.setText('\n'.join(f'{name}: {result["accuracy"]:.0%}' for name,result in results.items()))
            self.status.setText('Evaluation saved: '+str(destination))

    def closeEvent(self, event):
        self.finish(False)
        if self.unsaved_capture is not None:
            self.status.setText('Capture still needs saving. Use Stop and save before closing.')
            event.ignore()
            return
        if self.project_lock is not None:
            self.project_lock.unlock()
        event.accept()


if __name__ == '__main__':
    app = Q.QApplication([])
    window = Pilot()
    window.show()
    app.exec()
