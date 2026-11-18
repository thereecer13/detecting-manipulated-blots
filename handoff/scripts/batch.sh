#!/bin/bash
# usage: bash batch.sh N   (N = shared-panel run number; blot dir = crawlscan$((N-1)))
set -u; N=$1; C=crawlscan$((N-1)); P=/home/user/detecting-manipulated-blots/pilot
mkdir -p $C; python3 -I - $C <<'E'
import json,glob,sys
C=sys.argv[1]; done=set()
for f in glob.glob('crawlscan*/scraped.jsonl'):
    if not f.startswith(C+'/'): done|={json.loads(l)['file'] for l in open(f) if l.strip()}
L=[l for l in open('icc_all/wb/scraped.jsonl') if l.strip() and json.loads(l)['file'] not in done]
open(C+'/scraped.jsonl','w').writelines(L); print(len(L),'new blots')
E
ln -sfn ../icc_all/wb/images $C/images
(python3 -I $P/template_scan2.py scan --richardson raw/rich_aug --scraped $C --out $C/scan_t2.json --jobs 2 2>/dev/null | head -1; python3 -I $P/pattern_a.py scan $C --members scraped_members --member-list patA/members_A.txt --out $C/scan_a.json --jobs 2 2>&1 | sed -n 2,5p) > $C/log.txt 2>&1 &
timeout 6600 python3 -I -W ignore $P/shared_panels.py icc_all/index.jsonl ctrl_all/index.jsonl --images icc_all/images ctrl_all/images --out sp/run$N.json --jobs 3 2>&1 | sed -n 1,3p
python3 -I - $N <<'E'
import json,sys,hashlib
N=int(sys.argv[1]); k=lambda p: frozenset((p["a"]["file"],p["b"]["file"]))
old=set()
for i in range(1,N):
    r=json.load(open(f"sp/run{i}.json")); old|={k(p) for p in (r["pairs"] if isinstance(r,dict) else r)}
r=json.load(open(f"sp/run{N}.json")); new=[p for p in r["pairs"] if k(p) not in old]
json.dump(new,open(f"sp/run{N}_new.json","w"),indent=1)
from collections import Counter; print(len(r["pairs"]),"pairs,",len(new),"new", Counter(p["tier"] for p in new))
for p in new:
    if p["tier"]!="dark: generic hub": print(p["tier"],p["score"],p["detail"],p["a"]["catalog"],p["a"]["target"][:30],"|",p["b"]["catalog"],p["b"]["target"][:30])
E
wait; cat $C/log.txt
python3 -I - $C <<'E'
import json,re,sys
C=sys.argv[1]; flag=set()
for f in ("raw/rich/260605_catch_all_spreadsheet.csv","raw/rich_aug/260825_catch_all_spreadsheet.csv"):
    flag|=set(re.findall(r"\b(?:PA5|MA5|PA1|MA1)-\d+\b",open(f,errors="ignore").read()))
r=json.load(open(C+"/scan_t2.json")); hits=[x for x in r if (x.get("share") or 0)>=0.15]
cats={x['catalog'] for x in hits}; print(len(cats),"template hit products; unlisted:")
for x in hits:
    if x['catalog'] not in flag: print(x['catalog'],round(x['share'],3),x['pattern'],x['exemplar'],x['path'])
E
