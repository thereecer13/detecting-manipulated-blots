import cv2,numpy as np
A=cv2.imread('bigA.png');Bw=cv2.imread('bigBw.png');M=np.load('Mbig.npy');h,w=A.shape[:2]
pm=lambda I:(cv2.cvtColor(I,cv2.COLOR_BGR2GRAY)<245).astype(np.uint8)
ov=(cv2.erode(pm(A),np.ones((31,31),np.uint8))>0)&(cv2.erode(pm(Bw),np.ones((31,31),np.uint8))>0)
def strength(I):
    hsv=cv2.cvtColor(I,cv2.COLOR_BGR2HSV).astype(np.float32);s=hsv[...,1];return s-cv2.GaussianBlur(s,(0,0),50)
sa,sb=strength(A),strength(Bw);thr=np.percentile(np.r_[sa[ov],sb[ov]],91)
def blobs(s):
    m=((s>thr)&ov).astype(np.uint8);m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
    n,l,st,ce=cv2.connectedComponentsWithStats(m);return [(int(ce[i][0]),int(ce[i][1]),int(st[i,4])) for i in range(1,n) if st[i,4]>80]
ba=blobs(sa);oa={tuple(x[:2]) for x in np.load('onlyA.npy').tolist()}
def best(src,dst,x,y,ar,excl):
    r=int(np.sqrt(ar/3.14))+7;t=src[y-r:y+r+1,x-r:x+r+1]
    if t.shape[:2]!=(2*r+1,2*r+1): return None
    R=cv2.matchTemplate(dst,t,cv2.TM_CCOEFF_NORMED)
    for ex,ey in excl: cv2.circle(R,(ex-r,ey-r),r+4,-1,-1)
    _,mx,_,loc=cv2.minMaxLoc(R);return mx,(loc[0]+r,loc[1]+r)
own=[];other=[]
for x,y,ar in ba:
    if (x,y) in oa: continue
    a=best(A,Bw,x,y,ar,[]);b=best(A,Bw,x,y,ar,[(x,y)])
    if a: own.append((ar,a[0]));other.append((ar,b[0]))
own=np.array(own);other=np.array(other)
for nm,sel in (('small (<500)',own[:,0]<500),('large (>=500)',own[:,0]>=500)):
    print(nm,'n',sel.sum(),'| shared colony vs its own copy: median',np.median(own[sel,1]).round(3),'5%',np.percentile(own[sel,1],5).round(3),'| vs best OTHER colony: median',np.median(other[sel,1]).round(3),'95%',np.percentile(other[sel,1],95).round(3),'max',other[sel,1].max().round(3))
