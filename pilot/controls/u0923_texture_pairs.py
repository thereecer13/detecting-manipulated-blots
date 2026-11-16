import json,sys,re,itertools
import numpy as np,cv2
from PIL import Image
R=json.load(open(sys.argv[1]))
groups={'dark':[0,2,3,4,5,6,7,8,9,10,11,12,13,14,17,25,26,27,29,30,31,38],'two_lane_box':[15,16,28,32,33,34,35,36,37,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54],'single_A':[18,19,20,21,22,23,24,59],'grey_B':[1,55,56,57,58,60]}
refs={'single_A':[('REF PA5-99645','aval/PA5-99645_rich.png')],'grey_B':[('REF TSEN54 2019','sp/exB/PA5-101939-TSEN54-WB-1-20190808102937.jpg'),('REF GRB14 2019','sp/exB/PA5-101612-GRB14-WB-1-20190808102937.jpg')]}
def nm(u): return re.search(r'/650/([^/]+?-WB-?\d*)',u).group(1)
def prep(p,shape):
    g=np.asarray(Image.open(p).convert('L')).astype(np.float32)
    g=cv2.resize(g,(shape[1],shape[0]),interpolation=cv2.INTER_AREA)
    h=g-cv2.GaussianBlur(g,(0,0),2.5)
    h=h-cv2.blur(h,(1,61))  # remove vertical streak/column structure
    mad=np.median(np.abs(h))+1e-3
    bad=cv2.dilate(((np.abs(h)>14*mad)|(g<4)|(g>251)).astype(np.uint8),np.ones((5,5),np.uint8))>0
    return h,~bad
def score(A,B,s=6):
    (ha,ma),(hb,mb)=A,B;best=(-1,0,0)
    for dy in range(-s,s+1,1):
        for dx in range(-s,s+1,1):
            hb2=np.roll(np.roll(hb,dy,0),dx,1);mb2=np.roll(np.roll(mb,dy,0),dx,1)
            m=ma&mb2
            m[:s+1]=m[-s-1:]=False;m[:,:s+1]=m[:,-s-1:]=False
            if m.sum()<3000: continue
            r=np.corrcoef(ha[m],hb2[m])[0,1]
            if r>best[0]: best=(float(r),dy,dx)
    return best
out=[]
for gname,ids in groups.items():
    items=[(nm(R[i]['url']),R[i]['path'],i) for i in ids]+[(n,p,-1) for n,p in refs.get(gname,[])]
    shape=(480,360)
    P=[prep(p,shape) for _,p,_ in items]
    for a,b in itertools.combinations(range(len(items)),2):
        r,dy,dx=score(P[a],P[b])
        # control: one image flipped vertically
        rc=score(P[a],(P[b][0][::-1].copy(),P[b][1][::-1].copy()),s=2)[0]
        out.append(dict(group=gname,a=items[a][0],b=items[b][0],ia=items[a][2],ib=items[b][2],r=round(r,3),dy=dy,dx=dx,flip_r=round(rc,3)))
    print(gname,'done',flush=True)
json.dump(out,open(sys.argv[2],'w'),indent=0)
