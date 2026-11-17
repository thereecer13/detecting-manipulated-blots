import sys,cv2,numpy as np
sys.path.insert(0,'band')
from bandlib import load,VARIANTS
def render(path,hit,outprefix,pad=4):
    """hit=(nrmse,ncc,variant,[x,y,w,h],[lx,ly]) -> writes _o.png (original), _m.png (marked), _z.png (zoom)"""
    g=load(path);H,W=g.shape;e,ncc,var,(x,y,w,h),(lx,ly)=hit
    y0,y1,x0,x1=max(0,y-pad),min(H,y+h+pad),max(0,x-pad),min(W,x+w+pad);ph,pw=y1-y0,x1-x0
    cv2.imwrite(outprefix+'_o.png',g)
    m=g.copy()
    for (bx,by),t in(((x0,y0),'A'),((lx,ly),'B')):
        cv2.rectangle(m,(bx-4,by-4),(bx+pw+3,by+ph+3),255,3);cv2.rectangle(m,(bx-3,by-3),(bx+pw+2,by+ph+2),0,1)
        ty=by-8 if by>20 else by+ph+18
        cv2.putText(m,t,(bx-2,ty),cv2.FONT_HERSHEY_SIMPLEX,0.6,255,4);cv2.putText(m,t,(bx-2,ty),cv2.FONT_HERSHEY_SIMPLEX,0.6,0,2)
    cv2.imwrite(outprefix+'_m.png',m)
    A=g[y0:y1,x0:x1].astype(np.float32);Bn=g[ly:ly+ph,lx:lx+pw].astype(np.float32)
    inv={'same':'same','hflip':'hflip','vflip':'vflip','rot180':'rot180'}[var]
    Bo=np.ascontiguousarray(VARIANTS[inv](Bn))  # B turned back into A's orientation
    a,b=np.polyfit(A.ravel(),Bo.ravel(),1);D=np.clip(128+4*(Bo-(a*A+b)),0,255)
    s=max(2,min(10,220//pw))
    up=lambda p:cv2.resize(np.clip(p,0,255).astype(np.uint8),None,fx=s,fy=s,interpolation=cv2.INTER_NEAREST)
    tiles=[('A',up(A)),('B as shown',up(Bn)),('B turned to match A' if var!='same' else 'B',up(Bo)),('difference x4',up(D))]
    if var=='same': tiles.pop(2)
    gap=14;hh=tiles[0][1].shape[0]+26;ww=sum(t[1].shape[1] for t in tiles)+gap*(len(tiles)+1)
    z=np.full((hh,ww),255,np.uint8);cx=gap
    for name,t in tiles:
        z[22:22+t.shape[0],cx:cx+t.shape[1]]=t;cv2.putText(z,name,(cx,15),cv2.FONT_HERSHEY_SIMPLEX,0.42,0,1,cv2.LINE_AA);cx+=t.shape[1]+gap
    cv2.imwrite(outprefix+'_z.png',z)
if __name__=='__main__':
    import json
    o=json.load(open('band/null_out3.json'));it={i[0]:i[1] for i in json.load(open('band/null_items.json'))}
    o=[r for r in o if r[2]];o.sort(key=lambda r:r[2][0][0])
    for k,r in enumerate(o[:3]): render(it[r[0]],r[2][0],f'band/t{k}');print(r[0],r[2][0])
