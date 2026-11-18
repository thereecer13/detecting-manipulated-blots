"""Stretch-tolerant outline comparison (reviewer's suggestion, 2026-11-18).

Each band outline is described by four profiles read off its half-depth mask: the top and bottom edge as a
function of position along the band, and the left and right end as a function of height. Positions are
rescaled to 0..1 and distances to the band's own width / height, so stretching the band horizontally or
vertically changes nothing, while a bump, notch or tilt in the outline does.

  shape_feats(A, B) -> dict(shape_diff, bump_corr, ...) for two aligned grey patches (B already turned)
"""
import cv2,numpy as np
import sys;sys.path.insert(0,'band')
from outline import _mask
N=48
def profiles(P,frac=0.5):
    m,_=_mask(P,frac)
    if m is None: return None
    ys,xs=np.nonzero(m);x0,x1,y0,y1=xs.min(),xs.max(),ys.min(),ys.max();w,h=x1-x0+1,y1-y0+1
    if w<12 or h<5: return None
    sub=m[y0:y1+1,x0:x1+1]
    cols=np.nonzero(sub.any(0))[0];top=np.array([np.argmax(sub[:,c]) for c in cols],float);bot=np.array([h-1-np.argmax(sub[::-1,c]) for c in cols],float)
    rows=np.nonzero(sub.any(1))[0];lef=np.array([np.argmax(sub[r]) for r in rows],float);rig=np.array([w-1-np.argmax(sub[r,::-1]) for r in rows],float)
    rs=lambda v,n:np.interp(np.linspace(0,1,n),np.linspace(0,1,len(v)),v)
    # skip the outer 8% at each end of the long edges, where the edge turns the corner
    t=np.linspace(0.08,0.92,N);xi=np.linspace(0,1,len(cols))
    return dict(top=np.interp(t,xi,top)/h,bot=np.interp(t,xi,bot)/h,lef=rs(lef,N//3)/w,rig=rs(rig,N//3)/w,w=w,h=h)
def _bump(v):
    k=np.ones(9)/9;s=np.convolve(np.pad(v,4,mode='edge'),k,mode='valid');return v-s
def shape_feats(A,B):
    out={}
    for fr in(0.35,0.5,0.65):
        pa,pb=profiles(A,fr),profiles(B,fr)
        if pa is None or pb is None: return None
        d=[np.mean(np.abs((pa[k]-pa[k].mean())-(pb[k]-pb[k].mean()))) for k in('top','bot')]
        e=[np.mean(np.abs((pa[k]-pa[k].mean())-(pb[k]-pb[k].mean()))) for k in('lef','rig')]
        ba=np.concatenate([_bump(pa['top']),_bump(pa['bot'])]);bb=np.concatenate([_bump(pb['top']),_bump(pb['bot'])])
        la=np.concatenate([pa['top']-pa['top'].mean(),pa['bot']-pa['bot'].mean()]);lb=np.concatenate([pb['top']-pb['top'].mean(),pb['bot']-pb['bot'].mean()])
        cc=lambda u,v:float(np.corrcoef(u,v)[0,1]) if u.std()>1e-6 and v.std()>1e-6 else 0.0
        out[fr]=dict(edge_diff=float(np.mean(d)),end_diff=float(np.mean(e)),bump_corr=cc(ba,bb),prof_corr=cc(la,lb),bump_amp=float(min(np.abs(ba).mean(),np.abs(bb).mean())),stretch=[pb['w']/pa['w'],pb['h']/pa['h']])
    m=lambda k:float(np.mean([out[f][k] for f in out]))
    return dict(edge_diff=m('edge_diff'),end_diff=m('end_diff'),bump_corr=m('bump_corr'),prof_corr=m('prof_corr'),bump_amp=m('bump_amp'),stretch=out[0.5]['stretch'])
