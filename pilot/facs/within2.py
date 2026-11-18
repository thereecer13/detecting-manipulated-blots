"""Repeated-dot search inside each flow panel.  python3 within2.py CHUNKDIR"""
import json,sys
sys.path.insert(0,'/home/user/detecting-manipulated-blots/pilot/facs')
import figscan
from PIL import Image
from multiprocessing import Pool
D=sys.argv[1]
def run(x):
    out=[]
    try:
        im=Image.open(D+'/figs/'+x['file']).convert('RGB')
        for k,p in enumerate(x['panels']):
            b=p['box']; r=figscan.scan(im.crop((b[0],b[1],b[2]+1,b[3]+1)),min_dots=15,border=0.04)
            hs=r['hits']
            if hs: out.append({'file':x['file'],'panel':k,'box':b,'hit':hs[0],'ndots':r['ndots']})
    except Exception as e: out.append({'file':x['file'],'error':repr(e)})
    return out
if __name__=='__main__':
    r=[x for x in json.load(open(D+'/panels.json')) if x['panels']]
    with Pool(2) as P: res=[y for o in P.imap_unordered(run,r,chunksize=4) for y in o]
    json.dump(res,open(D+'/within.json','w'));print(len(res),'within hits')
