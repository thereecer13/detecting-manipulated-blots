"""Score verified cross-blot band pairs with the border-detail / unusualness / orientation score.
  python3 cross_score.py XDIR   -> XDIR/scored.json"""
import sys,json,cv2,numpy as np
sys.path.insert(0,'band')
from bandlib import load,VARIANTS
from outline import _mask
import multiprocessing as mp
X=sys.argv[1];M=json.load(open(X+'/bands.json'))['meta']
def crop(g,b,p):
    x,y,w,h=b;H,W=g.shape
    return None if x-p<0 or y-p<0 or x+w+p>W or y+h+p>H else g[y-p:y+h+p,x-p:x+w+p].astype(np.float32)
def border(ga,gb,ba,bb,var,width=2):
    if abs(ba[2]-bb[2])>2 or abs(ba[3]-bb[3])>2:
        fx,fy=ba[2]/bb[2],ba[3]/bb[3];gb=cv2.resize(gb,None,fx=fx,fy=fy,interpolation=cv2.INTER_AREA if fx<1 else cv2.INTER_LINEAR);bb=[round(bb[0]*fx),round(bb[1]*fy),ba[2],ba[3]]
    P=crop(ga,ba,14);Q=crop(gb,bb,10)
    if P is None or Q is None: return None
    B=np.ascontiguousarray(VARIANTS[var](Q))
    if B.shape[0]>P.shape[0] or B.shape[1]>P.shape[1]: return None
    _,_,_,loc=cv2.minMaxLoc(cv2.matchTemplate(P,B,cv2.TM_CCOEFF_NORMED));A=P[loc[1]:loc[1]+B.shape[0],loc[0]:loc[0]+B.shape[1]]
    ma,_=_mask(A,0.5);mb,_=_mask(B,0.5)
    if ma is None or mb is None: return None
    k=np.ones((3,3),np.uint8);m=(ma|mb).astype(np.uint8);mi=(ma&mb).astype(np.uint8)
    ring=(cv2.dilate(m,k,iterations=width)>0)&~(cv2.erode(mi,k,iterations=width)>0)
    if ring.sum()<40: return None
    hp=lambda Z:Z-cv2.GaussianBlur(Z,(0,0),1.5);u,v=hp(A)[ring],hp(B)[ring]
    return float(np.corrcoef(u,v)[0,1]) if u.std()>0 and v.std()>0 else 0.0
def f(job):
    a,b,sim,var,r=job
    try: d=border(load(M[a]['path']),load(M[b]['path']),M[a]['box'],M[b]['box'],var)
    except Exception: d=None
    return [a,b,var,r['nrmse'],r['outline'],r['ctx'],r['scaled'],d]
if __name__=='__main__':
    V=[v for v in json.load(open(X+'/verified.json')) if v[4]['nrmse']<=0.05 and v[4]['outline']>=0.92 and M[v[0]]['name']!=M[v[1]]['name']]
    with mp.Pool(3) as P: out=P.map(f,V,chunksize=32)
    json.dump(out,open(X+'/scored.json','w'));print(len(out),'pairs;',sum(o[7] is not None for o in out),'with a border score')
