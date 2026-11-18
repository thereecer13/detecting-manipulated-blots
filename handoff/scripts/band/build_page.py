"""Build review items (boxed original, contrast-enhanced, A/B GIF, orange difference) for a list of hits."""
import json,os,sys,cv2,numpy as np
sys.path.insert(0,'band');sys.path.insert(0,'/home/user/detecting-manipulated-blots/pilot')
from bandlib import load,VARIANTS
from views import levels_richardson
from PIL import Image
VT={'same':'as is','hflip':'mirrored left-right','vflip':'flipped top-bottom','rot180':'rotated 180 degrees'}
def item(idx,label,path,hit,outdir,pad=4,side=400):
    g=load(path);H,W=g.shape;e,ncc,var,(x,y,w,h),(lx,ly)=hit
    y0,y1,x0,x1=max(0,y-pad),min(H,y+h+pad),max(0,x-pad),min(W,x+w+pad);ph,pw=y1-y0,x1-x0
    pre=os.path.abspath(f'{outdir}/{idx}');m=g.copy()
    for (bx,by),t in(((x0,y0),'A'),((lx,ly),'B')):
        cv2.rectangle(m,(bx-4,by-4),(bx+pw+3,by+ph+3),255,3);cv2.rectangle(m,(bx-3,by-3),(bx+pw+2,by+ph+2),0,1)
        ty=by-8 if by>20 else by+ph+18
        cv2.putText(m,t,(bx-2,ty),cv2.FONT_HERSHEY_SIMPLEX,0.6,255,4);cv2.putText(m,t,(bx-2,ty),cv2.FONT_HERSHEY_SIMPLEX,0.6,0,2)
    for a,sfx in((m,'_m.png'),(levels_richardson(g),'_e.png')):
        im=Image.fromarray(a);im.thumbnail((side,side),Image.LANCZOS);im.save(pre+sfx,optimize=True)
    A=g[y0:y1,x0:x1];B=np.ascontiguousarray(VARIANTS[var](g[ly:ly+ph,lx:lx+pw]))
    sc=max(2,min(8,250//pw));fr=[]
    for name,P in(('A',A),('B' if var=='same' else 'B (turned)',B)):
        u=cv2.resize(P,None,fx=sc,fy=sc,interpolation=cv2.INTER_NEAREST)
        c=np.full((u.shape[0]+26,max(u.shape[1],130)),255,np.uint8);c[26:,:u.shape[1]]=u
        cv2.putText(c,name,(3,19),cv2.FONT_HERSHEY_SIMPLEX,0.55,0,2,cv2.LINE_AA);fr.append(Image.fromarray(c))
    fr[0].save(pre+'.gif',save_all=True,append_images=fr[1:],duration=700,loop=0,optimize=True)
    Af,Bf=A.astype(np.float32),B.astype(np.float32);a,b=np.polyfit(Af.ravel(),Bf.ravel(),1)
    d=np.clip(np.abs(Bf-(a*Af+b))*4/128,0,1)[...,None];rgb=((1-d)*np.array([255,150,0],np.float32)).astype(np.uint8)
    Image.fromarray(cv2.resize(rgb,None,fx=sc,fy=sc,interpolation=cv2.INTER_NEAREST)).save(pre+'_d.png',optimize=True)
    return {'id':idx,'label':label,'images':[
        {'path':pre+'_m.png','caption':'original; A = band, B = closest match elsewhere'},
        {'path':pre+'_e.png','caption':'contrast-enhanced, no boxes'},
        {'path':pre+'.gif','caption':'A and B overlaid, alternating'},
        {'path':pre+'_d.png','caption':'difference between A and B, x4: orange where identical, darker where they differ','color':True}]}
if __name__=='__main__':
    import hashlib,random,re
    random.seed(2)
    it={i[0]:i for i in json.load(open('band/all_items.json'))};key=json.load(open('band/review_key.json'))
    done={s['name'] for s in key.values()};donecat={s['cat'] for s in key.values()}
    rows=json.load(open('band/round2_rank.json'));sel=[];seen=set();cats=set()
    for sc,name,hit,f in rows:
        i=it[name];md=hashlib.md5(open(i[1],'rb').read()).hexdigest();k=re.sub(r'-?AV-?','',name)
        if name in done or i[2] in donecat or md in seen or k in seen or i[2] in cats: continue
        seen|={md,k};cats.add(i[2]);sel.append({'name':name,'path':i[1],'cat':i[2],'url':i[3],'hit':hit,'feat':f,'score':sc})
    print(len(sel));sel=sel[:60];random.shuffle(sel)
    os.makedirs('band/review_r2',exist_ok=True);items=[];k2={}
    for n,s in enumerate(sel):
        idx=f'C{n:02d}';items.append(item(idx,f"Blot {n+1} (B matches A {VT[s['hit'][2]]}) — outline match {100*s['feat']['outline']:.0f}%, fill match {100*(1-s['hit'][0]):.1f}%",s['path'],s['hit'],'band/review_r2'));k2[idx]=s
    json.dump(items,open('band/review_r2_items.json','w'));json.dump(k2,open('band/review_r2_key.json','w'),indent=1)
    from collections import Counter;print(Counter(s['hit'][2] for s in sel))
