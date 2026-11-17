"""Round-3 band review page: unreviewed within-blot candidates plus cross-blot groups (same band on several products).
  python3 build_page3.py   (from the scratch dir; writes band/review_r3/ and band/review_r3_items.json, _key.json)"""
import json,os,sys,re,random,cv2,numpy as np
sys.path.insert(0,'band')
from bandlib import load
from build_page import item,VT
from PIL import Image
OUT='band/review_r3';os.makedirs(OUT,exist_ok=True);random.seed(5)
def okdate(d): return d if re.match(r'20\d\d-(0[1-9]|1[0-2])-([0-2]\d|3[01])$',d) else 'no date'
def padcrop(g,x0,y0,x1,y1):
    H,W=g.shape;o=np.full((y1-y0,x1-x0),255,np.uint8)
    a,b,c,d=max(0,x0),max(0,y0),min(W,x1),min(H,y1)
    if c>a and d>b: o[b-y0:d-y0,a-x0:c-x0]=g[b:d,a:c]
    return o
def label(img,text,h=26):
    t=np.full((img.shape[0]+h,max(img.shape[1],9*len(text)+8)),255,np.uint8);t[h:,:img.shape[1]]=img
    cv2.putText(t,text,(4,18),cv2.FONT_HERSHEY_SIMPLEX,0.5,0,1,cv2.LINE_AA);return t
def group_item(idx,G):
    mem=sorted(G['members'],key=lambda m:(m['listed'],m['cat']));seen=set();M=[]
    for m in mem:
        if m['cat'] in seen: continue
        seen.add(m['cat']);M.append(m)
    M=M[:5];ims=[load(m['path']) for m in M];pre=os.path.abspath(f'{OUT}/{idx}')
    # row of whole blots, band boxed
    tiles=[]
    for m,g in zip(M,ims):
        c=cv2.cvtColor(g,cv2.COLOR_GRAY2BGR);x,y,w,h=m['box'];cv2.rectangle(c,(x-6,y-6),(x+w+6,y+h+6),(0,0,230),2)
        s=430/c.shape[0];c=cv2.resize(c,(int(c.shape[1]*s),430),interpolation=cv2.INTER_AREA)
        t=np.full((430+28,max(c.shape[1],250),3),255,np.uint8);t[28:,:c.shape[1]]=c
        cv2.putText(t,f"{m['cat']} {m['target'][:16]}",(4,19),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,0,0),1,cv2.LINE_AA);tiles.append(t)
    row=np.hstack([np.pad(t,((0,0),(0,10),(0,0)),constant_values=255) for t in tiles]);cv2.imwrite(pre+'_row.png',row)
    # aligned band crops, cycling
    r=M[0];rx,ry,rw,rh=r['box'];mx,my=55,38;R=padcrop(ims[0],rx-7,ry-7,rx+rw+7,ry+rh+7).astype(np.float32);fr=[]
    for m,g in zip(M,ims):
        x,y,w,h=m['box'];ox=oy=0
        if m is not r:
            t=padcrop(g,x-3,y-3,x+w+3,y+h+3).astype(np.float32)
            if t.shape[0]<=R.shape[0] and t.shape[1]<=R.shape[1]:
                _,_,_,loc=cv2.minMaxLoc(cv2.matchTemplate(R,t,cv2.TM_CCOEFF_NORMED));ox,oy=(x-3)-(rx-7+loc[0]),(y-3)-(ry-7+loc[1])
        c=padcrop(g,rx+ox-mx,ry+oy-my,rx+ox+rw+mx,ry+oy+rh+my);c=cv2.resize(c,None,fx=4,fy=4,interpolation=cv2.INTER_NEAREST)
        fr.append(Image.fromarray(label(c,f"{m['cat']} {m['target'][:22]} ({okdate(m['date'])})")))
    W=max(f.width for f in fr);fr=[Image.fromarray(np.pad(np.asarray(f),((0,0),(0,W-f.width)),constant_values=255)) for f in fr]
    fr[0].save(pre+'.gif',save_all=True,append_images=fr[1:],duration=800,loop=0,optimize=True)
    ctx=G['ctx_med'];sur='surroundings also match (same image region)' if ctx is not None and ctx>=0.9 else ('surroundings partly match' if ctx is not None and ctx>=0.6 else 'surroundings differ; only the band matches')
    n=G['n_products'];desc='; '.join(f"{m['cat']} {m['target']} ({okdate(m['date'])}{', in Richardson' if m['listed'] else ''})" for m in M)
    lab=f"Across blots: {n} products show this band{' (5 shown)' if n>5 else ''} — {sur}. {desc}"
    return {'id':idx,'label':lab,'images':[{'path':pre+'_row.png','caption':'each blot with the matching band boxed','color':True},{'path':pre+'.gif','caption':'the band and its surroundings, aligned on the band and alternating (4x)'}]}
if __name__=='__main__':
    items=[];key={}
    W=json.load(open('band/r3_within.json'))
    for n,s in enumerate(W):
        idx=f'W{n:02d}';it=item(idx,f"Within one blot ({s['cat']}): B matches A {VT[s['hit'][2]]} — outline match {100*s['feat']['outline']:.0f}%, fill match {100*(1-s['hit'][0]):.1f}%",s['path'],s['hit'],OUT,side=640)
        items.append(it);key[idx]=s
    G=[g for g in json.load(open('band/xall/groups.json')) if g['n_unlisted']>0]
    for n,g in enumerate(G):
        idx=f'G{n:02d}';items.append(group_item(idx,g));key[idx]={'kind':'cross','members':g['members'],'pairs':g['pairs'],'ctx_med':g['ctx_med'],'n_products':g['n_products'],'n_unlisted':g['n_unlisted']}
    json.dump(items,open('band/review_r3_items.json','w'));json.dump(key,open('band/review_r3_key.json','w'),indent=1);print(len(W),'within +',len(G),'groups')
