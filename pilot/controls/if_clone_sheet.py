import json,cv2,numpy as np,sys
src,out=sys.argv[1],sys.argv[2];amin=int(sys.argv[3]) if len(sys.argv)>3 else 120
D=json.load(open(src));rows=[]
for r in D:
    for f in r.get('found') or []:
        if min(abs(f['shift'][0]),abs(f['shift'][1]))>3 and f['area']>=amin: rows.append((f,r))
rows.sort(key=lambda t:-t[0]['area']);tiles=[]
for i,(f,r) in enumerate(rows):
    im=cv2.imread('icc_all/images/'+r['file']);x,y,w,h=f['bbox'];dx,dy=f['shift'];p=26
    x0=max(0,x-p,-dx);y0=max(0,y-p,-dy);x1=min(im.shape[1],x+w+p,im.shape[1]-dx);y1=min(im.shape[0],y+h+p,im.shape[0]-dy)
    if x1-x0<8 or y1-y0<8: continue
    A=im[y0:y1,x0:x1];B=im[y0+dy:y1+dy,x0+dx:x1+dx]
    df=np.clip(np.abs(A.astype(np.float32)-B).max(2)*4,0,255).astype(np.uint8);Dd=cv2.cvtColor(255-df,cv2.COLOR_GRAY2BGR)
    t=np.hstack([A,B,Dd]);sc=min(200/t.shape[0],480/t.shape[1]);t=cv2.resize(t,None,fx=sc,fy=sc,interpolation=cv2.INTER_NEAREST)
    th=cv2.resize(im,(int(im.shape[1]*200/im.shape[0]),200));cv2.rectangle(th,(int(x*200/im.shape[0]),int(y*200/im.shape[0])),(int((x+w)*200/im.shape[0]),int((y+h)*200/im.shape[0])),(0,255,255),2);cv2.rectangle(th,(int((x+dx)*200/im.shape[0]),int((y+dy)*200/im.shape[0])),(int((x+dx+w)*200/im.shape[0]),int((y+dy+h)*200/im.shape[0])),(0,255,0),2)
    th=th[:,:230];c=np.full((224,720,3),255,np.uint8);c[22:22+t.shape[0],:t.shape[1]]=t;c[22:222,486:486+th.shape[1]]=th
    cv2.putText(c,f"{i} {r['catalog']} {r['file'][:6]} a{f['area']} in{f['inside']} ring{f['ring']} {f['shift']} n{len(r['found'])}",(2,15),0,0.45,(0,0,0),1,cv2.LINE_AA);tiles.append(c)
for p in range(0,len(tiles),12):
    ch=tiles[p:p+12];rw=[np.hstack(ch[q:q+2]+[np.full((224,720,3),255,np.uint8)]*(2-len(ch[q:q+2]))) for q in range(0,len(ch),2)]
    cv2.imwrite(f'{out}{p//12}.jpg',np.vstack(rw))
print(len(tiles),'tiles')
