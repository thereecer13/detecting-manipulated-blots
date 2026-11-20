import cv2,numpy as np
A=cv2.imread('bigA.png');Bw=cv2.imread('bigBw.png');pa=np.load('onlyA.npy');pb=np.load('onlyB.npy')
def tm(src,dst,pts,same,tag):
    out=[]
    for x,y,ar in pts:
        r=int(np.sqrt(ar/3.14))+7;t=src[y-r:y+r+1,x-r:x+r+1]
        if t.shape[0]<2*r+1 or t.shape[1]<2*r+1: continue
        best=(-1,None)
        for sc in (1.0,):
            R=cv2.matchTemplate(dst,t,cv2.TM_CCOEFF_NORMED)
            if same: cv2.circle(R,(x-r,y-r),r+4,-1,-1)
            _,mx,_,loc=cv2.minMaxLoc(R)
            best=(mx,(loc[0]+r,loc[1]+r))
        out.append((x,y,ar,round(best[0],3),best[1]));print(tag,(x,y),'area',ar,'best match',round(best[0],3),'at',best[1],'offset',(best[1][0]-x,best[1][1]-y))
    return out
print('--- colonies only in upper plate: best look-alike in the lower plate');ab=tm(A,Bw,pa,False,'U->L')
print('--- colonies only in lower plate: best look-alike in the upper plate');ba=tm(Bw,A,pb,False,'L->U')
print('--- same-plate look-alikes (upper)');aa=tm(A,A,pa,True,'U->U')
print('--- same-plate look-alikes (lower)');bb=tm(Bw,Bw,pb,True,'L->L')
# null: shared colonies matched elsewhere in other plate (excluding own position) to calibrate what score is "lookalike"
import json;json.dump({'ab':ab,'ba':ba},open('tm.json','w'))
