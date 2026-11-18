"""For two blot images, find every band of one that matches a band of the other (any orientation) and draw them.
  python3 pair_page.py   (from the scratch dir; rebuilds the round-3 groups that matched after a flip)"""
import json,os,sys,cv2,numpy as np
sys.path.insert(0,'band')
from bandlib import load,find_bands,VARIANTS
import cross
from PIL import Image
COL=[(0,0,230),(230,120,0),(0,150,0),(170,0,170)]
VT={'same':'as is','hflip':'mirrored left-right','vflip':'flipped top-bottom','rot180':'rotated 180 degrees'}
def all_pairs(ga,gb,mx=0.05,mo=0.90):
    out=[]
    for a in find_bands(ga):
        for b in find_bands(gb):
            best=None
            for v in VARIANTS:
                r=cross.check(ga,gb,list(a),list(b),v)
                if r and (best is None or r['nrmse']<best[1]['nrmse']): best=(v,r)
            if best and best[1]['nrmse']<=mx and best[1]['outline']>=mo: out.append((a,b,best[0],best[1]))
    return out
def crop(g,b,mx=45,my=30):
    x,y,w,h=b;H,W=g.shape;o=np.full((h+2*my,w+2*mx),255,np.uint8)
    x0,y0=x-mx,y-my;a,c,d,e=max(0,x0),max(0,y0),min(W,x0+o.shape[1]),min(H,y0+o.shape[0]);o[c-y0:e-y0,a-x0:d-x0]=g[c:e,a:d];return o
def build(idx,ma,mb,out):
    ga,gb=load(ma['path']),load(mb['path']);P=all_pairs(ga,gb);pre=os.path.abspath(f'{out}/{idx}');tiles=[]
    for g,m,k in((ga,ma,0),(gb,mb,1)):
        c=cv2.cvtColor(g,cv2.COLOR_GRAY2BGR)
        for n,p in enumerate(P):
            x,y,w,h=p[k];cv2.rectangle(c,(x-6,y-6),(x+w+6,y+h+6),COL[n%4],2);cv2.putText(c,str(n+1),(x-6,y-10),cv2.FONT_HERSHEY_SIMPLEX,0.6,COL[n%4],2,cv2.LINE_AA)
        s=560/c.shape[0];c=cv2.resize(c,(int(c.shape[1]*s),560),interpolation=cv2.INTER_AREA);t=np.full((588,c.shape[1]+12,3),255,np.uint8);t[28:,:c.shape[1]]=c
        cv2.putText(t,f"{m['cat']} {m['target'][:20]}",(4,19),cv2.FONT_HERSHEY_SIMPLEX,0.55,(0,0,0),1,cv2.LINE_AA);tiles.append(t)
    cv2.imwrite(pre+'_row.png',np.hstack(tiles));ims=[{'path':pre+'_row.png','caption':'both blots; boxes with the same number and colour mark a matching pair of bands','color':True}]
    for n,(a,b,v,r) in enumerate(P):
        A=crop(ga,a);fx,fy=a[2]/b[2],a[3]/b[3];B=crop(gb,b,int(round(45/fx)),int(round(30/fy)));B=np.ascontiguousarray(VARIANTS[v](cv2.resize(B,(A.shape[1],A.shape[0]),interpolation=cv2.INTER_LINEAR)))
        # fine alignment of B on A
        t=B[20:-20,25:-25].astype(np.float32);_,_,_,loc=cv2.minMaxLoc(cv2.matchTemplate(A.astype(np.float32),t,cv2.TM_CCOEFF_NORMED));B=np.roll(np.roll(B,loc[1]-20,0),loc[0]-25,1);fr=[]
        for nm,Pp in((f"pair {n+1}: {ma['cat']}",A),(f"pair {n+1}: {mb['cat']} ({VT[v]})",B)):
            u=cv2.resize(Pp,None,fx=5,fy=5,interpolation=cv2.INTER_NEAREST);c=np.full((u.shape[0]+30,max(u.shape[1],520)),255,np.uint8);c[30:,:u.shape[1]]=u
            cv2.putText(c,nm,(4,21),cv2.FONT_HERSHEY_SIMPLEX,0.6,0,2,cv2.LINE_AA);fr.append(Image.fromarray(c))
        fr[0].save(f'{pre}_p{n}.gif',save_all=True,append_images=fr[1:],duration=800,loop=0)
        ims.append({'path':f'{pre}_p{n}.gif','caption':f"pair {n+1}, aligned and alternating (5x); the second band is shown {VT[v]}; fill match {100*(1-r['nrmse']):.1f}%, outline match {100*r['outline']:.0f}%"})
    lab=f"{ma['cat']} {ma['target']} and {mb['cat']} {mb['target']}: {len(P)} matching band pair(s), orientations: {', '.join(VT[p[2]] for p in P) or 'none'}"
    return {'id':idx,'label':lab,'images':ims},[[list(p[0]),list(p[1]),p[2],p[3]['nrmse'],p[3]['outline']] for p in P]
if __name__=='__main__':
    key=json.load(open('band/review_r3_key.json'));it={l[0]:l[1] for l in json.load(open('band/m_items.json'))};out='band/review_r3c';os.makedirs(out,exist_ok=True);items=[];k2={}
    for g in sys.argv[1:]:
        ms=[];seen=set()
        for m in key[g]['members']:
            if m['cat'] not in seen: seen.add(m['cat']);m=dict(m,path=it[m['name']]);ms.append(m)
        i,p=build(g,ms[0],ms[1],out);items.append(i);k2[g]={'members':[{k:v for k,v in m.items() if k!='path'} for m in ms[:2]],'pairs':p};print(g,i['label'])
    json.dump(items,open('band/review_r3c_items.json','w'));json.dump(k2,open('band/review_r3c_key.json','w'),indent=1)
