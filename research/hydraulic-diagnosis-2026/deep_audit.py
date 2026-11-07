import json,time
from pathlib import Path
import numpy as np,torch
from torch import nn
from sklearn.metrics import accuracy_score,f1_score
from scipy.optimize import minimize_scalar
from scipy.special import softmax
from threadpoolctl import threadpool_limits
threadpool_limits(1);torch.set_num_threads(2)
out=Path('audit');z=np.load(out/'features.npz');y=z['y'];groups=z['groups'];profiles=z['profiles'];K=[len(np.unique(y[:,k])) for k in range(4)];cuts=np.cumsum([0]+K)
names=['PS1','PS2','PS3','PS4','PS5','PS6','EPS1','FS1','FS2','TS1','TS2','TS3','TS4','VS1','CE','CP','SE'];raw=[np.loadtxt('data/'+n+'.txt',dtype=np.float32) for n in names]
class CNN(nn.Module):
 def __init__(self):
  super().__init__();self.br=nn.ModuleList([nn.Sequential(nn.Conv1d(c,16,k,stride=s,padding=k//2),nn.ReLU(),nn.Conv1d(16,32,3,padding=1),nn.ReLU(),nn.AdaptiveAvgPool1d(4),nn.Flatten()) for c,k,s in [(7,31,20),(2,7,2),(8,3,1)]]);self.fc=nn.Linear(384,sum(K))
 def forward(self,x):return self.fc(torch.cat([b(a) for b,a in zip(self.br,x)],1))
class Mixer(nn.Module):
 def __init__(self):
  super().__init__();self.emb=nn.Linear(728,32);self.ln1=nn.LayerNorm(32);self.token=nn.Sequential(nn.Linear(60,32),nn.GELU(),nn.Linear(32,60));self.ln2=nn.LayerNorm(32);self.channel=nn.Sequential(nn.Linear(32,64),nn.GELU(),nn.Linear(64,32));self.fc=nn.Linear(32,sum(K))
 def forward(self,x):
  a=self.emb(x[0]);a=a+self.token(self.ln1(a).transpose(1,2)).transpose(1,2);a=a+self.channel(self.ln2(a));return self.fc(a.mean(1))
def prob(logits,T=1):return [softmax(logits[:,cuts[k]:cuts[k+1]]/T,axis=1) for k in range(4)]
def coverage(pc,pt,b,c,calgroups):
 scores=np.max(np.column_stack([1-p[np.arange(len(b)),y[b,k]] for k,p in enumerate(pc)]),1);gs=np.array([scores[groups[b]==g].max() for g in calgroups]);r=int(np.ceil((len(gs)+1)*.9));q=np.sort(gs)[r-1] if r<=len(gs) else np.inf
 joint=np.column_stack([p[np.arange(len(c)),y[c,k]]>=1-q for k,p in enumerate(pt)]).all(1)
 return {'profile_coverage':float(np.mean([joint[groups[c]==g].all() for g in np.unique(groups[c])])),'cycle_coverage':float(joint.mean()),'set_size':[float((p>=1-q).sum(1).mean()) for p in pt],'calibration_profiles':len(gs)}
records=[]
for seed in range(10):
 rng=np.random.default_rng(seed)
 while True:
  ids=rng.permutation(len(profiles));tr,ca,te=ids[:100],ids[100:122],ids[122:];a,b,c=[np.flatnonzero(np.isin(groups,g)) for g in [tr,ca,te]]
  if all(all(len(np.unique(y[ix,k]))==K[k] for k in range(4)) for ix in [a,b,c]):break
 normalized=[(v-v[a].mean())/max(float(v[a].std()),1e-6) for v in raw]
 cnn=[torch.from_numpy(np.stack(normalized[lo:hi],1)) for lo,hi in [(0,7),(7,9),(9,17)]]
 mixer=[torch.from_numpy(np.concatenate([v.reshape(len(v),60,-1) for v in normalized],2))]
 for name,cls,data in [('MultirateCNN',CNN,cnn),('PatchMixer',Mixer,mixer)]:
  torch.manual_seed(seed);m=cls();opt=torch.optim.AdamW(m.parameters(),lr=.001,weight_decay=.0001);ys=torch.from_numpy(y).long();m.train()
  for epoch in range(20):
   order=a[np.random.default_rng(seed*100+epoch).permutation(len(a))]
   for start in range(0,len(a),64):
    ix=order[start:start+64];logits=m([v[ix] for v in data]);loss=sum(nn.functional.cross_entropy(logits[:,cuts[k]:cuts[k+1]],ys[ix,k]) for k in range(4));opt.zero_grad();loss.backward();opt.step()
  m.eval()
  def logits(ix):
   with torch.no_grad():return np.concatenate([m([v[ix[start:start+64]] for v in data]).numpy() for start in range(0,len(ix),64)])
  lb,lc=logits(b),logits(c);pc,pt=prob(lb),prob(lc);pred=np.column_stack([p.argmax(1) for p in pt]);rec={'seed':seed,'model':name,'epochs':20,'accuracy':[accuracy_score(y[c,k],pred[:,k]) for k in range(4)],'macro_f1':[f1_score(y[c,k],pred[:,k],average='macro') for k in range(4)],'split_conformal':coverage(pc,pt,b,c,ca)}
  # Disjoint calibration profiles for temperature fitting and thresholding.
  tempgroups=ca[:11];qgroups=ca[11:];tm=np.isin(groups[b],tempgroups);qm=~tm
  def nll(logt):
   pp=prob(lb[tm],np.exp(logt));return np.mean([-np.log(np.maximum(p[np.arange(tm.sum()),y[b[tm],k]],1e-12)).mean() for k,p in enumerate(pp)])
  T=float(np.exp(minimize_scalar(nll,bounds=(-3,3),method='bounded').x));rec['temperature']=T;rec['temperature_threshold']=coverage(prob(lb[qm],T),prob(lc,T),b[qm],c,qgroups)
  torch.save(m.state_dict(),out/f'{name}_{seed}.pt');records.append(rec);(out/'deep_scores.json').write_text(json.dumps(records,indent=2));print('completed',seed,name,flush=True)
