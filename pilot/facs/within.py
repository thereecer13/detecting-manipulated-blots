import json,sys
sys.path.insert(0,'/home/user/detecting-manipulated-blots/pilot/facs')
import figscan
from PIL import Image
from multiprocessing import Pool
def run(x):
    out=[]
    try:
        im=Image.open('pmc/figs/'+x['file']).convert('RGB')
        for k,p in enumerate(x['panels']):
            b=p['box']; r=figscan.scan(im.crop((b[0],b[1],b[2]+1,b[3]+1)),min_dots=15,border=0.04)
            hs=r['hits']
            if hs: out.append({'file':x['file'],'panel':k,'box':b,'hit':hs[0],'ndots':r['ndots']})
    except Exception as e: out.append({'file':x['file'],'error':repr(e)})
    return out
if __name__=='__main__':
    r=[x for x in json.load(open('pmc/panels2.json')) if x['panels']]
    with Pool(3) as P: res=[y for o in P.imap_unordered(run,r,chunksize=4) for y in o]
    json.dump(res,open('pmc/within.json','w'))
    ok=sorted([y for y in res if 'hit' in y],key=lambda y:-y['hit']['score'])
    print(len(ok),'panels with an internal repeat; errors',sum('error' in y for y in res))
    for y in ok[:30]: h=y['hit']; print(round(h['score']),y['file'][:45],y['panel'],h['n'],round(h['frac'],2),h['dx'],h['dy'],h['src'])
    W=Image.new('RGB',(1300,4*220),'grey')
    from PIL import ImageDraw
    for k,y in enumerate(ok[:24]):
        b=y['box']; c=Image.open('pmc/figs/'+y['file']).convert('RGB').crop((b[0],b[1],b[2]+1,b[3]+1)); d=ImageDraw.Draw(c); h=y['hit']
        d.rectangle(h['src'],outline=(255,0,0)); d.rectangle(h['dst'],outline=(0,90,255)); c=c.resize((212,212)); W.paste(c,((k%6)*216,(k//6)*220))
    W.save('pmc/within.png')
