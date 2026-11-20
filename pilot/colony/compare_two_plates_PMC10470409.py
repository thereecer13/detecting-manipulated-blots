import cv2,numpy as np,json
from PIL import Image
im=cv2.imread('/tmp/claude-0/-home-user/d3491ae8-cca5-5e56-9093-18710041e4bb/images/2.webp')
S=5;R=80
def crop(x,y): return cv2.resize(im[y-R:y+R,x-R:x+R],None,fx=S,fy=S,interpolation=cv2.INTER_CUBIC)
A=crop(1465,136);B=crop(1465,304)
ga=cv2.cvtColor(A,cv2.COLOR_BGR2GRAY);gb=cv2.cvtColor(B,cv2.COLOR_BGR2GRAY)
sift=cv2.SIFT_create(6000);ka,da=sift.detectAndCompute(ga,None);kb,db=sift.detectAndCompute(gb,None)
m=[p for p,q in cv2.BFMatcher().knnMatch(db,da,k=2) if p.distance<0.75*q.distance]
src=np.float32([kb[x.queryIdx].pt for x in m]);dst=np.float32([ka[x.trainIdx].pt for x in m])
M,inl=cv2.estimateAffinePartial2D(src,dst,ransacReprojThreshold=6)
sc=np.hypot(M[0,0],M[0,1]);rot=np.degrees(np.arctan2(M[1,0],M[0,0]))
print('matches',len(m),'inliers',int(inl.sum()),'scale',round(sc,3),'rot',round(rot,2))
# where are the inlier matches?
ip=dst[inl.ravel()==1];print('inlier x quartiles',np.percentile(ip[:,0],[10,50,90]).round(),'y',np.percentile(ip[:,1],[10,50,90]).round())
W=M.astype(np.float32)
cc,W=cv2.findTransformECC(ga.astype(np.float32),gb.astype(np.float32),cv2.invertAffineTransform(M).astype(np.float32),cv2.MOTION_AFFINE,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,300,1e-6),None,5)
Bw=cv2.warpAffine(B,W,(A.shape[1],A.shape[0]),flags=cv2.INTER_CUBIC|cv2.WARP_INVERSE_MAP,borderValue=(255,255,255));print('ecc',round(cc,3))
h,w=ga.shape;yy,xx=np.mgrid[:h,:w];c=h/2;disk=((xx-c)**2+(yy-c)**2)<(66*S)**2
def sat(I):
    hsv=cv2.cvtColor(I,cv2.COLOR_BGR2HSV).astype(np.float32);s=hsv[...,1];return s-cv2.GaussianBlur(s,(0,0),60)
sa,sb=sat(A),sat(Bw)
def blobs(s):
    m=((s>np.percentile(s[disk],90))&disk).astype(np.uint8);m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
    n,l,st,ce=cv2.connectedComponentsWithStats(m);return m,[(ce[i],st[i,4],l==i) for i in range(1,n) if st[i,4]>120]
ma,ba=blobs(sa);mb,bb=blobs(sb)
k=np.ones((15,15),np.uint8);mad=cv2.dilate(ma,k);mbd=cv2.dilate(mb,k)
oA=[b for b in ba if mbd[b[2]].mean()<0.2];oB=[b for b in bb if mad[b[2]].mean()<0.2]
print('colonies upper',len(ba),'lower',len(bb),'only upper',len(oA),'only lower',len(oB))
gbw=cv2.cvtColor(Bw,cv2.COLOR_BGR2GRAY).astype(np.float32);gaf=ga.astype(np.float32)
for nm,mk in (('whole',disk),('left',disk&(xx<c)),('right',disk&(xx>=c)),('top',disk&(yy<c)),('bottom',disk&(yy>=c))): print(nm,round(float(np.corrcoef(gaf[mk],gbw[mk])[0,1]),3))
oa,ob=A.copy(),Bw.copy()
for (cx,cy),ar,_ in oA:
    r=int(np.sqrt(ar/3.14))+12;cv2.circle(oa,(int(cx),int(cy)),r,(0,0,255),3);cv2.circle(ob,(int(cx),int(cy)),r,(0,0,255),1)
for (cx,cy),ar,_ in oB:
    r=int(np.sqrt(ar/3.14))+12;cv2.circle(ob,(int(cx),int(cy)),r,(0,150,0),3);cv2.circle(oa,(int(cx),int(cy)),r,(0,150,0),1)
gap=np.full((h,20,3),255,np.uint8);m_=np.hstack([oa,gap,ob])
lab=np.full((64,m_.shape[1],3),255,np.uint8)
cv2.putText(lab,'C4-2B row, shS+NPHP4',(200,28),0,0.9,(0,0,0),2,cv2.LINE_AA);cv2.putText(lab,'PC-3 row, shS+NPHP4 (aligned)',(960,28),0,0.9,(0,0,0),2,cv2.LINE_AA)
cv2.putText(lab,'thick red = colony only in the C4-2B plate; thick green = only in the PC-3 plate; thin circles mark the same spot in the other plate',(20,56),0,0.6,(60,60,60),1,cv2.LINE_AA)
cv2.imwrite('/home/user/reviews/PMC10470409_Fig7B_differences.png',np.vstack([lab,m_]))
cv2.imwrite('plain.png',np.hstack([A,gap,Bw]))
fr=[Image.fromarray(cv2.cvtColor(x,cv2.COLOR_BGR2RGB)) for x in (A,Bw)]
fr[0].save('/home/user/reviews/PMC10470409_Fig7B_blink.gif',save_all=True,append_images=[fr[1]],duration=700,loop=0)
d=cv2.absdiff(A,Bw).max(2);d[~disk]=0;cv2.imwrite('diff.png',255-cv2.convertScaleAbs(d,alpha=2.5))
