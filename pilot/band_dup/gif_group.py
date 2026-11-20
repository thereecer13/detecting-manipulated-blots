import json,sys,cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,'band')
from bandlib import load
G=json.load(open('band/xall/groups_hi.json'));g=[g for g in G if 'PA5-102302' in {m['cat'] for m in g['members']}][0]
M=sorted(g['members'],key=lambda m:(m['box'][1],m['cat']));F=lambda s,b=True:ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if b else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',s)
cw,ch=150,56;ref=None;frames=[]
def crop(im,cx,cy): 
    x0,y0=int(round(cx-cw/2)),int(round(cy-ch/2));return im[y0:y0+ch,x0:x0+cw]
for n,m in enumerate(M):
    im=load(m['path']);x,y,w,h=m['box'];cx,cy=x+w/2,y+h/2;c=crop(im,cx,cy)
    if ref is None: ref=c
    else:   # fine alignment on the first band
        big=im[int(cy-ch/2)-8:int(cy-ch/2)-8+ch+16,int(cx-cw/2)-8:int(cx-cw/2)-8+cw+16].astype(np.float32)
        _,_,_,loc=cv2.minMaxLoc(cv2.matchTemplate(big,ref[6:-6,10:-10].astype(np.float32),cv2.TM_CCOEFF_NORMED));c=big[loc[1]-6:loc[1]-6+ch,loc[0]-10:loc[0]-10+cw].astype(np.uint8)
    lane=im[:, :330];s=760/lane.shape[0];lane=cv2.resize(lane,(int(lane.shape[1]*s),760),interpolation=cv2.INTER_AREA);lane=cv2.cvtColor(lane,cv2.COLOR_GRAY2RGB)
    cv2.rectangle(lane,(int((x-8)*s),int((y-8)*s)),(int((x+w+8)*s),int((y+h+8)*s)),(230,0,0),3)
    Z=6;zc=cv2.cvtColor(cv2.resize(c,(cw*Z,ch*Z),interpolation=cv2.INTER_CUBIC),cv2.COLOR_GRAY2RGB)
    W=40+lane.shape[1]+50+cw*Z+40;H=110+760+30;cv=Image.new('RGB',(W,H),'white');d=ImageDraw.Draw(cv)
    d.text((40,28),m["target"].replace("Cytomegalovirus-US28","Cytomegalovirus US28"),font=F(48),fill='black')
    cv.paste(Image.fromarray(lane),(40,110));zx=40+lane.shape[1]+50;zy=110+200
    d.text((zx,zy-64),"The band, enlarged",font=F(36),fill='black');cv.paste(Image.fromarray(zc),(zx,zy));d.rectangle([zx-3,zy-3,zx+cw*Z+2,zy+ch*Z+2],outline=(230,0,0),width=4)
    d.text((zx,zy+ch*Z+24),"22 antibodies for 22 different proteins.",font=F(30,False),fill='black');d.text((zx,zy+ch*Z+64),"The band has the same shape in every blot.",font=F(30,False),fill='black')
    frames.append(cv.convert('P',palette=Image.ADAPTIVE,colors=128))
frames[0].save('/home/user/reviews/band_reused_22_blots.gif',save_all=True,append_images=frames[1:],duration=700,loop=0)
print(len(frames),frames[0].size)
