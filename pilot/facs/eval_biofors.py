import json,sys,time
sys.path.insert(0,'/home/user/detecting-manipulated-blots/pilot/facs')
import numpy as np
from PIL import Image
from multiprocessing import Pool
import panelmatch as pm
A='biofors_repo/annotation_files/'
ix=json.load(open('biofors/facs_index.json'))
pos={(d,frozenset(p.split())) for d,p in ix['pos']}
pairs=[]
for f in ('edd_train_pairs.json','edd_test_pairs.json'):
    for doc,d in json.load(open(A+f)).items():
        for p in d.get('FACS',[]): pairs.append((doc,)+tuple(p.split()))
seen={(d,frozenset((a,b))) for d,a,b in pairs}
for d,p in pos:
    if (d,p) not in seen:
        a,b=sorted(p); pairs.append((d,a,b))
def run(doc):
    ps=[p for p in pairs if p[0]==doc]; cache={}; out=[]
    def g(f):
        if f not in cache: cache[f]=pm.dots(Image.open('biofors/x/biofors_images/%s/%s'%(doc,f)))
        return cache[f]
    for _,a,b in ps:
        try: r=pm.match_dots(g(a),g(b))
        except Exception as e: r={'score':0,'err':str(e)}
        r.update(doc=doc,a=a,b=b,pos=(doc,frozenset((a,b))) in pos); out.append(r)
    return out
if __name__=='__main__':
    t=time.time(); docs=sorted({p[0] for p in pairs})
    with Pool(4) as P: res=[x for o in P.imap_unordered(run,docs) for x in o]
    json.dump(res,open('biofors/eval.json','w'))
    res.sort(key=lambda r:-r['score']); y=np.array([r['pos'] for r in res])
    tp=np.cumsum(y); prec=tp/np.arange(1,len(y)+1)
    print('pairs',len(res),'pos',y.sum(),'AP %.3f'%(prec[y].mean()),'time %.0fs'%(time.time()-t))
    for k in (25,50,82,150,300): print('top',k,'pos',tp[k-1])
    print('pos scores',sorted(round(r['score'],1) for r in res if r['pos'])[:30])
    print('top neg',[(r['doc'],r['a'],r['b'],round(r['score'],1)) for r in res if not r['pos']][:12])
