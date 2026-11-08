"""One-second feature extraction and streaming classification."""
from collections import deque
from pathlib import Path
import pickle
import numpy as np

RATE = 48000
HOP = 2400
FRAMES = 20
BANDS = ((80,300),(300,700),(700,1500),(1500,3000),(3000,6000),(6000,12000))
MODEL_PATH = Path(__file__).resolve().parent / 'model' / 'breath_1000ms.pkl'

def frame_features(samples):
    x = np.asarray(samples, dtype=float)
    if x.shape != (HOP,):
        raise ValueError('Expected 2400 mono samples at 48 kHz')
    power = abs(np.fft.rfft(x*np.hanning(HOP)))**2 / HOP**2
    frequencies = np.fft.rfftfreq(HOP, 1/RATE)
    return np.array([np.log10(np.mean(power[(frequencies>=low)&(frequencies<high)])+1e-12) for low,high in BANDS])

def window_features(samples):
    x = np.asarray(samples)
    if x.shape != (RATE,):
        raise ValueError('Expected exactly one second of mono audio at 48 kHz')
    f = np.asarray([frame_features(x[i:i+HOP]) for i in range(0,RATE,HOP)])
    return np.concatenate((f.mean(axis=0),f.std(axis=0)))

def load_model(path=MODEL_PATH):
    # Pickle executes code: only load a model received from a trusted source.
    with open(path,'rb') as handle: bundle = pickle.load(handle)
    if bundle['window_ms'] != 1000 or bundle['feature'] != 'mean_std_6band_v1':
        raise ValueError('Unexpected checkpoint format')
    return bundle['model']

class StreamClassifier:
    def __init__(self,model):
        self.model=model; self.reset()
    def reset(self):
        self.frames=deque(maxlen=FRAMES); self.current='SILENCE'; self.candidate='SILENCE'; self.count=0
    def advance(self,samples):
        self.frames.append(frame_features(samples))
        if len(self.frames)<FRAMES: return None
        f=np.asarray(self.frames); vector=np.r_[f.mean(axis=0),f.std(axis=0)]
        predicted=str(self.model.predict(vector.reshape(1,-1))[0])
        if predicted == self.candidate: self.count+=1
        else: self.candidate=predicted; self.count=1
        if self.count>=3:self.current=predicted
        return {'label':self.current,'raw_label':predicted}
