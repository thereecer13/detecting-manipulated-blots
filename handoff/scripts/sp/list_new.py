import json,re,sys
N=int(sys.argv[1])
new=json.load(open(f'sp/run{N}_new.json'))
conf=json.load(open('/home/user/detecting-manipulated-blots/pilot/controls/confirmed_pairs.json'))
cc=set()
for c in conf: cc|={c['a'],c['b']}
old=set()
for i in range(1,N):
    try:d=json.load(open(f'sp/run{i}.json'))
    except Exception:continue
    for p in (d['pairs'] if isinstance(d,dict) else d): old.add(p['a']['file']);old.add(p['b']['file'])
norm=lambda s:re.sub(r'phospho|-','',(s or '').lower()).strip()[:5]
seen=set();sel=[]
for p in new:
    if p['tier'].startswith('dark: generic hub'):continue
    k=(p['a']['file'],p['a']['k'],p['b']['file'],p['b']['k'])
    if k in seen:continue
    seen.add(k)
    if norm(p['a']['target'])==norm(p['b']['target']) and '?' not in (p['a']['target'],p['b']['target']):continue
    sel.append(p);f=lambda s:('F' if s['file'] in old else '-')+('C' if s['catalog'] in cc else '-')
    print(len(sel)-1,round(p['score'],2),p['tier'][:14],'|',p['a']['catalog'],p['a']['target'][:22],p['a']['k'],f(p['a']),'|',p['b']['catalog'],p['b']['target'][:22],p['b']['k'],f(p['b']))
json.dump(sel,open(f'sp/sel{N}.json','w'))
