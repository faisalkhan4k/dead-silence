"""Collect user-labeled continuous breath sequences without model-generated labels."""
import json, queue, time, uuid
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
from PySide6 import QtCore, QtWidgets as Q

HERE=Path(__file__).resolve().parent
ROOT=HERE/'breath_sequence_dataset'
RATE=48000
PROMPTS=[('1 2 1','Short inhale, exhale, inhale; pause naturally between each.'),
         ('2 1 2','Short exhale, inhale, exhale; pause naturally between each.'),
         ('1 1 2','Two short inhales, then a short exhale.'),
         ('2 2 1','Two short exhales, then a short inhale.'),
         ('2211 DELETE','Exhale, exhale, inhale, inhale; pause to finish the delete code.'),
         ('1 SEND','Inhale once; pause for at least 4 seconds to send.')]

class Collector(Q.QWidget):
    def __init__(self):
        super().__init__(); self.setWindowTitle('Breath sequence collection'); self.resize(850,450)
        self.stream=None; self.chunks=[]; self.flags=[]; self.frames=0; self.started=None
        layout=Q.QVBoxLayout(self)
        self.devices=[(i,d) for i,d in enumerate(sd.query_devices()) if d['max_input_channels']]
        self.device=Q.QComboBox()
        for i,d in self.devices: self.device.addItem(d['name'],i)
        layout.addWidget(self.device)
        self.split=Q.QComboBox(); self.split.addItems(['train','held-out']); layout.addWidget(Q.QLabel('Session split (use a separate sitting and reposition headset for held-out)')); layout.addWidget(self.split)
        self.prompt=Q.QComboBox()
        for code,description in PROMPTS: self.prompt.addItem(code+' — '+description,code)
        layout.addWidget(Q.QLabel('Choose the intended sequence')); layout.addWidget(self.prompt)
        self.notes=Q.QLineEdit(); self.notes.setPlaceholderText('Setup and timing notes (no secrets)'); layout.addWidget(self.notes)
        self.status=Q.QLabel('Record one sequence at a time. Breathe comfortably; stop whenever you want.'); self.status.setWordWrap(True); layout.addWidget(self.status,1)
        buttons=Q.QHBoxLayout(); layout.addLayout(buttons)
        self.start=Q.QPushButton('Start recording'); self.start.clicked.connect(self.begin); buttons.addWidget(self.start)
        self.stop_button=Q.QPushButton('Stop and save'); self.stop_button.setEnabled(False); self.stop_button.clicked.connect(self.finish); buttons.addWidget(self.stop_button)
        self.timer=QtCore.QTimer(self); self.timer.timeout.connect(self.update_status); self.timer.start(100)
    def callback(self,data,frames,timing,status):
        if status: self.flags.append(str(status))
        self.chunks.append(data[:,0].copy()); self.frames+=frames
    def begin(self):
        if self.stream: return
        if not self.devices: self.status.setText('No microphone available.'); return
        self.chunks=[]; self.flags=[]; self.frames=0
        try:
            self.stream=sd.InputStream(device=self.device.currentData(),channels=1,samplerate=RATE,dtype='float32',callback=self.callback)
            self.stream.start()
        except Exception as e:
            if self.stream: self.stream.close(); self.stream=None
            self.status.setText('Could not start microphone: '+str(e)); return
        self.started=datetime.now(timezone.utc).isoformat(); self.start.setEnabled(False); self.stop_button.setEnabled(True)
        for item in (self.device,self.split,self.prompt,self.notes): item.setEnabled(False)
    def update_status(self):
        if self.stream:
            self.status.setText(f'Recording {self.frames/RATE:.1f} s • {self.prompt.currentText()}\nStop when finished; take breaks as needed.')
    def finish(self):
        if not self.stream:return
        self.stream.stop(); self.stream.close(); self.stream=None
        for item in (self.device,self.split,self.prompt,self.notes): item.setEnabled(True)
        self.start.setEnabled(True); self.stop_button.setEnabled(False)
        x=np.concatenate(self.chunks) if self.chunks else np.empty(0,dtype=np.float32)
        if not len(x): self.status.setText('No audio captured; try again.'); return
        run=ROOT/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]); run.mkdir(parents=True)
        write(run/'mic.wav',RATE,x)
        metadata={'split':self.split.currentText(),'expected_sequence':self.prompt.currentData(),
                  'prompt':self.prompt.currentText(),'started_utc':self.started,'rate':RATE,'frames':len(x),
                  'audio_flags':self.flags,'notes':self.notes.text(),'device_id':self.device.currentData(),
                  'event_timestamps':None,'label_type':'sequence-level only; no event boundaries',
                  'warning':'Do not use as frame-level ground truth without annotation.'}
        (run/'metadata.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
        self.status.setText(f'Saved {len(x)/RATE:.1f} s to {run}. Sequence labels are approximate; event boundaries are not labeled.')
    def closeEvent(self,event):
        if self.stream:self.finish()
        event.accept()

if __name__=='__main__':
    app=Q.QApplication([]); w=Collector(); w.show(); app.exec()
