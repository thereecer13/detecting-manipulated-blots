"""Border similarity of a band and its match: how alike the two bands are in the edge zone only,
where the shape lives, ignoring the filled interior (reviewer's suggestion, 2026-11-18)."""
import sys,cv2,numpy as np
sys.path.insert(0,'band')
from bandlib import VARIANTS
from outline import _mask
def crops(g,hit,pad=10):
    e,ncc,var,(x,y,w,h),(lx,ly)=hit;H,W=g.shape;p0=4;ex=pad-p0;pw,ph=w+2*p0,h+2*p0
    def c(x0,y0):
        xa,ya,xb,yb=x0-ex,y0-ex,x0+pw+ex,y0+ph+ex
        return None if xa<0 or ya<0 or xb>W or yb>H else g[ya:yb,xa:xb].astype(np.float32)
    A=c(x-p0,y-p0);B=c(lx,ly)
    if A is None or B is None: return None,None
    return A,np.ascontiguousarray(VARIANTS[var](B))
def border_feats(g,hit,width=2):
    A,B=crops(g,hit)
    if A is None: return None
    ma,_=_mask(A,0.5);mb,_=_mask(B,0.5)
    if ma is None or mb is None: return None
    k=np.ones((3,3),np.uint8);m=(ma|mb).astype(np.uint8);mi=(ma&mb).astype(np.uint8)
    ring=(cv2.dilate(m,k,iterations=width)>0)&~(cv2.erode(mi,k,iterations=width)>0)
    inner=cv2.erode(mi,k,iterations=width)>0
    if ring.sum()<40: return None
    a,b=np.polyfit(B[ring|inner],A[ring|inner],1);Bf=a*B+b
    rng=float(np.percentile(A,98)-np.percentile(A,2))+1e-6
    d=A-Bf
    hp=lambda P:P-cv2.GaussianBlur(P,(0,0),1.5)
    ha,hb=hp(A),hp(B)
    cc=lambda u,v:float(np.corrcoef(u,v)[0,1]) if u.std()>0 and v.std()>0 else 0.0
    return dict(border_sim=1-float(np.sqrt(np.mean(d[ring]**2)))/rng,inner_sim=(1-float(np.sqrt(np.mean(d[inner]**2)))/rng) if inner.sum()>10 else None,
                border_corr=cc(A[ring],B[ring]),border_detail=cc(ha[ring],hb[ring]),ring=int(ring.sum()))
