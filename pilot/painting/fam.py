import json,re,collections,sys,cv2,numpy as np,multiprocessing as mp
sys.path.insert(0,'/home/user/detecting-manipulated-blots/pilot/painting')
from feat_v3 import features
def stamp(b):
    m=re.search(r'(20\d{6})[\d_]*\.jpg$',b) or re.search(r'-(20\d{5,6})\d{6}\.jpg$',b)
    return m.group(1) if m else 'none'
FAM=['20200207','20201021','20210721','20220201','20230104']
def fam(d):
    s=stamp(d[0])
    if s in FAM: return s
    if s=='none' and re.match(r'MA5-3[2-4]',d[2]): return 'none_MA5-32-34'
def f(t):
    lab,d=t
    try:
        g=cv2.imread(d[1],0);x=features(g)
    except Exception: x=None;g=None
    return [lab,fam(d),d[0],d[1],d[2],d[3],list(g.shape) if g is not None else None,x]
if __name__=='__main__':
    N=json.load(open('paint/allneg_f2.json'));P=json.load(open('paint/allpos_f2.json'))
    J=[('neg',d) for d in N if fam(d)]+[('pos',d) for d in P if fam(d)];print(len(J),collections.Counter((l,fam(d)) for l,d in J))
    with mp.Pool(3) as p: out=p.map(f,J,chunksize=16)
    json.dump(out,open('paint/fam_feats.json','w'))
