import numpy as np,cv2,json,sys
from PIL import Image
EXT=0
def feats(path,return_maps=False):
    g=np.asarray(Image.open(path).convert('L')).astype(np.float32)
    if g.shape[1]>700: g=cv2.resize(g,(650,round(g.shape[0]*650/g.shape[1])),interpolation=cv2.INTER_AREA)
    H,W=g.shape;gu=np.clip(g,0,255).astype(np.uint8)
    mx=cv2.dilate(gu,np.ones((11,11),np.uint8)).astype(np.int16);mn=cv2.erode(gu,np.ones((11,11),np.uint8)).astype(np.int16)
    exact=(mx-mn)<=EXT
    content=(g>20)&(g<248)
    # blot rectangles: large components of darker-than-page area (labels/ringing on white page excluded)
    blot=(cv2.GaussianBlur(g,(0,0),3)<232).astype(np.uint8)
    blot=cv2.morphologyEx(blot,cv2.MORPH_CLOSE,np.ones((15,15),np.uint8))
    nb,lb,sb,_=cv2.connectedComponentsWithStats(blot);bm=np.zeros_like(blot)
    for i in range(1,nb):
        x,y,w,h,a=sb[i]
        if a>0.01*H*W and w>=20 and h>=60 and a>0.5*w*h: bm[lb==i]=1
    bm=cv2.erode(bm,np.ones((5,5),np.uint8))>0
    content&=bm
    tex=content&(~exact)
    # lane columns: >=55% textured over the rows that have any content in that column band
    rows=np.where(content.mean(1)>0.05)[0]
    if len(rows)<40: return None
    r0,r1=rows.min(),rows.max()
    colfrac=tex[r0:r1+1].mean(0)
    lanecol=cv2.morphologyEx((colfrac>0.55).astype(np.uint8).reshape(1,-1),cv2.MORPH_OPEN,np.ones((1,9),np.uint8)).ravel()>0
    if lanecol.sum()<15: return dict(lane_px=0,max_patch=0,n_patch=0,lane_flat=0.0,patches=[])
    lane=np.zeros_like(content);lane[r0:r1+1,lanecol]=True
    # trim lane vertically to rows that are textured in lane columns
    rowfrac=tex[:,lanecol].mean(1);rr=np.where(rowfrac>0.3)[0];lane[:rr.min()]=False;lane[rr.max()+1:]=False
    lane&=content
    lane=cv2.erode(lane.astype(np.uint8),np.ones((5,5),np.uint8))>0
    lm=float(np.median(g[lane])) if lane.sum() else 0
    band=((g<lm-25)&lane).astype(np.uint8);band=cv2.morphologyEx(band,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    halo=cv2.dilate(band,np.ones((25,25),np.uint8))>0
    flat=(exact&lane&(~halo)).astype(np.uint8)
    flat=cv2.morphologyEx(flat,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    n,lab,st,_=cv2.connectedComponentsWithStats(flat)
    patches=[]
    for i in range(1,n):
        x,y,w,h,a=st[i]
        if a<40: continue
        pad=7;y0,y1,x0,x1=max(0,y-pad),min(H,y+h+pad),max(0,x-pad),min(W,x+w+pad)
        c=(lab[y0:y1,x0:x1]==i).astype(np.uint8);ring=(cv2.dilate(c,np.ones((13,13),np.uint8))-c)>0
        lr=lane[y0:y1,x0:x1][ring];tr=tex[y0:y1,x0:x1][ring]
        if lr.sum()<30: continue
        enc=float(tr.sum()/max(1,ring.sum()))
        if enc>0.6: patches.append([int(a),round(enc,2),[int(x),int(y),int(w),int(h)]])
    patches.sort(key=lambda p:-p[0])
    out=dict(lane_px=int(lane.sum()),max_patch=patches[0][0] if patches else 0,n_patch=len(patches),
             lane_flat=float(((exact&lane&~halo).sum())/max(1,(lane&~halo).sum())),patches=patches[:6])
    if return_maps: out['maps']=(g,lane,flat,halo)
    return out
if __name__=='__main__':
    import multiprocessing as mp
    items=json.load(open(sys.argv[1]))
    def f(it):
        try: return it+[feats(it[1])]
        except Exception as e: return it+[None]
    with mp.Pool(int(sys.argv[3]) if len(sys.argv)>3 else 3) as P: out=P.map(f,items,chunksize=8)
    json.dump(out,open(sys.argv[2],'w'))
