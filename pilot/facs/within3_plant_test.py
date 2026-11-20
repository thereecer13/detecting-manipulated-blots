import json,glob,random,sys,io,numpy as np
sys.path.insert(0,'/home/user/detecting-manipulated-blots/pilot/facs')
import within3
from PIL import Image
from multiprocessing import Pool
def one(t):
    d,x,k,seed=t;rnd=random.Random(seed)
    try:
        im=Image.open(d+'/figs/'+x['file']).convert('RGB');b=x['panels'][k]['box'];p=np.asarray(im.crop((b[0],b[1],b[2]+1,b[3]+1))).copy()
    except Exception: return None
    H,W=p.shape[:2]
    if min(H,W)<120: return None
    base=within3.scan(p,zmin=0)
    if base['ndots']<60: return None
    frac=rnd.choice([0.12,0.18,0.25,0.35]);w,h=int(W*frac),int(H*frac);g=p.min(2)
    for _ in range(300):
        x0=rnd.randrange(int(W*.06),W-w-int(W*.06));y0=rnd.randrange(int(H*.06),H-h-int(H*.06))
        ink=(g[y0:y0+h,x0:x0+w]<160).mean()
        dx=rnd.randint(-W//3,W//3);dy=rnd.randint(-H//3,H//3)
        if 0.02<ink<0.35 and int(W*.06)<=x0+dx<W-w-int(W*.06) and int(H*.06)<=y0+dy<H-h-int(H*.06) and (abs(dx)>w*0.6 or abs(dy)>h*0.6): break
    else: return None
    q=p.copy();q[y0+dy:y0+dy+h,x0+dx:x0+dx+w]=np.minimum(q[y0+dy:y0+dy+h,x0+dx:x0+dx+w],p[y0:y0+h,x0:x0+w])
    buf=io.BytesIO();Image.fromarray(q).save(buf,'JPEG',quality=88);r=within3.scan(np.asarray(Image.open(buf).convert('RGB')),zmin=0)
    ok=[hh for hh in r['hits'] if (abs(hh['dx']-dx)<=1 and abs(hh['dy']-dy)<=1) or (abs(hh['dx']+dx)<=1 and abs(hh['dy']+dy)<=1)]
    m,_=within3.dot_mask(p);nsrc=int(cv2_cc(m[y0:y0+h,x0:x0+w]))
    return {'frac':frac,'ndots':base['ndots'],'src_dots':nsrc,'clean_z':base['hits'][0]['z'] if base['hits'] else 0,'clean':base['hits'][0] if base['hits'] else None,'found':bool(ok),'rank1':bool(ok) and r['hits'][0] is ok[0],'z':ok[0]['z'] if ok else None,'hit':ok[0] if ok else None,'file':x['file'],'panel':k,'dir':d}
def cv2_cc(m):
    import cv2;return cv2.connectedComponents(m.astype(np.uint8),8)[0]-1
if __name__=='__main__':
    J=[];rnd=random.Random(7)
    for d in sorted(glob.glob('facs/pmcbig/c[1-9]')):
        P=[x for x in json.load(open(d+'/panels.json')) if x['panels']]
        for x in rnd.sample(P,60): J.append((d,x,rnd.randrange(len(x['panels'])),rnd.randrange(10**6)))
    with Pool(3) as p: R=[r for r in p.map(one,J,chunksize=4) if r]
    json.dump(R,open('facs/syn/plant3.json','w'));print(len(R),'planted')
    cz=np.array([r['clean_z'] for r in R]);print('clean best z percentiles 50/90/95/99:',np.round(np.percentile(cz,[50,90,95,99]),1))
    for thr in (8,10,12,15):
        print('z>=',thr,'clean panels flagged %.0f%%'%(100*(cz>=thr).mean()),'planted found (top hit, z>=thr): %d of %d'%(sum(r['rank1'] and r['z']>=thr for r in R),len(R)))
    for f in (0.12,0.18,0.25,0.35):
        S=[r for r in R if r['frac']==f];print(f,len(S),'top hit at planted offset',sum(r['rank1'] for r in S),'median z',np.round(np.median([r['z'] for r in S if r['found']] or [0]),1),'median source dots',np.median([r['src_dots'] for r in S]))
