"""Retrain or evaluate the portable one-second model using the frozen split."""
import argparse
import hashlib
import json
import pickle
from collections import Counter
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score,confusion_matrix
from breath_model import RATE,MODEL_PATH,load_model,window_features

ROOT=Path(__file__).resolve().parent
LABELS=['SILENCE','INHALE','EXHALE']
def load_data(split):
    rows=json.loads((ROOT/'data/manifest.json').read_text(encoding='utf-8'))['clips']
    X=[];y=[];groups=[];hashes=[]
    for row in rows:
        if row['split'] != split: continue
        path=ROOT/row['path'];digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if digest!=row['sha256']: raise ValueError('SHA-256 mismatch: '+str(path))
        rate,x=wavfile.read(path)
        if rate!=RATE or x.ndim!=1:raise ValueError('Expected mono 48 kHz: '+str(path))
        if np.issubdtype(x.dtype,np.integer):x=x.astype(float)/np.iinfo(x.dtype).max
        x=np.asarray(x,dtype=np.float32); start=row['start_sample']; segment=x[start:start+RATE]
        X.append(window_features(segment));y.append(row['label']);groups.append(row['source']);hashes.append(digest)
    return np.asarray(X),np.asarray(y),np.asarray(groups),set(hashes)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--train',action='store_true');parser.add_argument('--output',type=Path,default=ROOT/'model/retrained_candidate.pkl');args=parser.parse_args()
    X,y,_,train_hash=load_data('train'); T,actual,group,test_hash=load_data('held-out')
    if train_hash & test_hash:raise ValueError('Duplicate audio across train and test')
    if args.train:
        model=RandomForestClassifier(n_estimators=200,max_depth=8,min_samples_leaf=2,random_state=42,n_jobs=1,class_weight='balanced');model.fit(X,y)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open('wb') as handle:pickle.dump({'model':model,'window_ms':1000,'frame_ms':50,'feature':'mean_std_6band_v1','classes':LABELS},handle)
        print('Saved candidate:',args.output)
    else:model=load_model()
    print('Training clips:',dict(Counter(y)))
    for name in ('original','fresh'):
        sel=group==name; predicted=model.predict(T[sel]);truth=actual[sel]
        print(name,'held-out clips:',len(truth),'classes:',dict(Counter(truth)),'accuracy:',round(float(accuracy_score(truth,predicted)),4))
        print('Confusion matrix rows/columns',LABELS,':',confusion_matrix(truth,predicted,labels=LABELS).tolist())

if __name__=='__main__':main()
