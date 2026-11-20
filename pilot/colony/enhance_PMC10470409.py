import cv2,numpy as np
im=cv2.imread('/tmp/claude-0/-home-user/d3491ae8-cca5-5e56-9093-18710041e4bb/images/2.webp')
S=5;R=80
nat=lambda x,y: im[y-R:y+R,x-R:x+R]
An,Bn=nat(1465,136),nat(1465,304)
M=np.load('M2.npy')            # B(5x) -> A(5x)
up=lambda I,i=cv2.INTER_CUBIC: cv2.resize(I,None,fx=S,fy=S,interpolation=i)
h=w=R*2*S
def stretch(I,lo=2,hi=98):
    # background-only stretch: median-filter away colonies, expand what is left
    g=cv2.cvtColor(I,cv2.COLOR_BGR2GRAY).astype(np.float32)
    a,b=np.percentile(g[40:120,40:120],[lo,hi]);return np.clip((g-a)/(b-a)*255,0,255).astype(np.uint8)
def bg_stretch(I):
    g=cv2.cvtColor(I,cv2.COLOR_BGR2GRAY).astype(np.float32);med=np.median(g[30:130,30:130])
    return np.clip((g-med)*12+128,0,255).astype(np.uint8)   # 12x gain around background level
def noise(I):
    g=cv2.cvtColor(I,cv2.COLOR_BGR2GRAY).astype(np.float32);hp=g-cv2.GaussianBlur(g,(0,0),1.2)
    v=np.sqrt(cv2.GaussianBlur(hp*hp,(0,0),3));return np.clip(v/2.5*255,0,255).astype(np.uint8)
def ela(I,q=90):
    ok,enc=cv2.imencode('.jpg',I,[cv2.IMWRITE_JPEG_QUALITY,q]);d=cv2.absdiff(I,cv2.imdecode(enc,1)).max(2).astype(np.float32)
    return np.clip(cv2.GaussianBlur(d,(0,0),1.5)*40,0,255).astype(np.uint8)
rows=[]
for nm,f in (('background stretched 12x',bg_stretch),('fine-grain noise level',noise),('recompression error',ela)):
    a=up(cv2.cvtColor(f(An),cv2.COLOR_GRAY2BGR),cv2.INTER_NEAREST);b=cv2.warpAffine(up(cv2.cvtColor(f(Bn),cv2.COLOR_GRAY2BGR),cv2.INTER_NEAREST),M,(w,h),flags=cv2.INTER_NEAREST,borderValue=(255,255,255))
    rows.append((nm,a,b))
onlyA=[(715,324),(209,459),(126,568),(261,686)];onlyB=[(283,206),(244,359),(640,402),(242,557),(258,593)]
out=[]
for nm,a,b in rows:
    for I in (a,b):
        for x,y in onlyA: cv2.circle(I,(x,y),34,(0,0,255),2)
        for x,y in onlyB: cv2.circle(I,(x,y),34,(0,170,0),2)
    r=np.hstack([a,np.full((h,12,3),255,np.uint8),b]);r=cv2.copyMakeBorder(r,34,0,0,0,cv2.BORDER_CONSTANT,value=(255,255,255))
    cv2.putText(r,nm+'   (left: C4-2B plate, right: PC-3 plate aligned; red = colony only in C4-2B, green = only in PC-3)',(8,24),0,0.6,(0,0,0),1,cv2.LINE_AA);out.append(r)
cv2.imwrite('enh.png',np.vstack(out))
for i,r in enumerate(out): cv2.imwrite(f'enh{i}.jpg',cv2.resize(r,None,fx=0.75,fy=0.75,interpolation=cv2.INTER_AREA))
# numbers: background smoothness at the "empty" spot vs random empty background spots
def spotstats(I_empty_native,pts,scale):
    g=cv2.cvtColor(I_empty_native,cv2.COLOR_BGR2GRAY).astype(np.float32);hp=g-cv2.GaussianBlur(g,(0,0),1.2);v=[]
    for x,y in pts:
        x,y=int(x/scale),int(y/scale);v.append(float(hp[y-5:y+6,x-5:x+6].std()))
    return np.round(v,2)
Mi=cv2.invertAffineTransform(M)
toB=lambda pts:[tuple((Mi[:,:2]@np.array(p,float)+Mi[:,2])) for p in pts]
gA=cv2.cvtColor(An,cv2.COLOR_BGR2GRAY).astype(np.float32);gB=cv2.cvtColor(Bn,cv2.COLOR_BGR2GRAY).astype(np.float32)
def bgref(g):
    hp=g-cv2.GaussianBlur(g,(0,0),1.2);col=cv2.dilate((g<np.percentile(g[30:130,30:130],12)).astype(np.uint8),np.ones((7,7),np.uint8))
    yy,xx=np.mgrid[:160,:160];dk=((xx-80)**2+(yy-80)**2)<60**2;v=[]
    rng=np.random.default_rng(1)
    while len(v)<400:
        x,y=rng.integers(15,145,2)
        if dk[y,x] and col[y-5:y+6,x-5:x+6].sum()==0: v.append(hp[y-5:y+6,x-5:x+6].std())
    return np.percentile(v,[5,50,95]).round(2)
print('noise at empty spots in PC-3 plate where C4-2B has a colony:',spotstats(Bn,toB(onlyA),S),' PC-3 background 5/50/95%:',bgref(gB))
print('noise at empty spots in C4-2B plate where PC-3 has a colony:',spotstats(An,onlyB,S),' C4-2B background 5/50/95%:',bgref(gA))
