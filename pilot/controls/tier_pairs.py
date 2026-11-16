import json,re,datetime,collections,sys
SP='/tmp/claude-0/-home-user/d3491ae8-cca5-5e56-9093-18710041e4bb/scratchpad/'
d=json.load(open('/home/user/detecting-manipulated-blots/pilot/controls/confirmed_pairs.json'))
cap={}
for f in ['icc_all/media.jsonl','media_all.jsonl','ctrl_sample/media.jsonl']:
    try:
        for l in open(SP+f):
            try: r=json.loads(l)
            except: continue
            if r.get('url'): cap[r['url']]=(r.get('description') or '')
    except FileNotFoundError: pass
SPEC={'A32790':'rabbit','A27034':'rabbit','A32731':'rabbit','A32794':'rabbit','A11008':'rabbit','A11034':'rabbit','A21206':'rabbit',
      'A32766':'mouse','A32723':'mouse','A28175':'mouse','A32787':'mouse','A11001':'mouse','A11029':'mouse','A21202':'mouse','A32814':'goat','A11055':'goat'}
rx=re.compile(r'(?:using|in) (?:\d+ ?% confluent log phase )?([\w\-:\.,/ ]+?) (?:cells|treated|cell line)')
STOP=re.compile(r'(was performed using|paraformaldehyde fixed|\d+ ?%? confluent log phase|confluent|log phase|fixed|untreated)',re.I)
KNOWN=['mdamb231','shsy5y','u87mg','hela','a431','mcf7','a549','hepg2','t47d','u2os','hek293','bewo','thp1','caco2','daudi','raw264','ovcar3','c2c12','hct116','u937','jurkat','ntera2','skbr3','ht1080','k562','hacat','nih3t3','sknsh','ht29','lncap','du145','pc12','vero']
ALIAS={'raw264':'raw2647','sknsh':'sknsh'}
EXACT={'c6','pc3','3t3','293t','293'}
def cells(c):
    n=re.sub(r'[^a-z0-9]','',c.lower());out=set()
    for k in KNOWN:
        if k in n: out.add(ALIAS.get(k,k))
    if 'hek293' in out: pass
    elif re.search(r'\b(?:HEK-?)?293T?\b',c): out.add('hek293')
    if re.search(r'\bC6\b',c): out.add('c6')
    if re.search(r'\bPC-?3\b',c): out.add('pc3')
    if re.search(r'\b3T3\b',c) and 'nih3t3' not in out: out.add('nih3t3')
    return out
def secs(c):
    return {SPEC[a] for a in re.findall(r'\b(A\d{5})\b',c) if a in SPEC}
def stamp(u):
    m=re.search(r'-(20\d{2})(\d{2})(\d{2})[\d_]*\.jpg$',u)
    if m:
        try: return datetime.date(*map(int,m.groups()))
        except ValueError: pass
    m=re.search(r'-(20\d{2})(\d)(\d{2})\d{6}\.jpg$',u)   # 2021923125244 style (single-digit month)
    if m:
        try: return datetime.date(*map(int,m.groups()))
        except ValueError: pass
    return None
OVR={frozenset(('PA5-28622','PA5-40698')):'label conflict: "No Primary antibody" vs "BeWo (Negative)"'}
rows=[]
for x in d:
    ca,cb=cap.get(x['a_url'],''),cap.get(x['b_url'],'')
    A=dict(cells=cells(ca),sec=secs(ca),date=stamp(x['a_url']));B=dict(cells=cells(cb),sec=secs(cb),date=stamp(x['b_url']))
    why=[]
    if A['cells'] and B['cells'] and not (A['cells']&B['cells']): why.append(f"cell lines {sorted(A['cells'])} vs {sorted(B['cells'])}")
    if A['sec'] and B['sec'] and not (A['sec']&B['sec']): why.append(f"secondary anti-{'/'.join(sorted(A['sec']))} vs anti-{'/'.join(sorted(B['sec']))}")
    o=OVR.get(frozenset((x['a'],x['b'])))
    if o: why.append(o)
    known=(A['cells'] and B['cells']) or (A['sec'] and B['sec'])
    gap=abs((A['date']-B['date']).days) if A['date'] and B['date'] else None
    if why and any(w.startswith(('cell','label')) for w in why): t='1a captions contradict: cell line or label'
    elif why: t='1b captions contradict: secondary antibody species only'
    elif not known: t='4 undetermined (caption details missing)'
    elif gap is None: t='4 undetermined (no upload stamp)'
    elif gap<=7: t='3 plausible batch control'
    else: t='2 probable reuse'
    rows.append(dict(tier=t,why='; '.join(why),gap_days=gap,a=x['a'],b=x['b'],group=x['group'],
        a_cells=sorted(A['cells']),b_cells=sorted(B['cells']),a_sec=sorted(A['sec']),b_sec=sorted(B['sec']),
        a_date=str(A['date'] or ''),b_date=str(B['date'] or ''),a_url=x['a_url'],b_url=x['b_url']))
json.dump(rows,open(sys.argv[1],'w'),indent=1)
print(collections.Counter(r['tier'] for r in rows))
