import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
def panels(im):
    g=im.min(2);white=g>=250
    cols=np.where(white.mean(0)<0.5)[0];rows=np.where(white.mean(1)<0.3)[0]
    def runs(ix):
        out=[];s=ix[0];p=ix[0]
        for v in ix[1:]:
            if v!=p+1: out.append((s,p+1));s=v
            p=v
        out.append((s,p+1));return [r for r in out if r[1]-r[0]>40]
    return runs(rows),runs(cols)
def get(path):
    im=cv2.imread(path);R,C=panels(im);R=[(4,215),(219,430)];C=[(4,215),(219,430)]
    return im[R[1][0]:R[1][1],C[0][0]:C[0][1]],im[R[1][0]:R[1][1],C[1][0]:C[1][1]]
A=get('icc_all/images/2b049af07707.jpg');B=get('icc_all/images/b274d372464f.jpg')
S=3;up=lambda x:cv2.cvtColor(cv2.resize(x,(160*S,160*S),interpolation=cv2.INTER_CUBIC),cv2.COLOR_BGR2RGB)
gap=24;left=20;top=10;rowlab=110;W=left+2*160*S+gap+left;H=top+2*(160*S+rowlab)-20
cv=Image.new('RGB',(W,H),'white');d=ImageDraw.Draw(cv)
def font(sz,bold=True):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',):
        try: return ImageFont.truetype(p,sz)
        except Exception: pass
    return ImageFont.load_default()
def ctext(x,y,t,f,fill='black'):
    w=d.textlength(t,font=f);d.text((x-w/2,y),t,font=f,fill=fill)
c1=left+80*S;c2=left+160*S+gap+80*S
pass
for i,(pair,lab) in enumerate(((A,'Antibody A: caption says HeLa cells'),(B,'Antibody B: caption says MCF7 cells'))):
    y=top+i*(160*S+rowlab)
    d.text((left,y+14),lab,font=font(36),fill='black')
    cv.paste(Image.fromarray(up(pair[0])),(left,y+70));cv.paste(Image.fromarray(up(pair[1])),(left+160*S+gap,y+70))
    d.rectangle([left+160*S+gap-4,y+66,left+2*160*S+gap+3,y+70+160*S+3],outline=(255,200,0),width=6)
cv.save('/home/user/reviews/no_primary_control_reuse_example.png');print(cv.size)
