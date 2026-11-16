import numpy as np,cv2,json,sys
STRICT=True
EXT=2
from PIL import Image
def feats(path):
    g=np.asarray(Image.open(path).convert('L')).astype(np.float32)
    if g.shape[1]>700: g=cv2.resize(g,(650,round(g.shape[0]*650/g.shape[1])),interpolation=cv2.INTER_AREA)
    H,W=g.shape
    # blot region: non-white, filled, large components
    nonwhite=(cv2.GaussianBlur(g,(0,0),2)<246).astype(np.uint8)
    nonwhite=cv2.morphologyEx(nonwhite,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
    n,lab,st,_=cv2.connectedComponentsWithStats(nonwhite)
    mask=np.zeros_like(nonwhite)
    for i in range(1,n):
        x,y,w,h,a=st[i]
        if a>0.02*H*W and w>25 and h>25: mask[lab==i]=1
    mask=cv2.erode(mask,np.ones((7,7),np.uint8))
    usable=(mask>0)&(g>20)&(g<248)
    if usable.sum()<2000: return None
    hp=g-cv2.GaussianBlur(g,(0,0),1.5)
    noise=np.sqrt(np.clip(cv2.blur(hp*hp,(9,9)),0,None))
    mx=cv2.dilate(g,np.ones((5,5),np.uint8));mn=cv2.erode(g,np.ones((5,5),np.uint8))
    exact=(mx-mn)<=EXT
    med=float(np.median(noise[usable]))
    low=exact if STRICT else ((noise<0.25*med)|exact)
    flat=low&usable
    gfrac=float(flat.sum()/usable.sum())
    # flat blobs inside textured membrane: components of flat, require textured ring around
    fl=cv2.morphologyEx(flat.astype(np.uint8),cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    n2,lab2,st2,_=cv2.connectedComponentsWithStats(fl)
    tex=usable&(~low)
    blobs=[]
    for i in range(1,n2):
        x,y,w,h,a=st2[i]
        if a<60: continue
        comp=(lab2[y:y+h,x:x+w]==i).astype(np.uint8)
        ring=cv2.dilate(comp,np.ones((9,9),np.uint8),iterations=1)-comp
        yy0,xx0=y,x
        rtex=tex[yy0:yy0+h,xx0:xx0+w][ring[:h,:w]>0] if True else None
        # ring may extend beyond box; recompute with padded window
        pad=6;y0,y1,x0,x1=max(0,y-pad),min(H,y+h+pad),max(0,x-pad),min(W,x+w+pad)
        c2=(lab2[y0:y1,x0:x1]==i).astype(np.uint8);r2=cv2.dilate(c2,np.ones((11,11),np.uint8))-c2
        ru=usable[y0:y1,x0:x1][r2>0];rt=tex[y0:y1,x0:x1][r2>0]
        if ru.sum()<20: continue
        ring_tex=float(rt.sum()/max(ru.sum(),1))
        blobs.append((int(a),ring_tex,[int(x),int(y),int(w),int(h)],i))
    enclosed=[b for b in blobs if b[1]>0.5]
    area_enc=sum(b[0] for b in enclosed)
    big=max([b[0] for b in enclosed],default=0)
    # band halo: dark blobs relative to lane median, dilated
    lm=float(np.median(g[usable]))
    band=((g<lm-25)&(mask>0)).astype(np.uint8)
    band=cv2.morphologyEx(band,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    halo=cv2.dilate(band,np.ones((31,31),np.uint8))>0
    away=usable&(~halo)
    na=max(int(away.sum()),1)
    flat_away=float((flat&away).sum()/na)
    tex2=usable&(noise>=0.6*med)&(~exact)
    tex_away=float((tex2&away).sum()/na)
    enc_away=[]
    for a,rt,bb,i in enclosed:
        x,y,w,h=bb;comp=lab2[y:y+h,x:x+w]==i
        if halo[y:y+h,x:x+w][comp].mean()<0.3: enc_away.append((a,rt,bb))
    max_enc_away=max([b[0] for b in enc_away],default=0)
    # boundary between flat and textured regions away from bands (per unit area)
    fa=(flat&away).astype(np.uint8);ta=(tex2&away).astype(np.uint8)
    edge=(cv2.dilate(fa,np.ones((5,5),np.uint8))&cv2.dilate(ta,np.ones((5,5),np.uint8))).sum()/na
    # absolute texture level of the textured parts (MAD of hp)
    return dict(flat_away=flat_away,tex_away=tex_away,edge_away=float(edge),away_px=na,halo_frac=float(halo[usable].mean()),med_noise=med,global_flat=gfrac,n_enclosed=len(enclosed),area_enclosed=area_enc/usable.sum(),max_enclosed=big,
                usable=int(usable.sum()),blobs=[b[:3] for b in sorted(enclosed,key=lambda b:-b[0])[:8]],max_enc_away=int(max_enc_away),enc_away=[list(b) for b in sorted(enc_away,key=lambda b:-b[0])[:6]])
if __name__=='__main__':
    import multiprocessing as mp
    items=json.load(open(sys.argv[1]))
    def f(it):
        try: return it+[feats(it[1])]
        except Exception as e: return it+[None]
    with mp.Pool(int(sys.argv[3]) if len(sys.argv)>3 else 3) as P: out=P.map(f,items,chunksize=8)
    json.dump(out,open(sys.argv[2],'w'))
