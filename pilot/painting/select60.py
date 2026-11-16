import json,random,re,collections,numpy as np,os
from PIL import Image,ImageOps
SP='/tmp/claude-0/-home-user/d3491ae8-cca5-5e56-9093-18710041e4bb/scratchpad/'
def stamp(b):
    m=re.search(r'(20\d{6})[\d_]*\.jpg$',b) or re.search(r'-(20\d{5,6})\d{6}\.jpg$',b)
    return m.group(1) if m else 'none'
N=[d for d in json.load(open(SP+'paint/allneg_f2.json')) if d[5]]
P=[d for d in json.load(open(SP+'paint/allpos_f2.json')) if d[5]]
random.seed(60)
N.sort(key=lambda d:-d[5]['max_patch'])
top=[];cat=set();st=collections.Counter()
for d in N:
    if d[2] in cat or st[stamp(d[0])]>=6: continue
    top.append(d);cat.add(d[2]);st[stamp(d[0])]+=1
    if len(top)==40: break
low=[d for d in N if d[5]['max_patch']==0 and d[5]['lane_px']>0 and d[2] not in cat]
negc=random.sample(low,10)
pst=collections.Counter();posc=[]
for d in random.sample(P,len(P)):
    if pst[stamp(d[0])]>=3: continue
    posc.append(d);pst[stamp(d[0])]+=1
    if len(posc)==10: break
sel=[('top',d) for d in top]+[('richardson_painted',d) for d in posc]+[('low_score',d) for d in negc]
random.shuffle(sel)
os.makedirs(SP+'paint/review',exist_ok=True)
items=[];key=[]
for i,(grp,d) in enumerate(sel):
    g=Image.open(d[1]).convert('L')
    o=SP+f'paint/review/{i:02d}_o.png';e=SP+f'paint/review/{i:02d}_e.png'
    g.save(o);ImageOps.equalize(g).save(e)
    rid=f'P{i:02d}'
    items.append({'id':rid,'label':f'Blot {i+1}','images':[{'path':o,'caption':'original'},{'path':e,'caption':'equalized (whole image)'}]})
    key.append({'id':rid,'group':grp,'file':d[0],'catalog':d[2],'url':d[3],'stamp':stamp(d[0]),'max_patch':d[5]['max_patch'],'patches':d[5]['patches']})
json.dump(items,open(SP+'paint/review_items.json','w'));json.dump(key,open(SP+'paint/review_key.json','w'),indent=1)
print(collections.Counter(k['group'] for k in key),'top max_patch range',top[0][5]['max_patch'],top[-1][5]['max_patch'],'stamps',st.most_common(8))
