import cv2,numpy as np,itertools
im=cv2.imread('/tmp/claude-0/-home-user/d3491ae8-cca5-5e56-9093-18710041e4bb/images/3.webp');print(im.shape)
g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY);nonw=(g<245).astype(np.uint8)
n,l,st,ce=cv2.connectedComponentsWithStats(nonw);big=sorted(range(1,n),key=lambda i:-st[i,4])[:2];big=sorted(big,key=lambda i:st[i,1])
boxes=[st[i,:4] for i in big];print(boxes)
P=[]
for x,y,w,h in boxes:
    s=max(w,h)+20;cx,cy=x+w//2,y+h//2;P.append(im[max(0,cy-s//2):cy+s//2,max(0,cx-s//2):cx+s//2])
s=min(min(p.shape[:2]) for p in P);P=[p[:s,:s] for p in P]
A,B=P;cv2.imwrite('bigA.png',A);cv2.imwrite('bigB.png',B);h,w=A.shape[:2];print(A.shape,B.shape)
yy,xx=np.mgrid[:h,:w]
def pm(I): return (cv2.cvtColor(I,cv2.COLOR_BGR2GRAY)<245)
def cents(I):
    m0=cv2.erode(pm(I).astype(np.uint8),np.ones((25,25),np.uint8))>0
    hsv=cv2.cvtColor(I,cv2.COLOR_BGR2HSV).astype(np.float32);s_=hsv[...,1];s_=s_-cv2.GaussianBlur(s_,(0,0),50)
    m=((s_>np.percentile(s_[m0],91))&m0).astype(np.uint8);m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
    n,l,st,ce=cv2.connectedComponentsWithStats(m);k=[i for i in range(1,n) if st[i,4]>60];return np.array([ce[i] for i in k])
ca,cb=cents(A),cents(B);print(len(ca),len(cb))
best=(0,None)
ib=np.argsort(-np.linalg.norm(cb-cb.mean(0),axis=1))
for i,j in itertools.permutations(range(len(cb)),2):
    vb=cb[j]-cb[i];lb=np.hypot(*vb)
    if lb<200: continue
    for k,l_ in itertools.permutations(range(len(ca)),2):
        va=ca[l_]-ca[k];la=np.hypot(*va);sc=la/lb
        if not 1.0<sc<1.25: continue
        ang=np.arctan2(va[1],va[0])-np.arctan2(vb[1],vb[0]);ang=(ang+np.pi)%(2*np.pi)-np.pi
        if abs(ang)>0.08: continue
        Rm=sc*np.array([[np.cos(ang),-np.sin(ang)],[np.sin(ang),np.cos(ang)]]);t=ca[k]-Rm@cb[i]
        d=np.linalg.norm((cb@Rm.T+t)[:,None]-ca[None],axis=2).min(1);nn=int((d<8).sum())
        if nn>best[0]: best=(nn,(Rm,t))
nn,(Rm,t)=best
for it in range(6):
    Pp=cb@Rm.T+t;D=np.linalg.norm(Pp[:,None]-ca[None],axis=2);j=D.argmin(1);ok=D.min(1)<8
    M,_=cv2.estimateAffine2D(cb[ok].astype(np.float32),ca[j[ok]].astype(np.float32),method=cv2.LMEDS);Rm=M[:,:2];t=M[:,2]
Pp=cb@Rm.T+t;D=np.linalg.norm(Pp[:,None]-ca[None],axis=2);ok=D.min(1)<8
res=Pp[ok]-ca[D.argmin(1)[ok]]
print('matched',int(ok.sum()),'M',M.round(4).tolist(),'sx,sy',round(np.hypot(M[0,0],M[1,0]),4),round(np.hypot(M[0,1],M[1,1]),4))
print('residual px: median',np.median(np.linalg.norm(res,axis=1)).round(2),'90%',np.percentile(np.linalg.norm(res,axis=1),90).round(2))
np.save('Mbig.npy',M);np.save('res.npy',np.c_[ca[D.argmin(1)[ok]],res])
