import sys,numpy as np,cv2
sys.path.insert(0,'/home/user/detecting-manipulated-blots/pilot')
import views
from PIL import Image
def load(p,width=None):
    g=np.asarray(Image.open(p).convert('L'))
    if width and g.shape[1]!=width: g=cv2.resize(g,(width,round(g.shape[0]*width/g.shape[1])),interpolation=cv2.INTER_AREA)
    return g
def find_bands(g,min_area=45,max_frac=0.08):
    """Bands: soft-edged dark blobs inside the membrane, away from the panel border. (x,y,w,h) boxes."""
    m=views.blot_mask_v2(g)
    if m.all(): return []
    inner=cv2.erode(m.astype(np.uint8),np.ones((9,9),np.uint8))>0
    gf=g.astype(np.float32)
    k=max(31,(min(g.shape)//12)|1)
    bg=cv2.medianBlur(g,k if k<=255 else 255).astype(np.float32)
    d=bg-gf
    dark=((d>18)&m).astype(np.uint8)
    dark=cv2.morphologyEx(dark,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    n,lab,st,_=cv2.connectedComponentsWithStats(dark,8)
    gy=np.abs(np.diff(gf,axis=0,prepend=gf[:1]));gx=np.abs(np.diff(gf,axis=1,prepend=gf[:,:1]))
    out=[]
    for i in range(1,n):
        x,y,w,h,a=st[i]
        if a<min_area or a>max_frac*g.size or w<10 or h<4 or h>0.2*g.shape[0]: continue
        if w<1.3*h or w>0.6*g.shape[1]: continue
        comp=lab[y:y+h,x:x+w]==i
        if not inner[y:y+h,x:x+w][comp].all(): continue      # touches the panel border / frame
        if a<0.45*w*h: continue                               # ragged: text or arrows
        depth=float(d[y:y+h,x:x+w][comp].max())
        if depth<40: continue
        # soft edges: steepest step across the blob edge is a fraction of its depth (text, ticks and bars are ~1)
        y0,y1,x0,x1=max(0,y-2),min(g.shape[0],y+h+2),max(0,x-2),min(g.shape[1],x+w+2)
        sharp=max(float(np.percentile(gy[y0:y1,x0:x1],98)),float(np.percentile(gx[y0:y1,x0:x1],98)))/depth
        if sharp>0.55: continue
        out.append((int(x),int(y),int(w),int(h)))
    return out
def patch(g,b,pad=5):
    x,y,w,h=b;H,W=g.shape
    return g[max(0,y-pad):min(H,y+h+pad),max(0,x-pad):min(W,x+w+pad)].astype(np.float32)
def resid(p): return p-cv2.GaussianBlur(p,(0,0),2.0)
VARIANTS={'same':lambda q:q,'hflip':lambda q:q[:,::-1],'vflip':lambda q:q[::-1],'rot180':lambda q:q[::-1,::-1]}
def compare(P,Q,shift=3):
    """Best match of Q (4 orientations) to P. Returns (raw NCC, residual NCC, variant)."""
    best=(-1,-1,None)
    if abs(P.shape[0]-Q.shape[0])>4 or abs(P.shape[1]-Q.shape[1])>6: return best
    for name,f in VARIANTS.items():
        q=np.ascontiguousarray(f(Q))
        h=min(P.shape[0],q.shape[0])-2*shift;w=min(P.shape[1],q.shape[1])-2*shift
        if h<6 or w<10: continue
        t=q[(q.shape[0]-h)//2:(q.shape[0]-h)//2+h,(q.shape[1]-w)//2:(q.shape[1]-w)//2+w]
        if t.std()<2: continue
        r=cv2.matchTemplate(P,t,cv2.TM_CCOEFF_NORMED);_,mx,_,loc=cv2.minMaxLoc(r)
        pr=resid(P);tr=resid(q)[(q.shape[0]-h)//2:(q.shape[0]-h)//2+h,(q.shape[1]-w)//2:(q.shape[1]-w)//2+w]
        win=pr[loc[1]:loc[1]+h,loc[0]:loc[0]+w]
        rr=float(np.corrcoef(win.ravel(),tr.ravel())[0,1]) if win.std()>0 and tr.std()>0 else 0.0
        if rr>best[1]: best=(float(mx),rr,name)
    return best
def compare2(P,Q,shift=3):
    """Aligned pixel difference. Returns (nrmse, variant): RMS of P-Q after best shift and gain/offset fit,
    divided by the patch's contrast range. Copies give ~JPEG noise; look-alike bands give edge residue."""
    best=(9.0,None)
    if abs(P.shape[0]-Q.shape[0])>2 or abs(P.shape[1]-Q.shape[1])>2: return best
    for name,f in VARIANTS.items():
        q=np.ascontiguousarray(f(Q))
        h=min(P.shape[0],q.shape[0])-2*shift;w=min(P.shape[1],q.shape[1])-2*shift
        if h<6 or w<10: continue
        t=q[(q.shape[0]-h)//2:(q.shape[0]-h)//2+h,(q.shape[1]-w)//2:(q.shape[1]-w)//2+w]
        rng=float(np.percentile(t,98)-np.percentile(t,2))
        if rng<30: continue
        r=cv2.matchTemplate(P,t,cv2.TM_SQDIFF);mn,_,loc,_=cv2.minMaxLoc(r)
        win=P[loc[1]:loc[1]+h,loc[0]:loc[0]+w]
        a,b=np.polyfit(t.ravel(),win.ravel(),1)
        if not 0.8<a<1.25: continue
        e=float(np.sqrt(np.mean((a*t+b-win)**2)))/rng
        if e<best[0]: best=(e,name)
    return best
def within_image2(g):
    B=find_bands(g);res=[];P=[patch(g,b) for b in B]
    for i in range(len(B)):
        for j in range(i+1,len(B)):
            e,v=compare2(P[i],P[j])
            if v: res.append((e,v,B[i],B[j]))
    res.sort(key=lambda r:r[0]);return B,res
def within_image(g):
    B=find_bands(g);res=[]
    P=[patch(g,b) for b in B]
    for i in range(len(B)):
        for j in range(i+1,len(B)):
            raw,rr,v=compare(P[i],P[j])
            if v: res.append((rr,raw,v,B[i],B[j]))
    res.sort(key=lambda r:-r[0]);return B,res

def search_copies(g,pad=4):
    """For each band, look for a copy of it (4 orientations) anywhere else in the image.
    Returns list of (nrmse, ncc, variant, band_box, (x,y) of match) sorted by nrmse."""
    B=find_bands(g);gf=g.astype(np.float32);H,W=g.shape;out=[]
    for b in B:
        x,y,w,h=b;y0,y1,x0,x1=max(0,y-pad),min(H,y+h+pad),max(0,x-pad),min(W,x+w+pad)
        P=gf[y0:y1,x0:x1];rng=float(np.percentile(P,98)-np.percentile(P,2))
        if rng<30: continue
        best=None
        for name,f in VARIANTS.items():
            t=np.ascontiguousarray(f(P))
            r=cv2.matchTemplate(gf,t,cv2.TM_CCOEFF_NORMED)
            # mask out the band's own position (same orientation matches itself)
            ph,pw=t.shape
            r[max(0,y0-ph//2):y0+ph//2+1,max(0,x0-pw//2):x0+pw//2+1]=-1
            # a copy sits in another lane: skip matches in the same column (marker ladders, parts of one smear)
            r[:,max(0,x0-int(0.6*pw)):x0+int(0.6*pw)+1]=-1
            _,mx,_,loc=cv2.minMaxLoc(r)
            if mx<0.8: continue
            win=gf[loc[1]:loc[1]+ph,loc[0]:loc[0]+pw]
            a,bb=np.polyfit(t.ravel(),win.ravel(),1)
            if not 0.8<a<1.25: continue
            e=float(np.sqrt(np.mean((a*t+bb-win)**2)))/rng
            if best is None or e<best[0]: best=(e,float(mx),name,b,(int(loc[0]),int(loc[1])))
        if best: out.append(best)
    out.sort(key=lambda r:r[0]);return B,out
