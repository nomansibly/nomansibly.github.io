import json,time,platform
from pathlib import Path
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from threadpoolctl import threadpool_limits
threadpool_limits(1)
while True:
 try:
  if len(json.load(open('audit/cross_scores.json')))==10:break
 except FileNotFoundError:pass
 time.sleep(1)
# No model training jobs remain; record single-thread batch-one CPU timings.
z=np.load('audit/features.npz');X,y=z['X'],z['y'];split=json.load(open('audit/partitions.json'))[0];a,c=split['train_rows'],split['test_rows'];ms=[RandomForestClassifier(n_estimators=300,min_samples_leaf=2,max_features='sqrt',class_weight='balanced_subsample',random_state=0,n_jobs=1).fit(X[a],y[a,k]) for k in range(4)]
# Execute the exact feature function without importing its experiment loop.
s=Path('audit.py').read_text();code=s[s.index('def features(a):'):s.index('raw=[np.loadtxt')];exec(code)
names=['PS1','PS2','PS3','PS4','PS5','PS6','EPS1','FS1','FS2','TS1','TS2','TS3','TS4','VS1','CE','CP','SE'];raw=[np.loadtxt('data/'+n+'.txt') for n in names]
for _ in range(10):[m.predict(X[c[:1]]) for m in ms]
ft=[];inf=[];total=[]
for ix in np.random.default_rng(2026).choice(c,200,replace=True):
 st=time.perf_counter_ns();xx=np.column_stack([features(v[ix:ix+1]) for v in raw]);mid=time.perf_counter_ns();[m.predict(xx) for m in ms];end=time.perf_counter_ns();ft.append((mid-st)/1e6);inf.append((end-mid)/1e6);total.append((end-st)/1e6)
r={'protocol':'Seed 0 model, batch one, 10 inference warmups, 200 randomly selected test cycles with replacement, one thread, no other experiment jobs; excludes disk I/O, model loading and 60-second acquisition','cpu':Path('/proc/cpuinfo').read_text().split('model name')[1].split('\n')[0].strip(': \t'),'platform':platform.platform()}
for n,v in [('feature',ft),('inference',inf),('total',total)]:r[n+'_median_ms']=float(np.median(v));r[n+'_p95_ms']=float(np.quantile(v,.95))
Path('audit/isolated_latency.json').write_text(json.dumps(r,indent=2));print(r)
