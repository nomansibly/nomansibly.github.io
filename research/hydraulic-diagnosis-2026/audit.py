import os,json,time,platform,hashlib
from pathlib import Path
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score,f1_score
from sklearn.model_selection import GroupShuffleSplit
from threadpoolctl import threadpool_limits
threadpool_limits(1)
out=Path('audit');out.mkdir(exist_ok=True)
names=['PS1','PS2','PS3','PS4','PS5','PS6','EPS1','FS1','FS2','TS1','TS2','TS3','TS4','VS1','CE','CP','SE']
def features(a):
 b=a.reshape(len(a),6,-1);t=np.linspace(0,1,a.shape[1]);t=t-t.mean();v=a-a.mean(1,keepdims=True);den=(v*v).sum(1)
 return np.column_stack([b.mean(2),b.std(2),np.sqrt((b*b).mean(2)),np.quantile(a,[.1,.5,.9],axis=1).T,a.min(1),a.max(1),(a@t)/(t@t),np.divide((v[:,:-1]*v[:,1:]).sum(1),den,out=np.zeros(len(a)),where=den>0)])
raw=[np.loadtxt('data/'+n+'.txt') for n in names]
X=np.column_stack([features(a) for a in raw]);y0=np.loadtxt('data/profile.txt',dtype=int)[:,:4];y=np.column_stack([np.unique(y0[:,k],return_inverse=True)[1] for k in range(4)])
profiles,groups=np.unique(y0,axis=0,return_inverse=True)
np.savez_compressed(out/'features.npz',X=X,y=y,groups=groups,profiles=profiles)
manifest=[];records=[];importance=[];latency=[]
for seed in range(10):
 rng=np.random.default_rng(seed)
 while True:
  ids=rng.permutation(len(profiles));tr,ca,te=ids[:100],ids[100:122],ids[122:]
  rows=[np.flatnonzero(np.isin(groups,g)) for g in [tr,ca,te]]
  if all(all(len(np.unique(y[ix,k]))==len(np.unique(y[:,k])) for k in range(4)) for ix in rows):break
 a,b,c=rows;manifest.append({'seed':seed,'train_rows':a.tolist(),'calibration_rows':b.tolist(),'test_rows':c.tolist(),'train_profiles':tr.tolist(),'calibration_profiles':ca.tolist(),'test_profiles':te.tolist()})
 models=[RandomForestClassifier(n_estimators=300,min_samples_leaf=2,max_features='sqrt',class_weight='balanced_subsample',random_state=seed,n_jobs=1).fit(X[a],y[a,k]) for k in range(4)]
 pred=np.column_stack([m.predict(X[c]) for m in models]);acc=np.array([accuracy_score(y[c,k],pred[:,k]) for k in range(4)])
 cp=[m.predict_proba(X[b]) for m in models];scores=np.max(np.column_stack([1-p[np.arange(len(b)),y[b,k]] for k,p in enumerate(cp)]),axis=1)
 gs=np.array([scores[groups[b]==g].max() for g in ca]);q=np.sort(gs)[20]
 probs=[m.predict_proba(X[c]) for m in models];included=np.column_stack([p[np.arange(len(c)),y[c,k]]>=1-q for k,p in enumerate(probs)])
 joint=included.all(1);pc=np.mean([joint[groups[c]==g].all() for g in te]);sizes=[(p>=1-q).sum(1).mean() for p in probs]
 records.append({'seed':seed,'accuracy':acc.tolist(),'macro_f1':[f1_score(y[c,k],pred[:,k],average='macro') for k in range(4)],'cycle_coverage':float(joint.mean()),'profile_coverage':float(pc),'set_size':sizes,'threshold':float(q)})
 for si,n in enumerate(names):
  drops=[]
  for rep in range(5):
   xp=X[c].copy();perm=np.random.default_rng(seed*1000+si*10+rep).permutation(len(c));xp[:,si*25:(si+1)*25]=xp[perm,si*25:(si+1)*25]
   drops.append(acc-np.array([accuracy_score(y[c,k],m.predict(xp)) for k,m in enumerate(models)]))
  importance.append({'seed':seed,'sensor':n,'drop':np.mean(drops,axis=0).tolist()})
 for _ in range(3):[m.predict(X[c[:1]]) for m in models]
 times=[];ft=[]
 for row in c[:50]:
  st=time.perf_counter_ns();xx=np.column_stack([features(v[row:row+1]) for v in raw]);ft.append((time.perf_counter_ns()-st)/1e6)
  st=time.perf_counter_ns();[m.predict(xx) for m in models];times.append((time.perf_counter_ns()-st)/1e6)
 latency.append({'seed':seed,'feature_ms_median':float(np.median(ft)),'feature_ms_p95':float(np.quantile(ft,.95)),'inference_ms_median':float(np.median(times)),'inference_ms_p95':float(np.quantile(times,.95))})
 for name,obj in [('partitions',manifest),('scores',records),('importance',importance),('latency',latency)]: (out/(name+'.json')).write_text(json.dumps(obj,indent=2))
 print('completed',seed,flush=True)
(out/'environment.json').write_text(json.dumps({'platform':platform.platform(),'python':platform.python_version(),'cpu':Path('/proc/cpuinfo').read_text().split('model name')[1].split('\n')[0] if Path('/proc/cpuinfo').exists() else platform.processor(),'archive_sha256':hashlib.sha256(Path('hydraulic_data.zip').read_bytes()).hexdigest(),'note':'New partitions; original manuscript partition identities unavailable.'},indent=2))
