"""Outline-based band comparison (v2), following the reviewer's criteria: whole bands only, outline
similarity first, fill second, saturated ovals discounted, unusual shapes weighted up."""
import sys,cv2,numpy as np
sys.path.insert(0,'band')
from bandlib import load,VARIANTS
def _mask(P,frac):
    bg=float(np.percentile(P,95));d=bg-P.astype(np.float32);mx=float(np.percentile(d,99.5))
    if mx<25: return None,0
    m=(d>=frac*mx).astype(np.uint8);n,lab,st,cen=cv2.connectedComponentsWithStats(m,8)
    if n<2: return None,0
    # component nearest the patch centre
    cy,cx=P.shape[0]/2,P.shape[1]/2;best=None
    for i in range(1,n):
        if st[i,4]<12: continue
        dd=abs(cen[i][0]-cx)+abs(cen[i][1]-cy)-0.02*st[i,4]
        if best is None or dd<best[0]: best=(dd,i)
    if best is None: return None,0
    c=lab==best[1];x,y,w,h,a=st[best[1]]
    touch=x==0 or y==0 or x+w==P.shape[1] or y+h==P.shape[0]
    return c,touch
def _iou(a,b,s=2):
    best=0
    for dy in range(-s,s+1):
        for dx in range(-s,s+1):
            bb=np.roll(np.roll(b,dy,0),dx,1);u=(a|bb).sum()
            if u: best=max(best,(a&bb).sum()/u)
    return best
def _center(m,shape):
    ys,xs=np.nonzero(m);o=np.zeros(shape,bool);cy,cx=int(round(ys.mean())),int(round(xs.mean()))
    yy=ys-cy+shape[0]//2;xx=xs-cx+shape[1]//2;k=(yy>=0)&(yy<shape[0])&(xx>=0)&(xx<shape[1]);o[yy[k],xx[k]]=True;return o
def features(g,hit,pad=10):
    e,ncc,var,(x,y,w,h),(lx,ly)=hit;H,W=g.shape;p0=4
    ax0,ay0=x-p0,y-p0;bx0,by0=lx,ly;pw,ph=w+2*p0,h+2*p0;ex=pad-p0
    def crop(x0,y0):
        xa,ya,xb,yb=x0-ex,y0-ex,x0+pw+ex,y0+ph+ex
        if xa<0 or ya<0 or xb>W or yb>H: return None
        return g[ya:yb,xa:xb]
    A=crop(ax0,ay0);B=crop(bx0,by0)
    if A is None or B is None: return None
    B=np.ascontiguousarray(VARIANTS[var](B));sh=(A.shape[0]+8,A.shape[1]+8)
    ious=[];touch=False;un=[]
    for f in(0.3,0.5,0.7):
        ma,ta=_mask(A,f);mb,tb=_mask(B,f)
        if ma is None or mb is None: return None
        if f==0.3: touch=bool(ta or tb)
        ca,cb=_center(ma,sh),_center(mb,sh);ious.append(_iou(ca,cb))
        un.append(1-np.mean([_iou(ca,_center(v(ma),sh),1) for k,v in VARIANTS.items() if k!='same']))
    ma,_=_mask(A,0.5);v=A[ma].astype(np.float32);sat=float((v<=v.min()+6).mean()) if v.min()<40 else 0.0
    area_ratio=min(ma.sum(),_mask(B,0.5)[0].sum())/max(ma.sum(),_mask(B,0.5)[0].sum())
    return dict(outline=float(np.mean(ious)),outline_min=float(min(ious)),touch=touch,unusual=float(np.mean(un)),sat=sat,fill=1-e,area_ratio=float(area_ratio))
if __name__=='__main__':
    import json
    key=json.load(open('band/review_key.json'));r={i['id']:i for i in json.load(open('band/review_results.json'))['results']}
    rows=[]
    for k,s in key.items():
        f=features(load(s['path']),s['hit']);rows.append((r[k]['verdict'],s['kind'],k,f))
    for v in('duplicated','unsure','not duplicated'):
        print('==',v)
        for row in sorted([x for x in rows if x[0]==v],key=lambda x:-(x[3] or {}).get('outline',0)):
            f=row[3];print(row[2],row[1],'  '.join(f'{a}={b:.2f}' if isinstance(b,float) else f'{a}={b}' for a,b in f.items()) if f else None)
