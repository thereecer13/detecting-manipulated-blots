import sys,json;sys.path.insert(0,'gif')
from reg import *
from PIL import Image,ImageDraw,ImageFont
FB=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',48)
def eq_box(g,box):
    l,r,t,b=box;inner=g[t:b,l:r]
    cdf=np.bincount(inner.ravel(),minlength=256).cumsum();cdf=cdf/cdf[-1]
    lut=np.clip(cdf*255,0,255).astype(np.uint8);out=g.copy();out[t:b,l:r]=lut[g[t:b,l:r]];return out
def find_marker(g,lane_right):
    # short dark horizontal dash just right of the lane frame
    reg=(g[:,lane_right+4:lane_right+70]<110).astype(np.uint8)
    n,lab,st,_=cv2.connectedComponentsWithStats(reg)
    c=[st[i] for i in range(1,n) if 12<=st[i][2]<=45 and st[i][3]<=9]
    if not c: return None
    x,y,w,h,_=max(c,key=lambda s:s[2]);return lane_right+4+x,y,w,h
def arrowize(g,lane_right):
    m=find_marker(g,lane_right)
    if m is None: return g,None
    x,y,w,h=m;g=g.copy();g[y-2:y+h+2,x-2:x+w+3]=255
    im=Image.fromarray(g);d=ImageDraw.Draw(im);cy=y+h/2;x0=lane_right+10
    d.line([(x0+6,cy),(x0+42,cy)],fill=0,width=3);d.polygon([(x0,cy),(x0+12,cy-6),(x0+12,cy+6)],fill=0)
    return np.asarray(im),(x,y,w,h)
def build(items,title,box,out):
    fr=[]
    for g in items:
        e=eq_box(g,box);a=Image.fromarray(g);b=Image.fromarray(e)
        W=a.width*2+30;H=a.height+76
        c=Image.new('L',(W,H),255);c.paste(a,(0,76));c.paste(b,(a.width+30,76));d=ImageDraw.Draw(c)
        tw=d.textlength(title,font=FB);d.text(((W-tw)/2,10),title,fill=0,font=FB)
        fr.append(c)
    # one shared palette (greyscale) so frames do not flicker
    pal=[];[pal.extend((i,i,i)) for i in range(256)]
    P=[]
    for f in fr:
        p=f.convert('P');p.putpalette(pal);p=Image.frombytes('P',f.size,f.tobytes());p.putpalette(pal);P.append(p)
    P[0].save(out,save_all=True,append_images=P[1:],duration=900,loop=0,optimize=False,disposal=1)
