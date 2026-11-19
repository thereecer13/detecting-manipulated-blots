import json,os,sys
sys.path.insert(0,'band')
from bandlib import load,find_bands
import pair_page
G=json.load(open('band/xall/groups_hi.json'));K=json.load(open('band/review_r4_key.json'))
done=[set(k['group_products']) for k in K.values()];sel=[]
for g in G:
    cats={m['cat'] for m in g['members']}
    if any(cats&d for d in done) or not g['n_unlisted']: continue
    bm={m['band']:m for m in g['members']};best=None
    for p in g['pairs']:
        if p['a'] not in bm or p['b'] not in bm: continue
        a,b=bm[p['a']],bm[p['b']];sd=a['date']==b['date']!='no date';cx=p['ctx'] or 0
        if not(cx>=0.6 or sd): continue
        k=((not a['listed'])+(not b['listed'])>0, cx+(0.3 if sd else 0))
        if best is None or k>best[0]: best=(k,p,a,b,sd)
    if best: sel.append((best,g,cats))
sel.sort(key=lambda t:-(t[0][1]['ctx'] or 0));print(len(sel),'groups')
out='band/review_r5';os.makedirs(out,exist_ok=True);items=[];key={}
for n,((k,p,a,b,sd),g,cats) in enumerate(sel):
    q=f'T{n:02d}'
    try: it,P=pair_page.build(q,a,b,out)
    except Exception as e: print(q,'failed',e);continue
    na,nb=len(find_bands(load(a['path']))),len(find_bands(load(b['path'])))
    f=lambda m:f"{m['cat']} {m['target']} ({m['date']}{', in Richardson' if m['listed'] else ''})"
    more=sorted(cats-{a['cat'],b['cat']})
    it['label']=(f"{f(a)} and {f(b)}. {len(P)} matching band pair(s); the blots have {na} and {nb} bands in total. "
      f"{'Same upload date. ' if sd else ''}Surroundings match {100*(p['ctx'] or 0):.0f}%, {'B resized to A' if p['scaled'] else 'same size'}."
      +(f" {len(more)} more product(s) match the same band: {', '.join(more[:8])}{'…' if len(more)>8 else ''}." if more else ''))
    items.append(it);key[q]={'a':{x:y for x,y in a.items() if x!='path'},'b':{x:y for x,y in b.items() if x!='path'},'pair':p,'band_pairs':P,'group_products':sorted(cats),'n_bands':[na,nb],'same_date':sd}
    print(q,it['label'][:110],flush=True)
json.dump(items,open('band/review_r5_items.json','w'));json.dump(key,open('/home/user/detecting-manipulated-blots/pilot/band_dup/review_r5_key.json','w'),indent=1)
