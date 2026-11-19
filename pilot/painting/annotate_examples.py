import sys,cv2,numpy as np
sys.path.insert(0,'/home/user/detecting-manipulated-blots/pilot');sys.path.insert(0,'/home/user/detecting-manipulated-blots/pilot/painting')
from views import levels_richardson
from deblock_view import deblock
def make(src,title,out,arrows):
    g=cv2.imread(src,0);e=levels_richardson(deblock(g));S=2;up=lambda x:cv2.cvtColor(cv2.resize(x,None,fx=S,fy=S,interpolation=cv2.INTER_CUBIC),cv2.COLOR_GRAY2BGR)
    A=up(g);B=up(e)
    for (x0,y0,x1,y1) in arrows: cv2.arrowedLine(B,(x0*S,y0*S),(x1*S,y1*S),(0,0,255),4,cv2.LINE_AA,tipLength=0.3)
    def cap(x,t):
        o=np.full((x.shape[0]+50,x.shape[1]+16,3),255,np.uint8);o[50:,8:-8]=x;cv2.putText(o,t,(8,32),cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,0,0),2,cv2.LINE_AA);return o
    row=np.hstack([cap(A,'Original'),cap(B,'Contrast enhanced; arrows: edges of painted area')])
    head=np.full((56,row.shape[1],3),255,np.uint8);cv2.putText(head,title,(8,38),cv2.FONT_HERSHEY_SIMPLEX,1.0,(0,0,0),2,cv2.LINE_AA)
    cv2.imwrite(out,np.vstack([head,row]))
make('review4/33_o.png','MA5-32069 CD8 alpha (Thermo Fisher)','/home/user/reviews/MA5-32069_CD8_annotated.png',
     [(130,330,72,330),(190,640,150,690),(290,420,315,478),(150,450,100,492)])
make('review4/55_o.png','PA5-119659 SHP-1 (Thermo Fisher)','/home/user/reviews/PA5-119659_SHP1_annotated.png',
     [(300,140,300,198),(370,410,350,358),(240,400,222,350),(290,430,318,468)])
