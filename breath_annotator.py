"""Review saved breath recordings and label sample-accurate audio intervals."""
import json, os
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import sounddevice as sd
from scipy.io import wavfile
from PySide6 import QtCore, QtWidgets as Q
import pyqtgraph as pg

ROOT = Path(__file__).resolve().parent / 'breath_noise_dataset'
LABELS = ('INHALE', 'EXHALE', 'NO_BREATH')


def validate_segment(start, end, label, length, existing):
    start, end = int(start), int(end)
    if label not in LABELS or not 0 <= start < end <= length:
        raise ValueError('Choose a non-empty interval inside the recording.')
    if any(start < item['end_sample'] and end > item['start_sample'] for item in existing):
        raise ValueError('This interval overlaps an existing marker. Remove that marker first.')
    return {'start_sample': start, 'end_sample': end, 'label': label}


class Annotator(Q.QWidget):
    def __init__(self):
        super().__init__(); self.setWindowTitle('Breath audio annotation'); self.resize(1320,800)
        self.entries=[]; self.path=None; self.samples=None; self.rate=None; self.segments=[]; self.dirty=False; self.updating=False
        root=Q.QHBoxLayout(self); side=Q.QVBoxLayout();root.addLayout(side,1)
        side.addWidget(Q.QLabel('Recordings'))
        self.filter=Q.QComboBox(); self.filter.addItems(['Selected training clips','Needs review','Reviewed']); side.addWidget(self.filter)
        self.clips=Q.QListWidget();side.addWidget(self.clips,1)
        self.reload=Q.QPushButton('Reload recordings');self.reload.clicked.connect(self.load_list);side.addWidget(self.reload)
        main=Q.QVBoxLayout();root.addLayout(main,3)
        self.info=Q.QLabel('Choose a recording. Drag the shaded region to select an interval.');self.info.setWordWrap(True);main.addWidget(self.info)
        self.plot=pg.PlotWidget();self.plot.setLabel('bottom','Time',units='s');self.plot.setLabel('left','Amplitude');self.plot.showGrid(x=True,y=True,alpha=.2);main.addWidget(self.plot,1)
        self.curve=self.plot.plot(pen=pg.mkPen('#50b8e7',width=1));self.marker_regions=[]
        self.region=pg.LinearRegionItem(values=[0,1],brush=(100,170,255,50));self.plot.addItem(self.region)
        self.region.sigRegionChanged.connect(self.selection_changed)
        self.selection=Q.QLabel('Selection: —');main.addWidget(self.selection)
        output_row=Q.QHBoxLayout();main.addLayout(output_row)
        output_row.addWidget(Q.QLabel('Playback device:'))
        self.output=Q.QComboBox();hosts=sd.query_hostapis();default_output=sd.default.device[1]
        for index,device in enumerate(sd.query_devices()):
            if device['max_output_channels']:
                self.output.addItem(f"{device['name']} ({hosts[device['hostapi']]['name']})",index)
        default_index=self.output.findData(default_output)
        if default_index>=0:self.output.setCurrentIndex(default_index)
        output_row.addWidget(self.output,1)
        self.boost=Q.QCheckBox('Boost quiet playback');self.boost.setChecked(True);output_row.addWidget(self.boost)
        test=Q.QPushButton('Test output');test.clicked.connect(self.test_output);output_row.addWidget(test)
        row=Q.QHBoxLayout();main.addLayout(row)
        for title,fn in [('Play entire clip',self.play_all),('Play selection',self.play_selection),('Stop playback',sd.stop)]:
            button=Q.QPushButton(title);button.clicked.connect(fn);row.addWidget(button)
        row=Q.QHBoxLayout();main.addLayout(row)
        for label in LABELS:
            button=Q.QPushButton('Mark '+label.replace('_',' '));button.clicked.connect(lambda checked=False,l=label:self.add_marker(l));row.addWidget(button)
        main.addWidget(Q.QLabel('Markers: green = inhale, red = exhale, gold = no breath. Unmarked audio stays unlabeled.'))
        self.markers=Q.QListWidget();self.markers.setMaximumHeight(155);main.addWidget(self.markers)
        row=Q.QHBoxLayout();main.addLayout(row)
        remove=Q.QPushButton('Remove selected marker');remove.clicked.connect(self.remove_marker);row.addWidget(remove)
        self.save=Q.QPushButton('Save markers');self.save.clicked.connect(self.save_markers);row.addWidget(self.save)
        self.status=Q.QLabel('');self.status.setWordWrap(True);main.addWidget(self.status)
        self.clips.currentRowChanged.connect(self.open_clip);self.filter.currentIndexChanged.connect(self.load_list)
        self.load_list()
    def maybe_discard(self):
        if not self.dirty:return True
        return Q.QMessageBox.question(self,'Unsaved markers','Discard unsaved markers?')==Q.QMessageBox.StandardButton.Yes
    def load_list(self):
        if not self.maybe_discard():return
        self.dirty=False;sd.stop();self.updating=True;self.clips.clear();self.entries=[];self.path=None;self.samples=None
        self.curve.setData([],[]);self.segments=[];self.refresh_markers()
        try:
            subset=json.loads((ROOT/'annotation_subset.json').read_text(encoding='utf-8'))['clips']
        except (OSError,ValueError,KeyError):
            self.updating=False;self.status.setText('Training selection not found.');return
        for selected in subset:
            meta_path=ROOT/selected['folder']/'metadata.json'
            try:
                meta=json.loads(meta_path.read_text(encoding='utf-8-sig'));audio=meta_path.parent/'mic.wav';annot=meta_path.parent/'annotations.json'
                if not audio.exists():continue
                flag='○'
                if annot.exists():
                    saved=json.loads(annot.read_text(encoding='utf-8'))
                    flag='AUTO' if saved.get('review_status')=='PROVISIONAL_AUTOMATIC' else '✓'
                if self.filter.currentIndex()==1 and flag=='✓':continue
                if self.filter.currentIndex()==2 and flag!='✓':continue
                self.entries.append((meta_path.parent,meta));self.clips.addItem(f"{selected['number']:02d}  {flag}  {meta.get('category','?')} | {meta.get('background','?')}")
            except (ValueError,OSError):continue
        self.updating=False;self.status.setText(f'{len(self.entries)} selected training recordings. AUTO markers need review.')
    def open_clip(self,index):
        if self.updating or index<0:return
        if not self.maybe_discard():
            self.updating=True;self.clips.setCurrentRow(next((i for i,(p,m) in enumerate(self.entries) if p==self.path),-1));self.updating=False;return
        sd.stop();folder,meta=self.entries[index]
        try:
            rate,samples=wavfile.read(folder/'mic.wav')
            if samples.ndim!=1 or not len(samples):raise ValueError('Expected a nonempty mono recording.')
            if np.issubdtype(samples.dtype,np.integer):samples=samples.astype(np.float32)/np.iinfo(samples.dtype).max
            else:samples=samples.astype(np.float32)
            ann=folder/'annotations.json';data=json.loads(ann.read_text(encoding='utf-8')) if ann.exists() else {}
            if data and (data.get('sample_rate')!=rate or data.get('total_samples')!=len(samples)):raise ValueError('Saved markers do not match this audio.')
            existing=[]
            for item in data.get('segments',[]):existing.append(validate_segment(item['start_sample'],item['end_sample'],item['label'],len(samples),existing))
        except (OSError,ValueError,KeyError) as error:self.status.setText('Could not open clip: '+str(error));return
        self.path,self.samples,self.rate,self.segments=folder,samples,rate,existing;self.dirty=False
        stride=max(1,int(np.ceil(len(samples)/30000)));indices=np.arange(0,len(samples),stride)
        self.curve.setData(indices/rate,samples[::stride]);duration=len(samples)/rate
        self.plot.setXRange(0,duration,padding=.01);self.plot.setYRange(-1,1,padding=.05)
        self.region.setBounds([0,duration]);self.region.setRegion((0,min(1,duration)))
        self.info.setText(f"Intended clip: {meta.get('category')} • {meta.get('background')} • {meta.get('split')} • {duration:.2f} s")
        self.refresh_markers()
        if data.get('review_status')=='PROVISIONAL_AUTOMATIC':
            self.status.setText('AUTO estimate — not verified. Background noise can be marked as a breath. Listen before relying on it.')
        else:self.status.setText('Listen, drag the shaded region, then mark the interval. Unmarked audio stays unlabeled.')
    def selection_changed(self):
        if self.rate:self.selection.setText('Selection: %.2f–%.2f s'%tuple(self.region.getRegion()))
    def selected_indices(self):
        start,end=sorted(self.region.getRegion());return max(0,round(start*self.rate)),min(len(self.samples),round(end*self.rate))
    def play_all(self):
        if self.samples is not None:self.play(self.samples)
    def play_selection(self):
        if self.samples is not None:
            a,b=self.selected_indices();self.play(self.samples[a:b])
    def test_output(self):
        rate=48000;t=np.arange(int(rate*.3))/rate
        signal=(.04*np.sin(2*np.pi*440*t)*np.sin(np.pi*np.arange(len(t))/len(t))**2).astype(np.float32)
        self.play_audio(signal,rate,'Test tone')
    def play(self,samples):
        if not len(samples):self.status.setText('The selection is empty.');return
        signal=np.asarray(samples,dtype=np.float32)
        gain=1.0
        if self.boost.isChecked() and self.samples is not None:
            peak=float(np.max(np.abs(self.samples)))
            if peak>0:gain=min(1000.0,.5/peak)
        signal=np.clip(signal*gain,-1,1)
        self.play_audio(signal,self.rate,f'Playing audio (gain {gain:.0f}×)')
    def play_audio(self,samples,rate,description):
        if self.output.currentData() is None:self.status.setText('No playback device is available.');return
        try:
            sd.stop();sd.play(samples,rate,device=self.output.currentData(),blocking=False)
            self.status.setText(description+' through '+self.output.currentText())
        except Exception as error:self.status.setText('Playback failed: '+str(error))
    def add_marker(self,label):
        if self.samples is None:return
        try:
            a,b=self.selected_indices();segment=validate_segment(a,b,label,len(self.samples),self.segments)
        except ValueError as error:self.status.setText(str(error));return
        self.segments.append(segment);self.segments.sort(key=lambda x:x['start_sample']);self.dirty=True;self.refresh_markers();self.status.setText('Marker added. Click Save markers before changing clips.')
    def refresh_markers(self):
        self.markers.clear()
        for region in self.marker_regions:self.plot.removeItem(region)
        self.marker_regions=[]
        colors={'INHALE':(40,210,130,70),'EXHALE':(255,100,95,70),'NO_BREATH':(235,190,60,70)}
        for item in self.segments:
            start,end=item['start_sample']/self.rate,item['end_sample']/self.rate
            self.markers.addItem(f"{start:.2f}–{end:.2f} s  {item['label']}")
            region=pg.LinearRegionItem(values=(start,end),movable=False,brush=colors[item['label']])
            region.setZValue(-10);self.plot.addItem(region);self.marker_regions.append(region)
    def remove_marker(self):
        i=self.markers.currentRow()
        if 0<=i<len(self.segments):self.segments.pop(i);self.dirty=True;self.refresh_markers()
    def save_markers(self):
        if self.path is None:return
        if not self.segments:self.status.setText('Add at least one marker before saving.');return
        data={'version':1,'audio':'mic.wav','sample_rate':self.rate,'total_samples':len(self.samples),'segments':self.segments,'saved_utc':datetime.now(timezone.utc).isoformat()}
        target=self.path/'annotations.json';tmp=self.path/'annotations.json.tmp'
        try:tmp.write_text(json.dumps(data,indent=2),encoding='utf-8');os.replace(tmp,target)
        except OSError as error:self.status.setText('Could not save markers: '+str(error));return
        self.dirty=False;self.status.setText('Markers saved. Choose the next recording.')
        i=self.clips.currentRow()
        if i>=0:self.clips.item(i).setText(self.clips.item(i).text().replace('○','✓',1).replace('AUTO','✓',1))
    def closeEvent(self,event):
        if not self.maybe_discard():event.ignore();return
        sd.stop();event.accept()

if __name__=='__main__':
    app=Q.QApplication([]);w=Annotator();w.show();app.exec()
