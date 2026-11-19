import sys,cv2,numpy as np
sys.path.insert(0,'/home/user/detecting-manipulated-blots/pilot');sys.path.insert(0,'/home/user/detecting-manipulated-blots/pilot/painting')
from views import levels_richardson,blot_mask_v2
from deblock_view import deblock
def make(src,out,S=2,pad=14,gap=28):
    g=cv2.imread(src,0);e=levels_richardson(deblock(g));m=blot_mask_v2(g)
    ys,xs=np.where(g<235);x0,x1,y0,y1=max(xs.min()-pad,0),min(xs.max()+pad,g.shape[1]),max(ys.min()-pad,0),min(ys.max()+pad,g.shape[0])
    mx=np.where(m.any(0))[0];bc=((mx.min()+mx.max())/2-x0)*S      # blot centre within the cropped panel
    up=lambda x:cv2.cvtColor(cv2.resize(x[y0:y1,x0:x1],None,fx=S,fy=S,interpolation=cv2.INTER_CUBIC),cv2.COLOR_GRAY2BGR)
    def cap(x,t):
        fs=x.shape[1]/620;hh=int(54*fs);o=np.full((x.shape[0]+hh,x.shape[1],3),255,np.uint8);o[hh:]=x
        (tw,th),_=cv2.getTextSize(t,cv2.FONT_HERSHEY_SIMPLEX,fs,max(2,int(2.3*fs)));tx=int(min(max(bc-tw/2,4),x.shape[1]-tw-4))
        cv2.putText(o,t,(tx,int(38*fs)),cv2.FONT_HERSHEY_SIMPLEX,fs,(0,0,0),max(2,int(2.3*fs)),cv2.LINE_AA);return o
    A=cap(up(g),'Original');B=cap(up(e),'Contrast enhanced')
    cv2.imwrite(out,np.hstack([A,np.full((A.shape[0],gap,3),255,np.uint8),B]))
make('review4/33_o.png','/home/user/reviews/MA5-32069_CD8_original_enhanced.png')
make('review4/55_o.png','/home/user/reviews/PA5-119659_SHP1_original_enhanced.png')
