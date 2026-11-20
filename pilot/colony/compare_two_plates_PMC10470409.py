import cv2,numpy as np,itertools
im=cv2.imread('/tmp/claude-0/-home-user/d3491ae8-cca5-5e56-9093-18710041e4bb/images/2.webp')
S=5;R=80
def crop(x,y): return cv2.resize(im[y-R:y+R,x-R:x+R],None,fx=S,fy=S,interpolation=cv2.INTER_CUBIC)
A=crop(1465,136);B=crop(1465,304);h,w=A.shape[:2];yy,xx=np.mgrid[:h,:w];c=h/2
def cents(I,rad=68):
    disk=((xx-c)**2+(yy-c)**2)<(rad*S)**2
    hsv=cv2.cvtColor(I,cv2.COLOR_BGR2HSV).astype(np.float32);s=hsv[...,1];s=s-cv2.GaussianBlur(s,(0,0),60)
    m=((s>np.percentile(s[disk],90))&disk).astype(np.uint8);m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
    n,l,st,ce=cv2.connectedComponentsWithStats(m);return np.array([ce[i] for i in range(1,n) if st[i,4]>120]),np.array([st[i,4] for i in range(1,n) if st[i,4]>120])
ca,aa=cents(A);cb,ab=cents(B);print(len(ca),len(cb))
# exhaustive similarity search from centroid pairs (no rotation assumed large): p_A = s*R*p_B + t
best=(0,None)
rng=np.random.default_rng(0)
for i,j in itertools.permutations(range(len(cb)),2):
    vb=cb[j]-cb[i];lb=np.hypot(*vb)
    if lb<150: continue
    for k,l in itertools.permutations(range(len(ca)),2):
        va=ca[l]-ca[k];la=np.hypot(*va);s=la/lb
        if not 0.8<s<1.25: continue
        ang=np.arctan2(va[1],va[0])-np.arctan2(vb[1],vb[0])
        if abs((ang+np.pi)%(2*np.pi)-np.pi)>0.15: continue
        Rm=s*np.array([[np.cos(ang),-np.sin(ang)],[np.sin(ang),np.cos(ang)]]);t=ca[k]-Rm@cb[i]
        P=cb@Rm.T+t;d=np.linalg.norm(P[:,None]-ca[None],axis=2).min(1);n=int((d<10).sum())
        if n>best[0]: best=(n,(Rm,t,s,ang))
n,(Rm,t,s,ang)=best;print('best centroid alignment: matched',n,'scale',round(s,3),'rot deg',round(np.degrees(ang),2),'t',t.round(1))
# refine by least squares on matched pairs
for it in range(5):
    P=cb@Rm.T+t;D=np.linalg.norm(P[:,None]-ca[None],axis=2);j=D.argmin(1);ok=D.min(1)<12
    M,_=cv2.estimateAffinePartial2D(cb[ok].astype(np.float32),ca[j[ok]].astype(np.float32),method=cv2.LMEDS);Rm=M[:,:2];t=M[:,2]
P=cb@Rm.T+t;D=np.linalg.norm(P[:,None]-ca[None],axis=2)
print('refined scale',round(np.hypot(M[0,0],M[1,0]),3),'matched(<12px)',int((D.min(1)<12).sum()),'of lower',len(cb),'| upper matched',int((D.min(0)<12).sum()),'of',len(ca),'median residual',round(float(np.median(D.min(1)[D.min(1)<12])),1))
np.save('M2.npy',M)
Bw=cv2.warpAffine(B,M,(w,h),flags=cv2.INTER_CUBIC,borderValue=(255,255,255))
# field of view of B in A coordinates: B's plate disk warped
mask=np.zeros((h,w),np.uint8);cv2.circle(mask,(int(c),int(c)),68*S,255,-1);mw=cv2.warpAffine(mask,M,(w,h))
cv2.imwrite('Bw2.png',Bw);cv2.imwrite('A2.png',A);cv2.imwrite('mw.png',mw)
ov=np.zeros_like(A);ov[...,2]=255-cv2.cvtColor(A,cv2.COLOR_BGR2GRAY);ov[...,1]=255-cv2.cvtColor(Bw,cv2.COLOR_BGR2GRAY);ov=255-ov
cv2.imwrite('overlay2.png',np.hstack([A,Bw,cv2.addWeighted(A,0.5,Bw,0.5,0)]))

# ---- step 2: recount with the alignment saved above (M2.npy) ----
import cv2,numpy as np
from PIL import Image
im=cv2.imread('/tmp/claude-0/-home-user/d3491ae8-cca5-5e56-9093-18710041e4bb/images/2.webp')
S=5;R=80
def crop(x,y): return cv2.resize(im[y-R:y+R,x-R:x+R],None,fx=S,fy=S,interpolation=cv2.INTER_CUBIC)
A=crop(1465,136);B=crop(1465,304);h,w=A.shape[:2];yy,xx=np.mgrid[:h,:w];c=h/2
M=np.load('M2.npy')
Bw=cv2.warpAffine(B,M,(w,h),flags=cv2.INTER_CUBIC,borderValue=(255,255,255))
dm=np.zeros((h,w),np.uint8);cv2.circle(dm,(int(c),int(c)),66*S,255,-1)
ov=(dm>0)&(cv2.warpAffine(dm,M,(w,h))>0)          # area visible in both
def strength(I):
    hsv=cv2.cvtColor(I,cv2.COLOR_BGR2HSV).astype(np.float32);s=hsv[...,1];return s-cv2.GaussianBlur(s,(0,0),60)
sa,sb=strength(A),strength(Bw)
thr=np.percentile(np.r_[sa[ov],sb[ov]],91)
def blobs(s):
    m=((s>thr)&ov).astype(np.uint8);m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
    n,l,st,ce=cv2.connectedComponentsWithStats(m);return [(ce[i],st[i,4],l==i) for i in range(1,n) if st[i,4]>200]
ba,bb=blobs(sa),blobs(sb)
# a colony counts as missing in the other plate if the other plate's stain strength under it is weak
def missing(bl,other): return [b for b in bl if np.percentile(other[cv2.dilate(b[2].astype(np.uint8),np.ones((13,13),np.uint8))>0],90)<thr*0.55]
oA,oB=missing(ba,sb),missing(bb,sa)
print('overlap colonies: upper',len(ba),'lower',len(bb),'only upper',len(oA),'only lower',len(oB))
print('only upper at',[(int(b[0][0]),int(b[0][1]),int(b[1])) for b in oA]);print('only lower at',[(int(b[0][0]),int(b[0][1]),int(b[1])) for b in oB])
ga=cv2.cvtColor(A,cv2.COLOR_BGR2GRAY).astype(np.float32);gb=cv2.cvtColor(Bw,cv2.COLOR_BGR2GRAY).astype(np.float32)
print('pixel agreement in shared area',round(float(np.corrcoef(ga[ov],gb[ov])[0,1]),3))
oa,ob=A.copy(),Bw.copy()
cnt,_=cv2.findContours(ov.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
for I in (oa,ob): cv2.drawContours(I,cnt,-1,(160,160,160),1)
for (cx,cy),ar,_ in oA:
    r=int(np.sqrt(ar/3.14))+14;cv2.circle(oa,(int(cx),int(cy)),r,(0,0,255),3);cv2.circle(ob,(int(cx),int(cy)),r,(0,0,255),1)
for (cx,cy),ar,_ in oB:
    r=int(np.sqrt(ar/3.14))+14;cv2.circle(ob,(int(cx),int(cy)),r,(0,150,0),3);cv2.circle(oa,(int(cx),int(cy)),r,(0,150,0),1)
gap=np.full((h,20,3),255,np.uint8);m_=np.hstack([oa,gap,ob])
lab=np.full((64,m_.shape[1],3),255,np.uint8)
cv2.putText(lab,'C4-2B row, shS+NPHP4',(200,28),0,0.9,(0,0,0),2,cv2.LINE_AA);cv2.putText(lab,'PC-3 row, shS+NPHP4 (shrunk 11% and shifted to align)',(850,28),0,0.8,(0,0,0),2,cv2.LINE_AA)
cv2.putText(lab,'thick red = colony only in the C4-2B plate; thick green = only in the PC-3 plate; thin circle = same spot in the other plate; grey line = area both show',(20,56),0,0.55,(60,60,60),1,cv2.LINE_AA)
cv2.imwrite('/home/user/reviews/PMC10470409_Fig7B_differences.png',np.vstack([lab,m_]))
fr=[Image.fromarray(cv2.cvtColor(x,cv2.COLOR_BGR2RGB)) for x in (A,Bw)]
fr[0].save('/home/user/reviews/PMC10470409_Fig7B_blink.gif',save_all=True,append_images=[fr[1]],duration=700,loop=0)
