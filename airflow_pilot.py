"""Microphone-only, silently articulated English letter-name pilot."""
import csv
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
from scipy.signal import stft
from PySide6 import QtWidgets as Q

import alphabet_models
from alphabet_pilot import AlphabetPilot, LETTERS, NAMES
from dataset_pilot import RATE, save_json

ROOT = Path(__file__).resolve().parent / 'airflow_alphabet_dataset'
CONFIG = dict(task='silent_airflow_alphabet', rate=RATE, labels=LETTERS,
              pronunciation='English letter names, Z=zee', train_per_label=10,
              test_per_label=5, block_size=26, feature_version=1,
              models=['SVM', 'RandomForest', 'LightGBM'], speaker=None)


def airflow_features(x):
    """72 log-band-energy features: 12 temporal bins by six frequency bands."""
    x = np.asarray(x, dtype=float)[RATE:3*RATE]
    if len(x) != 2*RATE:
        raise ValueError('Incomplete action window')
    frequencies, times, spectrum = stft(x, fs=RATE, nperseg=1024, noverlap=768,
                                        boundary=None, padded=False)
    power = np.abs(spectrum)**2
    bands = [(80, 300), (300, 700), (700, 1500), (1500, 3000), (3000, 6000), (6000, 12000)]
    result = []
    for left, right in zip(np.linspace(0, 2, 13)[:-1], np.linspace(0, 2, 13)[1:]):
        frame = (times >= left) & (times < right)
        for low, high in bands:
            mask = (frequencies >= low) & (frequencies < high)
            result.append(np.log10(np.mean(power[mask][:, frame]) + 1e-12))
    return np.asarray(result)

# Reuse the frozen-model provenance and reporting with this experiment's feature function.
alphabet_models.features = airflow_features


class InputCapture:
    def __init__(self, length, device):
        self.rx = np.zeros(length, np.float32)
        self.tx = np.empty((length, 0), np.float32)  # length only; never sent to an output device
        self.nin, self.nout = 0, length
        self.errors, self.streams = [], []
        self.mode, self.timing = 'input-only', []
        def callback(data, frames, timing, status):
            if status:
                self.errors.append(str(status))
            n = min(frames, length-self.nin)
            self.rx[self.nin:self.nin+n] = data[:n, 0]
            self.nin += n
        self.streams = [sd.InputStream(device=device, channels=1, samplerate=RATE,
                                       dtype='float32', callback=callback)]
        try:
            self.streams[0].start()
        except Exception:
            self.close()
            raise

    def close(self):
        for stream in self.streams:
            stream.abort()
            stream.close()
        self.streams = []


class AirflowPilot(AlphabetPilot):
    def __init__(self, labels=LETTERS, root=ROOT, config=CONFIG, block_size=26):
        super().__init__(labels=labels, root=root, config=config, block_size=block_size)
        self.setWindowTitle('Silent airflow • alphabet dataset')
        self.status.setText('Microphone only • 48 kHz • no speaker output')
        self.notes.setPlaceholderText('Record boom distance, mic gain, enhancements, room and headset position')
        self.confirm.setText('Boom close to mouth; unmuted; fixed placement and microphone settings')
        self.check.setText('1. Check microphone')
        self.prompt.setText('Select the boom microphone, enter setup notes, and check the microphone.')
        self.selector = Q.QComboBox()
        self.inputs = [d for d in self.inventory if d['inputs'] > 0]
        for d in self.inputs:
            self.selector.addItem(f"{d['name']} ({d['host']})", d['id'])
        self.layout().insertWidget(1, self.selector)
        if self.mic:
            index = self.selector.findData(self.mic['id'])
            if index >= 0:
                self.selector.setCurrentIndex(index)
        self.selector.currentIndexChanged.connect(self.change_mic)
        self.change_mic()
        self.check.setEnabled(bool(self.mic))
        self.start.setEnabled(bool(self.mic))

    def change_mic(self):
        self.mic = next((d for d in self.inputs if d['id'] == self.selector.currentData()), None)
        self.check_passed = False

    def controls(self, active):
        super().controls(active)
        self.selector.setEnabled(not active)

    def launch(self, tx):
        if self.unsaved_capture is not None or self.cap is not None:
            return False
        if not self.mic or not self.confirm.isChecked() or not self.notes.text().strip():
            self.status.setText('Choose a microphone, enter setup notes and confirm the setup.')
            return False
        try:
            self.cap = InputCapture(len(tx), self.mic['id'])
        except Exception as error:
            self.status.setText(f'Microphone could not open at 48 kHz: {error}')
            return False
        self.started = datetime.now(timezone.utc).isoformat()
        self.deadline = time.monotonic() + len(tx)/RATE + 5
        self.controls(True)
        return True

    def begin_check(self):
        self.checking = True
        if self.launch(np.empty((4*RATE, 0), np.float32)):
            self.prompt.setText('Silently mouth A, B, C near the boom mic for this check')

    def action_prompt(self, label):
        return f'Silently articulate “{NAMES[label]}” once; do not use your voice'

    def save_capture(self, cap, complete, folder):
        self.controls(False)
        folder.mkdir(parents=True, exist_ok=True)
        rx = cap.rx[:cap.nin]
        write(folder/'mic.wav', RATE, rx)
        metadata = dict(session_id=folder.name, role='check' if self.checking else self.role,
                        utc=self.started, input=self.mic, output=None, config=self.config,
                        notes=self.notes.text(), complete=complete, audio_flags=cap.errors,
                        stream_mode='input-only')
        save_json(folder/'session.json', metadata)
        if self.checking:
            peak = float(np.max(np.abs(rx))) if len(rx) else 0
            self.check_passed = bool(complete and not cap.errors and 0.00001 < peak < .999)
            self.prompt.setText('Mic check passed • ready to collect' if self.check_passed else 'Mic check failed • check input, mute, gain or clipping')
            self.status.setText(f'Mic peak: {peak:.5f}. This check does not verify airflow specificity.')
            return
        metadata.update(seed=self.seed, trial_order=self.pending, prompt_observations=self.observations)
        save_json(folder/'session.json', metadata)
        rows = []
        for index, (trial, label) in enumerate(self.pending):
            start = (2+index*4)*RATE
            if start >= len(rx):
                break
            x = rx[start:start+4*RATE]
            stages = {o['stage'] for o in self.observations if o['trial'] == trial}
            reasons = []
            if len(x) != 4*RATE: reasons.append('incomplete')
            if len(x) and np.max(np.abs(x)) >= .999: reasons.append('clipping')
            if cap.errors: reasons.append('audio fault')
            if trial in self.late or stages != {0, 1, 2}: reasons.append('late or missing cue')
            filename = f'{trial:03}_{label}.wav'
            write(folder/filename, RATE, x)
            row = dict(filename=filename, label=label, trial=trial, session_id=folder.name,
                       recording_id=f'{folder.name}/{filename}', rate=RATE, start_sample=start,
                       action_start_s=1, action_end_s=3, microphone_id=self.mic['id'],
                       accepted=not reasons, exclusions='; '.join(reasons))
            if not reasons:
                self.accepted[trial] = dict(label=label, features=airflow_features(x).tolist(),
                                            path=str(folder/filename), recording_id=row['recording_id'])
            rows.append(row)
        if rows:
            with (folder/'metadata.csv').open('w', newline='', encoding='utf-8') as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
        save_json(self.project/(self.role+'_accepted.json'), self.accepted)
        if len(self.accepted) < self.target_count():
            self.prompt.setText(f'Saved {len(self.accepted)}/{self.target_count()} trials. Take a break; press Record to continue. Faulty trials are retried.')
        else:
            self.complete_session()


if __name__ == '__main__':
    app = Q.QApplication([])
    window = AirflowPilot()
    window.show()
    app.exec()


