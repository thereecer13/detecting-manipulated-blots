import cv2,numpy as np
A=cv2.imread('bigA.png');B=cv2.imread('bigB.png');M=np.load('Mbig.npy');h,w=A.shape[:2]
Bw=cv2.warpAffine(B,M,(w,h),flags=cv2.INTER_CUBIC,borderValue=(255,255,255))
pm=lambda I:(cv2.cvtColor(I,cv2.COLOR_BGR2GRAY)<245).astype(np.uint8)
ov=(cv2.erode(pm(A),np.ones((31,31),np.uint8))>0)&(cv2.erode(cv2.warpAffine(pm(B),M,(w,h)),np.ones((31,31),np.uint8))>0)
ga=cv2.cvtColor(A,cv2.COLOR_BGR2GRAY).astype(np.float32);gb=cv2.cvtColor(Bw,cv2.COLOR_BGR2GRAY).astype(np.float32)
print('pixel agreement shared area',round(float(np.corrcoef(ga[ov],gb[ov])[0,1]),3))
def strength(I):
    hsv=cv2.cvtColor(I,cv2.COLOR_BGR2HSV).astype(np.float32);s=hsv[...,1];return s-cv2.GaussianBlur(s,(0,0),50)
sa,sb=strength(A),strength(Bw);thr=np.percentile(np.r_[sa[ov],sb[ov]],91)
def blobs(s):
    m=((s>thr)&ov).astype(np.uint8);m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
    n,l,st,ce=cv2.connectedComponentsWithStats(m);return [(ce[i],st[i,4],l==i) for i in range(1,n) if st[i,4]>80]
ba,bb=blobs(sa),blobs(sb)
miss=lambda bl,o:[b for b in bl if np.percentile(o[cv2.dilate(b[2].astype(np.uint8),np.ones((9,9),np.uint8))>0],90)<thr*0.5]
oA,oB=miss(ba,sb),miss(bb,sa)
print('colonies shared area: upper',len(ba),'lower',len(bb),'| only upper',len(oA),'only lower',len(oB))
pa=[(int(b[0][0]),int(b[0][1]),int(b[1])) for b in oA];pb=[(int(b[0][0]),int(b[0][1]),int(b[1])) for b in oB];print('onlyA',pa);print('onlyB',pb)
np.save('onlyA.npy',np.array(pa));np.save('onlyB.npy',np.array(pb))
cv2.imwrite('bigBw.png',Bw)
oa,ob=A.copy(),Bw.copy()
for x,y,ar in pa:
    r=int(np.sqrt(ar/3.14))+12;cv2.circle(oa,(x,y),r,(0,0,255),2);cv2.circle(ob,(x,y),r,(0,0,255),1)
for x,y,ar in pb:
    r=int(np.sqrt(ar/3.14))+12;cv2.circle(ob,(x,y),r,(0,150,0),2);cv2.circle(oa,(x,y),r,(0,150,0),1)
cv2.imwrite('bigmarked.png',np.hstack([oa,np.full((h,12,3),255,np.uint8),ob]))
# difference map (after matching brightness)
d=np.abs(ga-gb-np.median((ga-gb)[ov]));d[~ov]=0;cv2.imwrite('bigdiff.png',255-np.clip(d*4,0,255).astype(np.uint8))
print('residual abs diff in shared area: median',np.median(d[ov]).round(2),'95%',np.percentile(d[ov],95).round(2))
