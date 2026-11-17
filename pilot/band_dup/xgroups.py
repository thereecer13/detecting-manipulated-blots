"""Group verified cross-blot band matches into sets of products that show the same band.
  python3 xgroups.py XDIR   (run from the scratch dir; writes XDIR/groups.json and prints a summary)"""
import json,re,csv,sys,glob
from collections import Counter,defaultdict
X=sys.argv[1];M=json.load(open(X+'/bands.json'))['meta'];V=json.load(open(X+'/verified.json'))
tg={}
for f in glob.glob('icc_all/wb/scraped.jsonl')+glob.glob('scraped_*/scraped.jsonl'):
    for l in open(f):
        try:d=json.loads(l)
        except: continue
        s=d.get('product_url','').split('/product/')[-1].split('/')[0];tg[d['catalog']]=re.split(r'-Antibody|-Recombinant|-Monoclonal|-Polyclonal',s)[0]
norm=lambda c:re.sub(r'[^a-z0-9]','',tg.get(c,c).lower())
richcat=set();richband=set()
for f in('raw/rich/260605_catch_all_spreadsheet.csv','raw/rich_aug/260825_catch_all_spreadsheet.csv'):
    for r in csv.DictReader(open(f,encoding='utf-8',errors='replace')):
        richcat.add(r['catalog_number'].strip())
        if re.search(r'same band|band shape is unusually similar',r['summary'],re.I): richband.add(r['catalog_number'].strip())
def prod(m): return re.sub(r'[^A-Z0-9]','',m['name'].upper()).startswith(re.sub(r'[^A-Z0-9]','',m['cat'].upper()))
def stamp(n):
    m=re.search(r'(20\d{2})(\d{2})(\d{2})\d{4,6}',n.replace('_',''));return '%s-%s-%s'%m.groups() if m else 'no date'
A=[v for v in V if M[v[0]]['name']!=M[v[1]]['name'] and M[v[0]]['cat']!=M[v[1]]['cat'] and not v[4]['scaled'] and v[4]['nrmse']<=0.03 and v[4]['outline']>=0.94 and prod(M[v[0]]) and prod(M[v[1]])]
same=[v for v in A if norm(M[v[0]]['cat'])==norm(M[v[1]]['cat'])];A=[v for v in A if norm(M[v[0]]['cat'])!=norm(M[v[1]]['cat'])]
print(len(A),'different-target pairs;',len(same),'same-target pairs set aside')
par={}
def f(x):
    while par.setdefault(x,x)!=x: par[x]=par[par[x]];x=par[x]
    return x
for v in A: par[f(M[v[0]]['name'])]=f(M[v[1]]['name'])
g=defaultdict(set)
for x in list(par): g[f(x)].add(x)
byname=defaultdict(list)
for i,m in enumerate(M): byname[m['name']].append(i)
G=[]
for s in g.values():
    pr=[v for v in A if M[v[0]]['name'] in s]
    ctx=sorted(v[4]['ctx'] for v in pr if v[4]['ctx'] is not None)
    mem={}
    for v in pr:
        for i in(0,1):
            m=M[v[i]];mem.setdefault(m['name'],dict(band=v[i],cat=m['cat'],target=tg.get(m['cat'],'?'),date=stamp(m['name']),listed=m['cat'] in richcat,name=m['name'],path=m['path'],url=m['url'],box=m['box']))
    G.append(dict(members=list(mem.values()),pairs=[[v[0],v[1],v[3],v[4]['nrmse'],v[4]['ctx']] for v in pr],ctx_med=ctx[len(ctx)//2] if ctx else None,
                  n_unlisted=len({m['cat'] for m in mem.values() if not m['listed']}),n_products=len({m['cat'] for m in mem.values()}),rich_band=any(m['cat'] in richband for m in mem.values())))
G.sort(key=lambda x:(-x['n_unlisted'],-x['n_products']))
json.dump(G,open(X+'/groups.json','w'))
print(len(G),'groups;',sum(x['n_unlisted']>0 for x in G),'include a product not in Richardson;',sum(x['n_unlisted']==x['n_products'] for x in G),'entirely unlisted')
print('products:',len({m['cat'] for x in G for m in x['members']}),'unlisted:',len({m['cat'] for x in G for m in x['members'] if not m['listed']}))
print('listed-only groups flagged by Richardson for the band:',sum(x['rich_band'] for x in G if x['n_unlisted']==0),'of',sum(x['n_unlisted']==0 for x in G))
for x in G:
    if x['n_unlisted']: print(x['n_products'],x['n_unlisted'],x['ctx_med'] is not None and round(x['ctx_med'],2),'; '.join('%s %s %s%s'%(m['cat'],m['target'][:18],m['date'],'' if not m['listed'] else ' [R]') for m in x['members'][:6]))
