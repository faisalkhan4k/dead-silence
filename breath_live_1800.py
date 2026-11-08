"""Separate live 1.8-second model experiment; the 50 ms app is unchanged."""
import pickle
import queue
import time
from collections import deque
from pathlib import Path

import numpy as np
from PySide6 import QtWidgets as Q
import breath_live as live

CHECKPOINT = live.HERE/'breath_noise_dataset/experiments/20261108T104629Z-1800ms-7930df55/candidate.pkl'

class Window(live.Window):
    def __init__(self):
        super().__init__()
        bundle = pickle.loads(CHECKPOINT.read_bytes())  # Trusted locally trained artifact only.
        if bundle['window_ms'] != 1800 or bundle['feature'] != 'mean_std_6band_v1':
            raise ValueError('Unexpected 1.8-second model format')
        self.model = bundle['model']
        self.frames_1800 = deque(maxlen=36)
        self.last_arrival = None
        self.setWindowTitle('Breath to text • 1.8-second experimental model')
        self.letter_gap.setValue(1.0)
        self.word_gap.setValue(3.0)
        self.send_gap.setValue(5.0)
        self.info.setText('1.8-second model • 50 ms updates • pauses: letter 1 s, word 3 s, send 5 s after detected silence. Select microphone and Start.')

    def toggle(self):
        if self.stream is None:
            self.frames_1800.clear()
            self.last_arrival = None
            while True:
                try: self.q.get_nowait()
                except queue.Empty: break
        super().toggle()

    def poll(self):
        for _ in range(20):
            try: x, arrival = self.q.get_nowait()
            except queue.Empty: break
            if self.stream is None or self.speaking:
                self.frames_1800.clear(); self.last_arrival = None
                continue
            if len(x) != live.N:
                self.drops += 1; self.frames_1800.clear(); self.last_arrival = None
                continue
            # A discontinuous stream cannot represent a continuous 1.8-second window.
            if self.last_arrival is not None and arrival-self.last_arrival > .15:
                self.frames_1800.clear()
            self.last_arrival = arrival
            t = time.perf_counter()
            self.frames_1800.append(live.feature(x))
            if len(self.frames_1800) < 36:
                self.live.setText(f'Collecting audio: {len(self.frames_1800)*.05:.2f} / 1.80 s')
                continue
            frames = np.asarray(self.frames_1800)
            vector = np.concatenate((frames.mean(axis=0), frames.std(axis=0)))
            label = str(self.model.predict(vector.reshape(1,-1))[0])
            elapsed = (time.perf_counter()-t)*1000
            self.times.append((elapsed,(time.perf_counter()-arrival)*1000))
            if label == self.candidate: self.count += 1
            else: self.candidate = label; self.count = 1
            if self.count >= 3: self.current = label
            for event,value in self.decoder.advance(self.current):
                if event == 'letter': self.insert(value)
                elif event == 'space': self.accept_word_pause()
                elif event == 'delete': self.delete_letter(); self.info.setText('Deleted last letter.')
                elif event == 'send': self.info.setText('Send pause reached.'); self.send()
                elif event == 'invalid': self.info.setText(f'Unassigned code {value}; try again.')
                elif event == 'incomplete': self.info.setText(f'Incomplete code {value}; enter all five breaths.')
                elif event == 'overflow': self.info.setText('Maximum 5 numbers; pause and try again.')
            countdown = ''
            if self.current == 'SILENCE' and self.decoder.send_armed and self.decoder.silence >= self.decoder.word_gap:
                countdown = f'  |  send in {max(0., self.decoder.send_gap-self.decoder.silence):.1f} s'
            self.live.setText(f'{self.current}  |  code: {self.decoder.code or "—"}  |  compute {elapsed:.1f} ms{countdown}')

    def stop(self):
        if self.stream is None: return
        self.stream.stop(); self.stream.close(); self.stream = None
        self.device.setEnabled(True); self.start.setText('Start')
        for control in (self.letter_gap,self.word_gap,self.send_gap): control.setEnabled(True)
        if self.times:
            arr = np.asarray(self.times)
            self.info.setText(f'{len(arr)} predictions; compute median {np.median(arr[:,0]):.1f} ms, p95 {np.percentile(arr[:,0],95):.1f} ms; callback-to-result p95 {np.percentile(arr[:,1],95):.1f} ms; faults/drops {self.drops}. Audio context is 1.8 seconds.')
            try:
                import mlflow
                mlflow.set_tracking_uri('sqlite:///'+(live.HERE/'breath_mlflow.db').as_posix())
                mlflow.set_experiment('breath-live')
                with mlflow.start_run(run_name='live-1800ms'):
                    mlflow.log_params({'window_ms':1800,'hop_ms':50,'smoothing_windows':3,'model':'random_forest','model_checkpoint':CHECKPOINT.parent.name,'letter_gap_s':self.decoder.letter_gap,'word_gap_s':self.decoder.word_gap,'send_gap_s':self.decoder.send_gap})
                    mlflow.log_metrics({'compute_p50_ms':float(np.median(arr[:,0])),'compute_p95_ms':float(np.percentile(arr[:,0],95)),'callback_to_result_p95_ms':float(np.percentile(arr[:,1],95)),'predictions':len(arr),'faults_or_drops':self.drops})
            except Exception as error: self.info.setText(self.info.text()+' MLflow logging failed: '+str(error))
        self.times=[]; self.drops=0

if __name__ == '__main__':
    app=Q.QApplication([]); window=Window(); window.show(); app.exec()
