import cv2,numpy as np
A=cv2.imread('bigA.png');Bw=cv2.imread('bigBw.png');h,w=A.shape[:2]
pa=np.load('onlyA.npy');pb=np.load('onlyB.npy')
g=lambda I:cv2.cvtColor(I,cv2.COLOR_BGR2GRAY).astype(np.float32)
ga,gb=g(A),g(Bw)
def colmask(I):
    hsv=cv2.cvtColor(I,cv2.COLOR_BGR2HSV).astype(np.float32);s=hsv[...,1];s=s-cv2.GaussianBlur(s,(0,0),50)
    pl=cv2.erode((g(I)<245).astype(np.uint8),np.ones((41,41),np.uint8))>0
    return cv2.dilate((s>np.percentile(s[pl],85)).astype(np.uint8),np.ones((13,13),np.uint8))>0,pl
ca,pla=colmask(A);cb,plb=colmask(Bw);bg=pla&plb&~ca&~cb
print('clean background pixels',int(bg.sum()))
for s1,s2 in ((0,1.5),(1,3),(2,6),(4,12)):
    f=lambda G:(cv2.GaussianBlur(G,(0,0),s1) if s1 else G)-cv2.GaussianBlur(G,(0,0),s2)
    print(f'background detail at scale {s1}-{s2}px: correlation between plates',round(float(np.corrcoef(f(ga)[bg],f(gb)[bg])[0,1]),3))
# enhanced crops at each differing spot
def enh(I):
    G=g(I);m=np.median(G[bg]);return np.clip((G-m)*7+140,0,255).astype(np.uint8)
ea,eb=enh(A),enh(Bw);tiles=[]
for tag,pts,col in (('U',pa,(0,0,255)),('L',pb,(0,150,0))):
    for x,y,ar in pts:
        r=42;x0,y0=max(0,x-r),max(0,y-r)
        row=[]
        for I in (A,Bw):
            c=cv2.resize(I[y0:y0+2*r,x0:x0+2*r],(252,252),interpolation=cv2.INTER_CUBIC);row.append(c)
        for E in (ea,eb):
            c=cv2.cvtColor(cv2.resize(E[y0:y0+2*r,x0:x0+2*r],(252,252),interpolation=cv2.INTER_CUBIC),cv2.COLOR_GRAY2BGR);row.append(c)
        t=np.hstack(row);t=cv2.copyMakeBorder(t,20,4,0,6,cv2.BORDER_CONSTANT,value=(255,255,255))
        cv2.putText(t,f"{'only in upper' if tag=='U' else 'only in lower'} at ({x},{y}): upper | lower | upper enhanced | lower enhanced",(4,14),0,0.45,col,1,cv2.LINE_AA);tiles.append(t)
for i in range(0,len(tiles),8):
    ch=tiles[i:i+8];
    while len(ch)%2: ch.append(np.full_like(ch[0],255))
    cv2.imwrite(f'spots{i//8}.png',np.vstack([np.hstack(ch[j:j+2]) for j in range(0,len(ch),2)]))
print(len(tiles))
