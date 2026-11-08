"""Propose weak, amplitude-based markers for labeled audio; never overwrite reviews."""
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.ndimage import uniform_filter1d, binary_closing

ROOT=Path(__file__).resolve().parent/'breath_noise_dataset'

def propose(x,rate,label):
    if x.ndim!=1 or not len(x):raise ValueError('Expected nonempty mono audio')
    if label=='NO_BREATH':
        return [{'start_sample':0,'end_sample':len(x),'label':label}],None
    if label not in ('INHALE','EXHALE'):raise ValueError('Unexpected category')
    x=np.asarray(x,dtype=np.float64)
    width=max(1,round(.05*rate));hop=max(1,round(.025*rate))
    if len(x)<width:return [],'clip shorter than one analysis window'
    sq=np.r_[0.,np.cumsum(x*x)]
    starts=np.arange(0,len(x)-width+1,hop)
    rms=np.sqrt(np.maximum((sq[starts+width]-sq[starts])/width,0))
    smooth=uniform_filter1d(rms,size=5,mode='nearest')
    low=float(np.percentile(smooth,20));high=float(np.max(smooth))
    if high<1e-6 or high<low*1.5:return [],'no clear amplitude rise'
    threshold=low+.3*(high-low)
    active=smooth>=threshold
    # Close short gaps, then choose the strongest contiguous region.
    active=binary_closing(active,structure=np.ones(5,dtype=bool),border_value=0)
    edges=np.diff(np.r_[False,active,False].astype(int));regions=list(zip(np.flatnonzero(edges==1),np.flatnonzero(edges==-1)))
    regions=[(a,b) for a,b in regions if (b-a)*hop/rate>=.1]
    if not regions:return [],'no sustained amplitude rise'
    a,b=max(regions,key=lambda ab:float(np.sum(smooth[ab[0]:ab[1]]**2)))
    pad=round(.05*rate)
    start=max(0,int(starts[a])-pad);end=min(len(x),int(starts[b-1])+width+pad)
    return [{'start_sample':start,'end_sample':end,'label':label}],None


def run(apply=False):
    counts={};skips=[]
    for meta_path in sorted(ROOT.glob('*/metadata.json')):
        folder=meta_path.parent;target=folder/'annotations.json'
        if target.exists():counts['existing']=counts.get('existing',0)+1;continue
        meta=json.loads(meta_path.read_text(encoding='utf-8-sig'))
        rate,x=wavfile.read(folder/'mic.wav'); label=meta.get('category')
        if np.issubdtype(x.dtype,np.integer):x=x.astype(np.float64)/np.iinfo(x.dtype).max
        segments,reason=propose(x,rate,label)
        if reason:
            counts['ambiguous']=counts.get('ambiguous',0)+1;skips.append({'clip':folder.name,'label':label,'reason':reason});continue
        data={'version':1,'audio':'mic.wav','sample_rate':rate,'total_samples':len(x),'segments':segments,
              'saved_utc':datetime.now(timezone.utc).isoformat(), 'review_status':'PROVISIONAL_AUTOMATIC',
              'method':'whole_clip_intended_no_breath' if label=='NO_BREATH' else 'amplitude_peak_heuristic_v1',
              'warning':'Not human verified. Background sounds can be louder than breath; do not treat as ground truth.'}
        if apply:
            try:
                with target.open('x',encoding='utf-8') as out:json.dump(data,out,indent=2)
            except FileExistsError:counts['existing']=counts.get('existing',0)+1;continue
        counts[label]=counts.get(label,0)+1
    print(json.dumps({'applied':apply,'counts':counts,'ambiguous':skips},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args();run(args.apply)
