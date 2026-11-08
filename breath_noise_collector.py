"""Collect clip-level examples of deliberate breathing and background-only audio."""
import json, uuid
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
from PySide6 import QtCore, QtWidgets as Q

ROOT=Path(__file__).resolve().parent/'breath_noise_dataset'
RATE=48000

class Collector(Q.QWidget):
    def __init__(self):
        super().__init__(); self.setWindowTitle('Breath and background dataset'); self.resize(840,520)
        self.stream=None; self.chunks=[]; self.flags=[]; self.frames=0
        layout=Q.QVBoxLayout(self)
        self.devices=[(i,d) for i,d in enumerate(sd.query_devices()) if d['max_input_channels']]
        self.device=Q.QComboBox()
        for i,d in self.devices: self.device.addItem(d['name'],i)
        layout.addWidget(Q.QLabel('Microphone')); layout.addWidget(self.device)
        self.category=Q.QComboBox()
        for title,value in [('Intentional inhale','INHALE'),('Intentional exhale','EXHALE'),('No intentional breath input','NO_BREATH')]:self.category.addItem(title,value)
        layout.addWidget(Q.QLabel('Intended clip category'));layout.addWidget(self.category)
        self.background=Q.QComboBox();self.background.addItems(['Quiet room','Talking in background','Fan or ambient noise','Game or music audio','Other'])
        layout.addWidget(Q.QLabel('Background condition'));layout.addWidget(self.background)
        self.split=Q.QComboBox();self.split.addItems(['train','held-out'])
        layout.addWidget(Q.QLabel('Split: record held-out in a separate sitting after repositioning the headset'));layout.addWidget(self.split)
        self.notes=Q.QLineEdit();self.notes.setPlaceholderText('Optional: describe noise, headset placement, gain (no secrets)');layout.addWidget(self.notes)
        self.status=Q.QLabel('Record one short example at a time. Breathe comfortably. No-breath means no intentional input; do not hold your breath.');self.status.setWordWrap(True);layout.addWidget(self.status,1)
        bar=Q.QHBoxLayout();layout.addLayout(bar)
        self.start=Q.QPushButton('Start recording');self.start.clicked.connect(self.begin);bar.addWidget(self.start)
        self.stop=Q.QPushButton('Stop and save');self.stop.clicked.connect(self.finish);self.stop.setEnabled(False);bar.addWidget(self.stop)
        self.timer=QtCore.QTimer(self);self.timer.timeout.connect(self.tick);self.timer.start(100)
    def callback(self,data,frames,timing,status):
        if status:self.flags.append(str(status))
        self.chunks.append(data[:,0].copy());self.frames+=frames
    def begin(self):
        if self.stream:return
        if not self.devices:self.status.setText('No microphone available.');return
        self.chunks=[];self.flags=[];self.frames=0
        try:
            self.stream=sd.InputStream(device=self.device.currentData(),channels=1,samplerate=RATE,dtype='float32',callback=self.callback)
            self.stream.start()
        except Exception as error:
            if self.stream:self.stream.close();self.stream=None
            self.status.setText('Could not start microphone: '+str(error));return
        self.started=datetime.now(timezone.utc).isoformat()
        for item in (self.device,self.category,self.background,self.split,self.notes,self.start):item.setEnabled(False)
        self.stop.setEnabled(True)
    def tick(self):
        if self.stream:self.status.setText(f'Recording {self.frames/RATE:.1f} s • {self.category.currentText()} • {self.background.currentText()}')
    def finish(self):
        if not self.stream:return
        self.stream.stop();self.stream.close();self.stream=None
        for item in (self.device,self.category,self.background,self.split,self.notes,self.start):item.setEnabled(True)
        self.stop.setEnabled(False)
        x=np.concatenate(self.chunks) if self.chunks else np.empty(0,dtype=np.float32)
        if not len(x):self.status.setText('No audio captured. Try again.');return
        peak=float(np.max(np.abs(x)))
        folder=ROOT/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]);folder.mkdir(parents=True)
        write(folder/'mic.wav',RATE,x)
        meta={'category':self.category.currentData(),'background':self.background.currentText(),'split':self.split.currentText(),
              'utc':self.started,'rate':RATE,'frames':len(x),'peak':peak,'clipped':peak>=.999,'audio_flags':self.flags,
              'device_id':self.device.currentData(),'device_name':self.device.currentText(),'notes':self.notes.text(),
              'label_type':'clip-level intended category; no event boundaries',
              'warning':'Inhale/exhale clips may include pauses. Do not use as frame-level labels without annotation.'}
        (folder/'metadata.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
        quality=' Check clipping or audio faults and repeat.' if peak>=.999 or self.flags else ''
        self.status.setText(f'Saved {len(x)/RATE:.1f}s • {self.category.currentText()} • {self.background.currentText()}.{quality}')
    def closeEvent(self,event):
        if self.stream:self.finish()
        event.accept()

if __name__=='__main__':
    app=Q.QApplication([]);window=Collector();window.show();app.exec()
