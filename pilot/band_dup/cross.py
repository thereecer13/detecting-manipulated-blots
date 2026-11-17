"""Cross-blot band search: the same band appearing in two different blot images.

  python3 cross.py bands  ITEMS.json [ITEMS2.json ...] --out DIR   # stage 1: whole, unusual bands + descriptors
  python3 cross.py pairs  --out DIR                                # stage 2: candidate pairs by descriptor
  python3 cross.py verify --out DIR                                # stage 3: pixel / outline / context checks

Items are [name, path, catalog, url]. Run from the scratch directory that holds the image paths.
"""
import sys,os,json,hashlib,argparse,cv2,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from bandlib import load,find_bands,VARIANTS
from outline import _mask,_iou,_center
import multiprocessing as mp
DW,DH=32,16
FL={'same':lambda d:d,'hflip':lambda d:d[:,:,::-1],'vflip':lambda d:d[:,::-1],'rot180':lambda d:d[:,::-1,::-1]}

def band_feats(g,b,pad=10):
    """Whole-band test and shape features for one band box. None if the band is partial or featureless."""
    x,y,w,h=b;H,W=g.shape
    if x-pad<0 or y-pad<0 or x+w+pad>W or y+h+pad>H: return None
    A=g[y-pad:y+h+pad,x-pad:x+w+pad];sh=(A.shape[0]+8,A.shape[1]+8);un=[];masks=[]
    for f in(0.3,0.5,0.7):
        m,t=_mask(A,f)
        if m is None or (f==0.3 and t): return None
        c=_center(m,sh);masks.append(m)
        un.append(1-np.mean([_iou(c,_center(v(m),sh),1) for k,v in VARIANTS.items() if k!='same']))
    v=A[masks[1]].astype(np.float32);sat=float((v<=v.min()+6).mean()) if v.min()<40 else 0.0
    return float(np.mean(un)),sat

def _bands(it):
    try:
        g=load(it[1]);out=[]
        for b in find_bands(g):
            x,y,w,h=b
            if w<30 or h<10: continue
            f=band_feats(g,b)
            if f is None or f[0]<0.05: continue
            P=g[y-4:y+h+4,x-4:x+w+4].astype(np.float32)
            if np.percentile(P,98)-np.percentile(P,2)<30: continue
            d=cv2.resize(P,(DW,DH),interpolation=cv2.INTER_AREA);d-=d.mean();n=np.linalg.norm(d)
            if n<1e-3: continue
            out.append((b,f[0],f[1],(d/n).astype(np.float32)))
        return it[0],hashlib.md5(open(it[1],'rb').read()).hexdigest(),out
    except Exception as e:
        return it[0],None,[]

def stage_bands(files,out):
    items=[];seen=set()
    for f in files:
        for i in json.load(open(f)):
            if i[0] not in seen: seen.add(i[0]);items.append(i)
    with mp.Pool(3) as P: res=P.map(_bands,items,chunksize=16)
    it={i[0]:i for i in items};md={};meta=[];D=[]
    for name,h,bands in res:
        if h is None or not bands: continue
        if h in md: md[h]['also'].append([name,it[name][2]]);continue      # identical file on another product
        md[h]={'also':[]}
        for b,un,sat,d in bands:
            meta.append({'name':name,'path':it[name][1],'cat':it[name][2],'url':it[name][3],'md5':h,'box':list(b),'unusual':un,'sat':sat});D.append(d)
    json.dump({'meta':meta,'also':{h:v['also'] for h,v in md.items() if v['also']}},open(out+'/bands.json','w'))
    np.save(out+'/desc.npy',np.array(D,np.float32))
    print(len(items),'images;',len(md),'distinct files with a whole, unusual band;',len(meta),'bands')

def stage_pairs(out,thr=0.985,topk=6):
    meta=json.load(open(out+'/bands.json'))['meta'];D=np.load(out+'/desc.npy');N=len(D)
    w=np.array([m['box'][2] for m in meta],np.float32);h=np.array([m['box'][3] for m in meta],np.float32)
    xs=np.array([m['box'][0] for m in meta],np.float32)   # same-image pairs must sit in different lanes
    cats=np.unique([m['cat'] for m in meta],return_inverse=True)[1]
    imgs=np.unique([m['name'] for m in meta],return_inverse=True)[1]
    flat={k:np.ascontiguousarray(f(D)).reshape(N,-1) for k,f in FL.items()};base=flat['same'];pairs={}
    for s in range(0,N,400):
        e=min(N,s+400);best=np.full((e-s,N),-1,np.float32);arg=np.zeros((e-s,N),np.uint8)
        for vi,k in enumerate(FL):
            S=base[s:e]@flat[k].T;u=S>best;best[u]=S[u];arg[u]=vi
        rw=w[s:e,None]/w[None];rh=h[s:e,None]/h[None]
        ok=(rw>0.8)&(rw<1.25)&(rh>0.8)&(rh<1.25)&(((imgs[s:e,None]!=imgs[None])&(cats[s:e,None]!=cats[None]))|((imgs[s:e,None]==imgs[None])&(np.abs(xs[s:e,None]-xs[None])>=0.6*w[None])))
        best[~ok]=-1
        for i in range(e-s):
            r=best[i];js=np.nonzero(r>=thr)[0]
            if len(js)>topk: js=js[np.argsort(-r[js])[:topk]]
            for j in js:
                a,b=(s+i,int(j)) if s+i<j else (int(j),s+i)
                if (a,b) not in pairs or pairs[(a,b)][0]<r[j]: pairs[(a,b)]=(float(r[j]),list(FL)[arg[i,j]])
    json.dump([[a,b,v[0],v[1]] for (a,b),v in pairs.items()],open(out+'/pairs.json','w'))
    print(N,'bands;',len(pairs),'candidate pairs at descriptor similarity >=',thr)

def check(ga,gb,ba,bb,var):
    """Pixel, outline and context comparison of band ba in image ga with band bb in gb (turned by var)."""
    def crop(g,b,p):
        x,y,w,h=b;H,W=g.shape
        if x-p<0 or y-p<0 or x+w+p>W or y+h+p>H: return None
        return g[y-p:y+h+p,x-p:x+w+p]
    scaled=abs(ba[2]-bb[2])>2 or abs(ba[3]-bb[3])>2
    if scaled:      # bring image b to image a's band scale
        fx,fy=ba[2]/bb[2],ba[3]/bb[3];gb=cv2.resize(gb,None,fx=fx,fy=fy,interpolation=cv2.INTER_AREA if fx<1 else cv2.INTER_LINEAR)
        bb=[round(bb[0]*fx),round(bb[1]*fy),ba[2],ba[3]]
    P=crop(ga,ba,7);Q=crop(gb,bb,4)
    if P is None or Q is None: return None
    P=P.astype(np.float32);t=np.ascontiguousarray(VARIANTS[var](Q)).astype(np.float32)
    if t.shape[0]>P.shape[0] or t.shape[1]>P.shape[1]: return None
    rng=float(np.percentile(t,98)-np.percentile(t,2))
    r=cv2.matchTemplate(P,t,cv2.TM_SQDIFF);_,_,loc,_=cv2.minMaxLoc(r)
    win=P[loc[1]:loc[1]+t.shape[0],loc[0]:loc[0]+t.shape[1]];a,c=np.polyfit(t.ravel(),win.ravel(),1)
    if not 0.6<a<1.6 or rng<30: return None
    e=float(np.sqrt(np.mean((a*t+c-win)**2)))/rng
    # outlines
    A=crop(ga,ba,10);B=crop(gb,bb,10)
    if A is None or B is None: return None
    B=np.ascontiguousarray(VARIANTS[var](B));sh=(max(A.shape[0],B.shape[0])+8,max(A.shape[1],B.shape[1])+8);ious=[]
    for f in(0.3,0.5,0.7):
        ma,_=_mask(A,f);mb,_=_mask(B,f)
        if ma is None or mb is None: return None
        ious.append(_iou(_center(ma,sh),_center(mb,sh)))
    # context: the surroundings of the two bands, aligned on the band match, band area excluded
    xa,ya,wa,ha=ba;xb,yb,wb,hb=bb;ax=xa-7+loc[0]+t.shape[1]/2;ay=ya-7+loc[1]+t.shape[0]/2;bx=xb+wb/2;by=yb+hb/2
    Ha,Wa=ga.shape;Hb,Wb=gb.shape
    mx=int(min(ax,Wa-ax,bx,Wb-bx,wa/2+1.5*wa));my=int(min(ay,Ha-ay,by,Hb-by,ha/2+3*ha));ctx=None;ctx_n=0
    if mx>wa/2+12 and my>ha/2+8:
        CA=ga[int(ay)-my:int(ay)+my,int(ax)-mx:int(ax)+mx].astype(np.float32)
        CB=np.ascontiguousarray(VARIANTS[var](gb[int(by)-my:int(by)+my,int(bx)-mx:int(bx)+mx])).astype(np.float32)
        if CA.shape==CB.shape:
            k=np.ones(CA.shape,bool);k[my-ha//2-8:my+ha//2+8,mx-wa//2-10:mx+wa//2+10]=False
            # allow +-2 px of slack between the two crops
            best=-2
            for dy in range(-2,3):
                for dx in range(-2,3):
                    u=np.roll(np.roll(CB,dy,0),dx,1)[k];v=CA[k]
                    if u.std()>1 and v.std()>1: best=max(best,float(np.corrcoef(u,v)[0,1]))
            if best>-2: ctx=best
            ctx_n=int(k.sum())
    return dict(scaled=bool(scaled),gain=float(a),nrmse=e,outline=float(np.mean(ious)),ctx=ctx,ctx_n=ctx_n,loc=[int(loc[0])-3,int(loc[1])-3])

_M=None
def _verify(job):
    a,b,sim,var=job;ma,mb=_M[a],_M[b]
    try:
        r=check(load(ma['path']),load(mb['path']),ma['box'],mb['box'],var)
    except Exception as e: r=None
    return [a,b,sim,var,r]

def stage_verify(out):
    global _M
    _M=json.load(open(out+'/bands.json'))['meta'];jobs=json.load(open(out+'/pairs.json'))
    with mp.Pool(3) as P: res=P.map(_verify,jobs,chunksize=32)
    res=[r for r in res if r[4]];json.dump(res,open(out+'/verified.json','w'))
    print(len(jobs),'pairs;',len(res),'comparable;',sum(r[4]['nrmse']<=0.05 and r[4]['outline']>=0.92 for r in res),'pass nrmse<=0.05 and outline>=0.92')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('stage');ap.add_argument('files',nargs='*');ap.add_argument('--out',required=True);a=ap.parse_args()
    os.makedirs(a.out,exist_ok=True)
    {'bands':lambda:stage_bands(a.files,a.out),'pairs':lambda:stage_pairs(a.out),'verify':lambda:stage_verify(a.out)}[a.stage]()
