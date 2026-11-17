import json,csv,re,hashlib,random,sys,os,glob,numpy as np
sys.path.insert(0,'band')
from bandlib import load,search_copies
from render import render
from collections import Counter
random.seed(46)
o=json.load(open('band/all_out.json'));it={i[0]:i for i in json.load(open('band/all_items.json'))}
rich={}
for f in('raw/rich/260605_catch_all_spreadsheet.csv','raw/rich_aug/260825_catch_all_spreadsheet.csv'):
    for r in csv.DictReader(open(f,encoding='utf-8',errors='replace')):
        rich.setdefault(r['original_image_filename'].strip(),[]).append(r['summary'])
def stamp(n):
    m=re.search(r'(20\d{6})\d{4,6}',n.replace('_',''));return m.group(1) if m else ('pub' if n.startswith('tfs_') else 'none:'+n[:9])
def geom_ok(hh,pad=4):
    x,y,w,h=hh[3];lx,ly=hh[4];pw,ph=w+2*pad,h+2*pad
    if w<30 or h<10: return False
    return abs(lx-(x-pad))>=pw or abs(ly-(y-pad))>=ph   # A and B do not overlap
def pix_ok(path,hh):
    """Reject chart bars: one flat mid-grey fills the 'band'."""
    g=load(path);x,y,w,h=hh[3];P=g[y:y+h,x:x+w];v,c=np.unique(P,return_counts=True);i=c.argmax()
    return not (c[i]/P.size>0.3 and v[i]>30)
cand=[]
for r in o:
    for hh in r[2]:
        if geom_ok(hh): cand.append((hh[0],r[0],hh));break
cand.sort();print(len(cand),sum(c[0]<=0.03 for c in cand))
sel=[];seen=set();cnt=Counter();cats=set();rej=0
for x in cand:
    i=it[x[1]];md=hashlib.md5(open(i[1],'rb').read()).hexdigest();st=stamp(x[1]);key=re.sub(r'-?AV-?','',x[1])
    if md in seen or key in seen or i[2] in cats: continue
    if not st.startswith('none') and cnt[st]>=5: continue
    if not pix_ok(i[1],x[2]): rej+=1;continue
    seen|={md,key};cats.add(i[2]);cnt[st]+=1
    sel.append({'kind':'top','name':x[1],'path':i[1],'cat':i[2],'url':i[3],'hit':x[2],'rich':rich.get(x[1])})
    if len(sel)==49:break
print('bars rejected',rej,'last nrmse',sel[-1]['hit'][0],cnt.most_common(8))
rc=json.load(open('band/rich_cases.json'));n=0
for c in rc:
    if not c.get('have'):continue
    g=load(c['path']);B,res=search_copies(g)
    res=[[r[0],r[1],r[2],list(r[3]),list(r[4])] for r in res];res=[r for r in res if geom_ok(r)]
    if res and res[0][0]<=0.08 and n<5:
        sel.append({'kind':'rich','name':c['file'],'path':c['path'],'cat':c['cat'],'hit':res[0],'rich':[c['summary']]});n+=1
neg=[x for x in cand if 0.10<=x[0]<=0.16 and x[1] not in rich]
for x in random.sample(neg,40):
    i=it[x[1]]
    if len(sel)==60:break
    if pix_ok(i[1],x[2]): sel.append({'kind':'neg','name':x[1],'path':i[1],'cat':i[2],'url':i[3],'hit':x[2],'rich':None})
print(Counter(s['kind'] for s in sel))
random.shuffle(sel)
for f in glob.glob('band/review/*'):os.remove(f)
items=[];key={}
for k,s in enumerate(sel):
    pre=os.path.abspath(f'band/review/{k:02d}');render(s['path'],s['hit'],pre)
    vt={'same':'as is','hflip':'mirrored left-right','vflip':'flipped top-bottom','rot180':'rotated 180 degrees'}[s['hit'][2]]
    items.append({'id':f'B{k:02d}','label':f'Blot {k+1} (B matches A {vt})','images':[{'path':pre+'_o.png','caption':'original'},{'path':pre+'_m.png','caption':'A = band, B = closest match elsewhere'},{'path':pre+'_z.png','caption':'enlarged; difference is flat grey where A and B are identical'}]})
    key[f'B{k:02d}']=s
json.dump(items[:30],open('band/review_items_1.json','w'));json.dump(items[30:],open('band/review_items_2.json','w'));json.dump(key,open('band/review_key.json','w'),indent=1)
print(Counter(stamp(s['name']) for s in sel if s['kind']=='top').most_common(6), sum(1 for s in sel if s['kind']=='top' and s['rich']))
