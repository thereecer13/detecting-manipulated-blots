import cv2,numpy as np,glob,json
from multiprocessing import Pool
A=cv2.imread('bigA.png');B=cv2.imread('bigB.png');Bw=cv2.imread('bigBw.png');M=np.load('Mbig.npy');Mi=cv2.invertAffineTransform(M)
pa=np.load('onlyA.npy');pb=np.load('onlyB.npy')
g=lambda I:cv2.cvtColor(I,cv2.COLOR_BGR2GRAY)
toB=lambda x,y:tuple(np.round(Mi[:,:2]@np.array([x,y],float)+Mi[:,2]).astype(int))
T=[]   # (label, kind, gray patch)
gA,gB=g(A),g(B)
def patch(G,x,y,ar):
    r=int(np.sqrt(ar/3.14))+6;p=G[y-r:y+r+1,x-r:x+r+1];return p if p.shape==(2*r+1,2*r+1) else None
for x,y,ar in pa:
    p=patch(gA,x,y,ar)
    if p is not None: T.append((f'upper-only ({x},{y})','one',p,int(ar)))
for x,y,ar in pb:
    bx,by=toB(x,y);p=patch(gB,bx,by,ar/1.23)
    if p is not None: T.append((f'lower-only ({x},{y})','one',p,int(ar)))
# controls: colonies present in both plates
def strength(I):
    hsv=cv2.cvtColor(I,cv2.COLOR_BGR2HSV).astype(np.float32);s=hsv[...,1];return s-cv2.GaussianBlur(s,(0,0),50)
pl=cv2.erode((gA<245).astype(np.uint8),np.ones((41,41),np.uint8))>0;s=strength(A)
m=((s>np.percentile(s[pl],91))&pl).astype(np.uint8);m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
n,l,st,ce=cv2.connectedComponentsWithStats(m);one={(int(x),int(y)) for x,y,_ in pa}
rng=np.random.default_rng(0);ids=[i for i in range(1,n) if st[i,4]>100 and (int(ce[i][0]),int(ce[i][1])) not in one]
for i in rng.permutation(ids)[:26]:
    p=patch(gA,int(ce[i][0]),int(ce[i][1]),st[i,4])
    if p is not None: T.append((f'shared ({int(ce[i][0])},{int(ce[i][1])})','ctl',p,int(st[i,4])))
P={f.split('/')[-1][:-4]:g(cv2.imread(f)) for f in sorted(glob.glob('others/*.png'))}
scales=np.arange(0.65,1.31,0.05);rots=range(0,360,30)
def run(k):
    lab,kind,p,ar=T[k];best=(-1,)
    for sc in scales:
        q=cv2.resize(p,None,fx=sc,fy=sc,interpolation=cv2.INTER_AREA if sc<1 else cv2.INTER_CUBIC);hh=q.shape[0];c=hh/2
        yy,xx=np.mgrid[:hh,:hh];mask=(((xx-c)**2+(yy-c)**2)<(c-1)**2).astype(np.uint8)*255
        for fl in (0,1):
            q2=cv2.flip(q,1) if fl else q
            for ro in rots:
                t=cv2.warpAffine(q2,cv2.getRotationMatrix2D((c,c),ro,1),(hh,hh),borderMode=cv2.BORDER_REFLECT)
                for nm,G in P.items():
                    R=cv2.matchTemplate(G,t,cv2.TM_CCORR_NORMED if False else cv2.TM_CCOEFF_NORMED,mask=mask);R[~np.isfinite(R)]=-1
                    _,mx,_,loc=cv2.minMaxLoc(R)
                    if mx>best[0]: best=(float(mx),nm,[int(loc[0]+c),int(loc[1]+c)],round(float(sc),2),ro,fl)
    return lab,kind,ar,best
if __name__=='__main__':
    with Pool(4) as po: out=po.map(run,range(len(T)))
    json.dump(out,open('oth2.json','w'))
    ctl=np.array([o[3][0] for o in out if o[1]=='ctl']);print('controls (colonies known to be in both plates): n',len(ctl),'best scores median',np.median(ctl).round(3),'max',ctl.max().round(3))
    for o in sorted([o for o in out if o[1]=='one'],key=lambda o:-o[3][0]): print(o[0],'area',o[2],'best',round(o[3][0],3),o[3][1:])
