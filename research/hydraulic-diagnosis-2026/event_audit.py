import json
from pathlib import Path
import numpy as np
from scipy.signal import find_peaks
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score,f1_score
from threadpoolctl import threadpool_limits
threadpool_limits(1);out=Path('audit');z=np.load(out/'features.npz');X,y,g,profiles=[z[n] for n in ['X','y','groups','profiles']];names=['PS1','PS2','PS3','PS4','PS5','PS6','EPS1','FS1','FS2','TS1','TS2','TS3','TS4','VS1','CE','CP','SE'];raw=[np.loadtxt('data/'+n+'.txt') for n in names];K=[len(np.unique(y[:,k])) for k in range(4)];records=[]
for seed in range(10):
 rng=np.random.default_rng(seed)
 while True:
  ids=rng.permutation(len(profiles));tr,ca,te=ids[:100],ids[100:122],ids[122:];a,b,c=[np.flatnonzero(np.isin(g,j)) for j in [tr,ca,te]]
  if all(all(len(np.unique(y[ix,k]))==K[k] for k in range(4)) for ix in [a,b,c]):break
 pressure=np.median(raw[1][a].reshape(len(a),60,100).mean(2),axis=0);strength=np.abs(np.diff(pressure));peaks,_=find_peaks(strength,distance=3);chosen=sorted((peaks[np.argsort(strength[peaks])[-5:]]+1).tolist());bounds=[0]+chosen+[60]
 if len(chosen)!=5:raise ValueError('Insufficient resolved pressure transitions')
 feats=[]
 for si,v in enumerate(raw):
  rate=v.shape[1]//60;chunks=[v[:,lo*rate:hi*rate] for lo,hi in zip(bounds[:-1],bounds[1:])];feats.append(np.column_stack([np.column_stack([vv.mean(1) for vv in chunks]),np.column_stack([vv.std(1) for vv in chunks]),np.column_stack([np.sqrt((vv*vv).mean(1)) for vv in chunks]),X[:,si*25+18:(si+1)*25]]))
 xx=np.column_stack(feats);ms=[RandomForestClassifier(n_estimators=300,min_samples_leaf=2,max_features='sqrt',class_weight='balanced_subsample',random_state=seed,n_jobs=1).fit(xx[a],y[a,k]) for k in range(4)];pred=np.column_stack([m.predict(xx[c]) for m in ms]);records.append({'seed':seed,'boundaries_seconds':bounds,'accuracy':[accuracy_score(y[c,k],pred[:,k]) for k in range(4)],'macro_f1':[f1_score(y[c,k],pred[:,k],average='macro') for k in range(4)]});(out/'event_scores.json').write_text(json.dumps(records,indent=2));print('completed',seed,flush=True)
