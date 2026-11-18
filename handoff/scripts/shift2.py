import sys, numpy as np, cv2
from PIL import Image
def strip(g):
    m=((g>60)&(g<225)).mean(0); xs=np.where(m>0.85)[0]
    gr=np.split(xs,np.where(np.diff(xs)>1)[0]+1); q=max(gr,key=len)
    a,b=q.min(),q.max(); col=((g[:,a:b+1]>60)&(g[:,a:b+1]<225)).mean(1); ys=np.where(col>0.9)[0]
    return g[ys.min()+4:ys.max()-3,a+3:b-2]
def lane(p):
    g=np.asarray(Image.open(p).convert('L')).astype(np.float32)
    try: return lane0(p)
    except Exception: return cv2.resize(strip(g),(90,600),interpolation=cv2.INTER_AREA)
def lane0(p):
    g=np.asarray(Image.open(p).convert('L')).astype(np.float32); H,W=g.shape
    xs=np.where((g<70).mean(0)>0.6)[0]; gr=np.split(xs,np.where(np.diff(xs)>2)[0]+1); cs=[(q.min(),q.max()) for q in gr]
    _,a1,b0=max((b0-a1,a1,b0) for (a0,a1),(b0,b1) in zip(cs,cs[1:]))
    fy=(g[:,a1+3:b0-3]<70).mean(1); ys=np.where(fy>0.8)[0]
    return cv2.resize(g[ys.min()+6:ys.max()-5,a1+6:b0-5],(90,600),interpolation=cv2.INTER_AREA)
def res(c):
    r=c-cv2.GaussianBlur(c,(0,0),6); band=cv2.dilate((c<cv2.GaussianBlur(c,(0,0),8)-25).astype(np.uint8),np.ones((21,21),np.uint8))>0
    r=r-r.mean(0,keepdims=True)-r.mean(1,keepdims=True); return r,~band
(ra,ma),(rb,mb)=res(lane(sys.argv[1])),res(lane(sys.argv[2]))
def corr(dx,dy):
    s=lambda d,n:slice(max(0,d),n+min(0,d)); t=lambda d,n:slice(max(0,-d),n+min(0,-d))
    M=ma[s(dy,600),s(dx,90)]&mb[t(dy,600),t(dx,90)]
    return np.corrcoef(ra[s(dy,600),s(dx,90)][M],rb[t(dy,600),t(dx,90)][M])[0,1]
G=np.array([[corr(dx,dy) for dx in range(-12,13)] for dy in range(-12,13)])
i=np.unravel_index(G.argmax(),G.shape); print(sys.argv[1].split('/')[-1],'vs',sys.argv[2].split('/')[-1],'peak',round(G.max(),3),'at',i[0]-12,i[1]-12,'off-peak median',round(np.median(G),3),'p99',round(np.percentile(G,99),3))
