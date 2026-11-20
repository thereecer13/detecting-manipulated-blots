import cv2,numpy as np,itertools,json
D='/tmp/claude-0/-home-user/d3491ae8-cca5-5e56-9093-18710041e4bb/images/'
plates={}
for f in ('4','5','6'):
    im=cv2.imread(D+f+'.webp');g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY);m=(g<243).astype(np.uint8)
    m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((9,9),np.uint8))
    n,l,st,ce=cv2.connectedComponentsWithStats(m);ids=[i for i in range(1,n) if st[i,4]>100000]
    ids=sorted(ids,key=lambda i:(round(st[i,1]/300),st[i,0]))
    print(f,im.shape,[tuple(st[i,:4]) for i in ids])
    for k,i in enumerate(ids):
        x,y,w,h=st[i,:4];p=im[max(0,y-6):y+h+6,max(0,x-6):x+w+6];nm=f'img{f}_r{k//(len(ids)//2)+1}c{k%(len(ids)//2)+1}';plates[nm]=p;cv2.imwrite(f'others/{nm}.png',p)
plates['NPHP4_upper']=cv2.imread('bigA.png');plates['NPHP4_lower']=cv2.imread('bigB.png')
sift=cv2.SIFT_create(8000,contrastThreshold=0.02);F={}
for k,p in plates.items():
    g=cv2.createCLAHE(2.0,(8,8)).apply(cv2.cvtColor(p,cv2.COLOR_BGR2GRAY));F[k]=(sift.detectAndCompute(g,None),sift.detectAndCompute(cv2.flip(g,1),None))
bf=cv2.BFMatcher()
def match(a,b,flip):
    (ka,da),(kb,db)=F[a][0],F[b][1 if flip else 0]
    m=[p for p,q in bf.knnMatch(da,db,k=2) if p.distance<0.75*q.distance]
    if len(m)<6: return 0,None
    M,inl=cv2.estimateAffinePartial2D(np.float32([ka[x.queryIdx].pt for x in m]),np.float32([kb[x.trainIdx].pt for x in m]),ransacReprojThreshold=4)
    return (int(inl.sum()),M) if M is not None else (0,None)
res=[]
for a,b in itertools.combinations(plates,2):
    for fl in (0,1):
        n,M=match(a,b,fl)
        if n>=8: res.append((n,a,b,fl,round(float(np.hypot(M[0,0],M[1,0])),3),round(float(np.degrees(np.arctan2(M[1,0],M[0,0]))),1)))
for r in sorted(res,reverse=True)[:15]: print(r)
print('pairs tested',len(list(itertools.combinations(plates,2))))
