#!/bin/bash
# FACS scale-up: fetch PMC papers in chunks of 1000, detect flow panels, match, and drop figures without flow panels.
R=/home/user/detecting-manipulated-blots/pilot/facs
for k in "$@"; do
  d=pmcbig/c$k; mkdir -p $d
  [ -f $d/done ] && continue
  python3 -I $R/fetch_pmc.py --out $d --n 1000 --start $((k*1000)) > $d/fetch.log 2>&1
  python3 -I -W ignore $R/facs_panels.py $d/figs $d/panels.json --jobs 2 > $d/panels.log 2>&1
  python3 -I -W ignore $R/cross_fig.py $d/panels.json $d/figs.jsonl $d/figs $d/cross.json --jobs 2 > $d/cross.log 2>&1
  python3 -I -W ignore within2.py $d > $d/within.log 2>&1
  python3 -I - $d <<'P'
import json,os,sys
d=sys.argv[1];keep={x['file'] for x in json.load(open(d+'/panels.json')) if x['panels']};n=0
for f in os.listdir(d+'/figs'):
    if f not in keep: os.remove(d+'/figs/'+f);n+=1
print('kept',len(keep),'removed',n)
P
  touch $d/done; echo "chunk $k done $(date -u +%H:%M)"
done
