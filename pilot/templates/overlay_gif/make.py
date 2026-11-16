import sys,json;sys.path.insert(0,'gif')
from reg import *
from PIL import Image,ImageDraw,ImageFont,ImageOps
def eq_masked(O,box):
    l,r,t,b=box;g=np.clip(O,0,255).astype(np.uint8);inner=g[t+3:b-3,l+3:r-3]
    hist=np.bincount(inner.ravel(),minlength=256).astype(float);cdf=hist.cumsum()/hist.sum()
    lut=np.clip(cdf*255,0,255).astype(np.uint8);e=lut[g]
    out=g.copy();out[t:b,l:r]=e[t:b,l:r];return out
try: F=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15);Fs=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
except Exception: F=Fs=ImageFont.load_default()
def frames(R,box,items,title,out,up):
    fr=[]
    for lab,sub,O in items:
        o=np.clip(O,0,255).astype(np.uint8);e=eq_masked(O,box)
        a=Image.fromarray(o).resize((o.shape[1]*up,o.shape[0]*up),Image.BICUBIC);b=Image.fromarray(e).resize(a.size,Image.BICUBIC)
        W=a.width*2+30;H=a.height+70
        c=Image.new('L',(W,H),255);c.paste(a,(0,62));c.paste(b,(a.width+30,62));d=ImageDraw.Draw(c)
        d.text((4,4),lab,fill=0,font=F);d.text((4,24),sub,fill=60,font=Fs);d.text((4,44),'original (aligned)',fill=90,font=Fs);d.text((a.width+34,44),'equalized inside the blot frame',fill=90,font=Fs)
        fr.append(c.convert('P'))
    fr[0].save(out,save_all=True,append_images=fr[1:],duration=[1600]+[900]*(len(fr)-1),loop=0)
    return fr
