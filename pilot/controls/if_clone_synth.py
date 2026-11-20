import json,random,sys,io,cv2,numpy as np
from PIL import Image
sys.path.insert(0,'/home/user/detecting-manipulated-blots/pilot/controls')
import if_clone as I
B=I.B
def band(g): return cv2.GaussianBlur(g,(0,0),1.0)-cv2.GaussianBlur(g,(0,0),4.0)
def ncc(rgb,f):
    g=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY).astype(np.float32);b=band(g);x,y,w,h=f['bbox'];dx,dy=f['shift']
    m=np.zeros(g.shape,np.uint8);cv2.fillPoly(m,[np.array(f['outline'],np.int32)],1);m=m[y:y+h,x:x+w]>0
    a=b[y:y+h,x:x+w][m];c=b[y+dy:y+dy+h,x+dx:x+dx+w]
    if c.shape!=(h,w) or m.sum()<20: return None
    c=c[m];a=a-a.mean();c=c-c.mean();return float((a*c).sum()/max(np.sqrt((a*a).sum()*(c*c).sum()),1e-6)),float(a.std())
if __name__=='__main__':
    D=json.load(open('if_clone/pilot.json'));random.seed(5);clean=[r for r in D if r.get('found')==[]];out=[]
    for r in random.sample(clean,120):
        rgb=np.asarray(Image.open('icc_all/images/'+r['file']).convert('RGB')).copy();H,W=rgb.shape[:2];g=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
        s=random.choice([28,40,56]);ok=False
        for _ in range(200):
            x=random.randrange(0,W-s);y=random.randrange(0,H-s)
            if g[y:y+s,x:x+s].mean()>40 and g[y:y+s,x:x+s].std()>12: ok=True;break
        if not ok: continue
        for _ in range(200):
            dx=random.randint(-150,150);dy=random.randint(-150,150)
            if 0<=x+dx<W-s and 0<=y+dy<H-s and abs(dx)>s and abs(dy)>8: break
        else: continue
        mk=np.zeros((s,s),np.float32);cv2.circle(mk,(s//2,s//2),s//2-2,1,-1);mk=cv2.GaussianBlur(mk,(0,0),1.5)[...,None]
        rgb[y+dy:y+dy+s,x+dx:x+dx+s]=(mk*rgb[y:y+s,x:x+s]+(1-mk)*rgb[y+dy:y+dy+s,x+dx:x+dx+s]).astype(np.uint8)
        buf=io.BytesIO();Image.fromarray(rgb).save(buf,'JPEG',quality=85);rgb2=np.asarray(Image.open(buf).convert('RGB'))
        g2=cv2.cvtColor(rgb2,cv2.COLOR_RGB2GRAY).astype(np.float32);v=np.ones(g2.shape,bool);F=B.verify(rgb2,g2,v,B.candidates(g2,v))
        hit=[f for f in F if abs(abs(f['shift'][0])-abs(dx))<=2 and abs(abs(f['shift'][1])-abs(dy))<=2]
        out.append({'s':s,'hit':bool(hit),'area':hit[0]['area'] if hit else 0,'ncc':ncc(rgb2,hit[0]) if hit else None,'other':len(F)-len(hit)})
    json.dump(out,open('if_clone/synth.json','w'))
    for s in (28,40,56):
        o=[x for x in out if x['s']==s];print(s,len(o),'found',sum(x['hit'] for x in o),'median area',np.median([x['area'] for x in o if x['hit']] or [0]),'ncc',np.round(np.percentile([x['ncc'][0] for x in o if x['hit'] and x['ncc']] or [0],[10,50,90]),2))
    # same measure on the real pilot hits
    nc=[]
    for r in D:
        for f in r.get('found') or []:
            if min(abs(f['shift'][0]),abs(f['shift'][1]))>3:
                v=ncc(np.asarray(Image.open('icc_all/images/'+r['file']).convert('RGB')),f)
                if v: nc.append((round(v[0],2),f['area'],r['catalog']))
    print('pilot oblique hits ncc:',sorted(nc,reverse=True)[:30])
