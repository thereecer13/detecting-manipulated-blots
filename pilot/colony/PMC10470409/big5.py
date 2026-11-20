import cv2,numpy as np
A=cv2.imread('bigA.png');B=cv2.imread('bigB.png');Bw=cv2.imread('bigBw.png');M=np.load('Mbig.npy');Mi=cv2.invertAffineTransform(M);h,w=A.shape[:2]
pa=np.load('onlyA.npy');pb=np.load('onlyB.npy')
toB=lambda x,y:tuple(np.round(Mi[:,:2]@np.array([x,y],float)+Mi[:,2]).astype(int))
g=lambda I:cv2.cvtColor(I,cv2.COLOR_BGR2GRAY).astype(np.float32)
def hp(I): G=g(I);return G-cv2.GaussianBlur(G,(0,0),2.0)
def colmask(I):
    hsv=cv2.cvtColor(I,cv2.COLOR_BGR2HSV).astype(np.float32);s=hsv[...,1];s=s-cv2.GaussianBlur(s,(0,0),50)
    pl=cv2.erode((g(I)<245).astype(np.uint8),np.ones((31,31),np.uint8))>0
    return cv2.dilate(((s>np.percentile(s[pl],88))).astype(np.uint8),np.ones((9,9),np.uint8))>0,pl
def analyse(I,pts,tag):
    H=hp(I);cm,pl=colmask(I);rng=np.random.default_rng(0)
    # null: random clean background patches
    def stats(x,y,r):
        p=H[y-r:y+r+1,x-r:x+r+1];return p.std()
    def clone(x,y,r):
        t=H[y-r:y+r+1,x-r:x+r+1].copy();R=cv2.matchTemplate(H,t,cv2.TM_CCOEFF_NORMED);cv2.circle(R,(x-r,y-r),r,-1,-1)
        _,mx,_,loc=cv2.minMaxLoc(R);return mx,(loc[0]+r,loc[1]+r)
    null_s=[];null_c=[]
    while len(null_s)<150:
        x,y=rng.integers(40,h-40,2);r=14
        if pl[y,x] and not cm[y-r:y+r+1,x-r:x+r+1].any():
            null_s.append(stats(x,y,r))
            if len(null_c)<40: null_c.append(clone(x,y,r)[0])
    print(tag,'background texture std: 5/50/95% =',np.percentile(null_s,[5,50,95]).round(2),'| best repeat score of random background patches: median',np.median(null_c).round(2),'max',np.max(null_c).round(2))
    for x,y,ar in pts:
        r=min(14,int(np.sqrt(ar/3.14)));
        if not (r<x<w-r and r<y<h-r): continue
        mx,loc=clone(x,y,14) if 14<x<w-14 and 14<y<h-14 else (np.nan,None)
        print('   spot',(int(x),int(y)),'colony area on other plate',int(ar),'texture std',stats(x,y,r).round(2),'covered by colony here:',bool(cm[y-3:y+4,x-3:x+4].any()),'best repeat',np.round(mx,2),loc)
print('Empty spots in LOWER plate (native) where upper has a colony');analyse(B,[(*toB(x,y),ar/1.23) for x,y,ar in pa],'lower')
print('Empty spots in UPPER plate where lower has a colony');analyse(A,pb,'upper')
