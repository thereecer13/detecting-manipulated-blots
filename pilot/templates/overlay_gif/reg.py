import numpy as np,cv2
from PIL import Image
def load(p): return np.asarray(Image.open(p).convert('L')).astype(np.float32)
def framebox(g,thr=110,frac=0.55):
    d=(g<thr)
    cols=np.where(d.mean(0)>frac)[0]
    if len(cols)<2: return None
    l,r=cols.min(),cols.max()
    rows=np.where(d[:,l:r+1].mean(1)>frac)[0]
    t,b=(rows.min(),rows.max()) if len(rows)>=2 else (0,g.shape[0]-1)
    return int(l),int(r),int(t),int(b)
def hp(g): 
    h=g-cv2.GaussianBlur(g,(0,0),3);return cv2.GaussianBlur(h,(0,0),0.8)
def refmask(R,box,pad=6):
    l,r,t,b=box;m=np.zeros(R.shape,np.uint8);m[t+pad:b-pad,l+pad:r-pad]=1
    dark=(R<np.median(R[t+pad:b-pad,l+pad:r-pad])-25).astype(np.uint8)
    m[cv2.dilate(dark,np.ones((15,9),np.uint8))>0]=0
    return m
def register(R,C,mask,init_scale=None):
    bR=framebox(R);bC=framebox(C)
    s=(bR[1]-bR[0])/(bC[1]-bC[0]) if init_scale is None else init_scale
    A=np.array([[s,0,bR[0]-s*bC[0]],[0,s,bR[2]-s*bC[2]]],np.float32)
    hR=hp(R);hC=hp(C)
    crit=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,300,1e-6)
    W=A.copy()
    # ECC estimates warp from template(R) to input(C); invert our init
    Winv=cv2.invertAffineTransform(A)
    try:
        cc,Winv=cv2.findTransformECC(hR,hC,Winv.astype(np.float32),cv2.MOTION_AFFINE,crit,mask,5)
    except cv2.error as e:
        cc=None
    out=cv2.warpAffine(C,Winv,(R.shape[1],R.shape[0]),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderValue=255)
    return out,cc,Winv
def texcorr(R,O,mask,flip=False):
    a=hp(R);b=hp(O)
    if flip: b=b[::-1].copy()
    m=mask>0
    return float(np.corrcoef(a[m],b[m])[0,1])

def register2(R,C,mask,scales=(1.0,),shift=8,step=0.5):
    """Resize C to R's size (times scale about the centre), then search sub-pixel shift maximizing masked hp correlation."""
    hR=hp(R);m=mask>0;best=(-2,None)
    H,W=R.shape
    for s in scales:
        base=cv2.resize(C,(W,H),interpolation=cv2.INTER_AREA)
        for dy in np.arange(-shift,shift+1e-6,step):
            for dx in np.arange(-shift,shift+1e-6,step):
                A=np.array([[s,0,(1-s)*W/2+dx],[0,s,(1-s)*H/2+dy]],np.float32)
                O=cv2.warpAffine(base,A,(W,H),flags=cv2.INTER_LINEAR,borderValue=255)
                r=np.corrcoef(hR[m],hp(O)[m])[0,1]
                if r>best[0]: best=(r,(s,dx,dy),O)
    return best

def register3(R,C,mask,box,scales):
    """Find scale+translation mapping C into R: masked template match of R's lane (hp) inside scaled hp(C)."""
    l,r,t,b=box;pad=6
    T=hp(R)[t+pad:b-pad,l+pad:r-pad].astype(np.float32);Tm=mask[t+pad:b-pad,l+pad:r-pad].astype(np.float32)
    best=(-2,None)
    for s in scales:
        Cs=cv2.resize(C,(round(C.shape[1]*s),round(C.shape[0]*s)),interpolation=cv2.INTER_AREA)
        if Cs.shape[0]<T.shape[0] or Cs.shape[1]<T.shape[1]:
            Cs=cv2.copyMakeBorder(Cs,0,max(0,T.shape[0]-Cs.shape[0]+4),0,max(0,T.shape[1]-Cs.shape[1]+4),cv2.BORDER_CONSTANT,value=255)
        res=cv2.matchTemplate(hp(Cs).astype(np.float32),T,cv2.TM_CCOEFF_NORMED,mask=Tm)
        res[~np.isfinite(res)]=-2
        _,mx,_,loc=cv2.minMaxLoc(res)
        if mx>best[0]: best=(mx,(s,loc))
    mx,(s,(x,y))=best
    # mapping: point p in Cs at (x+ (l+pad) - (l+pad) ... ) -> C pixel q maps to R pixel q*s - (x,y) + (l+pad,t+pad)
    A=np.array([[s,0,(l+pad)-x],[0,s,(t+pad)-y]],np.float32)
    O=cv2.warpAffine(C,A,(R.shape[1],R.shape[0]),flags=cv2.INTER_AREA,borderValue=255)
    return mx,A,O

def hp(g):
    h=g-cv2.GaussianBlur(g,(0,0),3);h=cv2.GaussianBlur(h,(0,0),0.8)
    h=h-cv2.blur(h,(1,41));h=h-cv2.blur(h,(41,1))
    return h
