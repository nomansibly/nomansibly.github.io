import json
from pathlib import Path
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from threadpoolctl import threadpool_limits
threadpool_limits(1);out=Path('audit');z=np.load(out/'features.npz');X,y,g,profiles=[z[n] for n in ['X','y','groups','profiles']];K=[len(np.unique(y[:,k])) for k in range(4)];records=[]
for seed in range(10):
 rng=np.random.default_rng(seed)
 while True:
  ids=rng.permutation(len(profiles));tr,ca,te=ids[:100],ids[100:122],ids[122:];rows=[np.flatnonzero(np.isin(g,j)) for j in [tr,ca,te]]
  if all(all(len(np.unique(y[ix,k]))==K[k] for k in range(4)) for ix in rows):break
 dev=np.concatenate([tr,ca]);c=rows[2];folds=np.array_split(np.random.default_rng(seed+10000).permutation(dev),5);counts=[np.zeros((len(c),k)) for k in K]
 for fi,held in enumerate(folds):
  a=np.flatnonzero(np.isin(g,np.setdiff1d(dev,held)));b=np.flatnonzero(np.isin(g,held));ms=[RandomForestClassifier(n_estimators=300,min_samples_leaf=2,max_features='sqrt',class_weight='balanced_subsample',random_state=seed*10+fi,n_jobs=1).fit(X[a],y[a,k]) for k in range(4)]
  if any(len(m.classes_)!=K[k] for k,m in enumerate(ms)):raise ValueError('Missing class in inner training')
  pb=[m.predict_proba(X[b]) for m in ms];sc=np.max(np.column_stack([1-p[np.arange(len(b)),y[b,k]] for k,p in enumerate(pb)]),1);gs=np.array([sc[g[b]==h].max() for h in held])
  for k,m in enumerate(ms):counts[k]+=(gs[:,None,None]>=1-m.predict_proba(X[c])[None,:,:]).sum(0)
 ps=[(1+v)/(len(dev)+1) for v in counts];sets=[p>.1 for p in ps];joint=np.column_stack([s[np.arange(len(c)),y[c,k]] for k,s in enumerate(sets)]).all(1)
 records.append({'seed':seed,'development_profiles':len(dev),'inner_folds':5,'profile_coverage':float(np.mean([joint[g[c]==h].all() for h in te])),'cycle_coverage':float(joint.mean()),'set_size':[float(s.sum(1).mean()) for s in sets]});(out/'cross_scores.json').write_text(json.dumps(records,indent=2));print('completed',seed,flush=True)
