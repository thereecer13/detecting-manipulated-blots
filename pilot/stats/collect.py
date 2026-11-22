"""Confirmed publications from the repo's results files -> confirmed.json [{pmcid, kind}]"""
import json, re, glob
P='/home/user/detecting-manipulated-blots/pilot/'; out={}
def add(pm,kind): out.setdefault(pm,kind)
for f in sorted(glob.glob(P+'photo_reuse/*_results.json')):
    scan='cell' if '/cell_' in f else 'bli'
    for i in json.load(open(f)):
        if i['verdict'].startswith('same image'): add(i['pmcid'], 'Cell-assay image' if scan=='cell' else 'Animal imaging scan')
for i in json.load(open(P+'colony/review2_results.json')):
    if i['verdict'].startswith('same plate, shown'): add(i['pmcid'],'Colony plate')
for i in json.load(open(P+'colony/review3to7_results.json')):
    if i['verdict']=='real duplicate': add(i['pmcid'],'Colony plate')
for i in json.load(open(P+'colony/review_results.json'))['items']:
    if i['verdict'].startswith('same plate, shown'): add(re.search(r'PMC\d+',i['label']).group(0),'Colony plate')
for k,v in json.load(open(P+'facs/confirmed_key.json')).items(): add(v['pmcid'],'Flow cytometry plot')
json.dump([{"pmcid":k,"kind":v} for k,v in out.items()],open('confirmed.json','w'),indent=0)
import collections; print(len(out),collections.Counter(out.values()))
