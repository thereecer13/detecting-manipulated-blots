import json,re,hashlib,sys,os,random,numpy as np
sys.path.insert(0,'band')
from bandlib import load
from outline import features
from collections import Counter
o=json.load(open('band/all_out.json'));it={i[0]:i for i in json.load(open('band/all_items.json'))}
key=json.load(open('band/review_key.json'));done={s['name'] for s in key.values()};donecat={s['cat'] for s in key.values()}
def geom_ok(hh,pad=4):
    x,y,w,h=hh[3];lx,ly=hh[4];pw,ph=w+2*pad,h+2*pad
    return w>=30 and h>=10 and (abs(lx-(x-pad))>=pw or abs(ly-(y-pad))>=ph)
def bar(g,hh):
    x,y,w,h=hh[3];P=g[y:y+h,x:x+w];v,c=np.unique(P,return_counts=True);i=c.argmax();return c[i]/P.size>0.3 and v[i]>30
rows=[];n=0;why=Counter()
for r in o:
    for hh in r[2]:
        if hh[0]>0.05: break
        if not geom_ok(hh): continue
        n+=1;g=load(it[r[0]][1])
        if bar(g,hh): why['bar']+=1;continue
        f=features(g,hh)
        if f is None: why['nofeat']+=1;continue
        if f['touch']: why['partial band']+=1;continue
        if f['unusual']<0.05: why['symmetric oval']+=1;continue
        if f['outline']<0.94: why['outline<0.94']+=1;continue
        rows.append((f['outline']*(0.5+min(f['unusual'],0.3))*(1 if hh[2]=='same' else 0.9),r[0],hh,f))
print(n,'candidate matches;',why,'kept',len(rows))
best={}
for x in sorted(rows,key=lambda x:-x[0]): best.setdefault(x[1],x)
rows=sorted(best.values(),key=lambda x:-x[0]);print(len(rows),'images; already labelled',sum(x[1] in done for x in rows))
json.dump([[x[0],x[1],x[2],x[3]] for x in rows],open('band/round2_rank.json','w'))
