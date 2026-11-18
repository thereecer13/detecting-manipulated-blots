"""Build review items for spot-clone candidates: outlined image (2x), A/B GIF and difference map per candidate.

    python3 build_review.py SPOT_JSON IMAGES_DIR CANDS_JSON OUT_DIR ITEMS_JSON KEY_JSON

CANDS_JSON: [{"file", "shift", "sg", "box", "area", ...}] (one entry per image file and offset).
"""
import json,os,sys,cv2,numpy as np
from PIL import Image
from collections import defaultdict
COL=[(0,120,255),(255,140,0),(0,170,0),(200,0,200),(0,200,220)]
def build(spot,imgdir,cands,out,prefix='Q'):
    d={r['file']:r for r in json.load(open(spot))};by=defaultdict(list);os.makedirs(out,exist_ok=True)
    for c in cands: by[c['file']].append(c)
    items=[];key={}
    for n,(fn,cs) in enumerate(by.items()):
        r=d[fn];im=cv2.imread(f'{imgdir}/{fn}');S=2;m=cv2.resize(im,None,fx=S,fy=S,interpolation=cv2.INTER_CUBIC)
        idx=f'{prefix}{n:02d}';pre=os.path.abspath(f'{out}/{idx}');imgs=[]
        for k,c in enumerate(cs):
            fs=[f for f in r['found'] if f['shift']==c['shift']];x0,y0,x1,y1=c['box'];dx,dy=c['sg']*c['shift'][0],c['sg']*c['shift'][1];col=COL[k%5][::-1]
            for (ox,oy),t in(((0,0),f'{k+1}A'),((dx,dy),f'{k+1}B')):
                for f in fs:
                    pts=((np.array(f['outline'])+[ox,oy])*S).astype(np.int32)
                    cv2.polylines(m,[pts],True,(255,255,255),3,cv2.LINE_AA);cv2.polylines(m,[pts],True,col,1,cv2.LINE_AA)
                tx=min(f['bbox'][0] for f in fs)+ox;ty=min(f['bbox'][1] for f in fs)+oy
                cv2.putText(m,t,(tx*S,ty*S-6),0,0.6,(255,255,255),4,cv2.LINE_AA);cv2.putText(m,t,(tx*S,ty*S-6),0,0.6,col,2,cv2.LINE_AA)
            A=im[y0:y1,x0:x1].astype(np.float32);B=im[y0+dy:y1+dy,x0+dx:x1+dx].astype(np.float32);sc=max(3,min(8,360//(x1-x0)));fr=[]
            for name,Pt in((f'{k+1}A',A),(f'{k+1}B',B)):
                u=cv2.resize(Pt.astype(np.uint8),None,fx=sc,fy=sc,interpolation=cv2.INTER_NEAREST)
                cnv=np.full((u.shape[0]+28,max(u.shape[1],120),3),255,np.uint8);cnv[28:,:u.shape[1]]=u;cv2.putText(cnv,name,(3,20),0,0.6,(0,0,0),2,cv2.LINE_AA);fr.append(Image.fromarray(cnv[:,:,::-1]))
            fr[0].save(f'{pre}_g{k}.gif',save_all=True,append_images=fr[1:],duration=700,loop=0)
            df=np.clip(np.abs(A-B).max(2)*4/128,0,1)[...,None];rgb=((1-df)*np.array([255,150,0],np.float32)).astype(np.uint8)
            Image.fromarray(cv2.resize(rgb,None,fx=sc,fy=sc,interpolation=cv2.INTER_NEAREST)).save(f'{pre}_d{k}.png')
            imgs+=[{'path':f'{pre}_g{k}.gif','caption':f'candidate {k+1}: area {k+1}A and area {k+1}B ({abs(dx)} px across, {abs(dy)} px down from it) alternating, {sc}x; {c["area"]} px matched','color':True},
                   {'path':f'{pre}_d{k}.png','caption':f'candidate {k+1}: difference between {k+1}A and {k+1}B, x4: orange where identical, darker where they differ','color':True}]
        cv2.imwrite(pre+'_m.png',m);name=r['image_url'].split('/')[-1]
        items.append({'id':idx,'label':f"Proteintech {r['catalog']} {name.split('-Antibody')[0]}, image {name}: {len(cs)} candidate copied area(s)",'images':[{'path':pre+'_m.png','caption':'original (2x) with outlines: each numbered A/B pair of outlines marks two areas that match','color':True}]+imgs})
        key[idx]={'catalog':r['catalog'],'image_url':r['image_url'],'product_url':r['product_url'],'candidates':[[c['shift'],c['area']] for c in cs]}
    return items,key
if __name__=='__main__':
    spot,imgdir,cands,out,itemsf,keyf=sys.argv[1:7];items,key=build(spot,imgdir,json.load(open(cands)),out)
    json.dump(items,open(itemsf,'w'));json.dump(key,open(keyf,'w'),indent=1);print(len(items),'items')
