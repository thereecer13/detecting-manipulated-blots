"""Compare flow plots across different figures of the same paper.

  python3 cross_fig.py PANELS.json FIGS.jsonl FIGDIR OUT.json [--jobs 3]
PANELS.json comes from facs_panels.py (used to know which figures hold flow plots).
"""
import sys, os, json, collections
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import panelmatch as pm
import facs_panels as fpn

FIGDIR = None


def run(job):
    pmcid, files = job
    out = []
    try:
        P = {}
        for f in files:
            P[f] = fpn.find_panels(Image.open(os.path.join(FIGDIR, f)))
        for i, fa in enumerate(files):
            for fb in files[i + 1:]:
                for a in P[fa]:
                    for b in P[fb]:
                        r = pm.match_dots(a['_pts'], b['_pts'], scales=fpn.SC)
                        if r['score'] >= 8:
                            r.update(pmcid=pmcid, fa=fa, fb=fb, a=a['box'], b=b['box'])
                            out.append(r)
    except Exception as e:
        out.append({'pmcid': pmcid, 'error': repr(e)})
    return out


if __name__ == '__main__':
    from multiprocessing import Pool
    panels, meta, FIGDIR, outp = sys.argv[1:5]
    jobs = int(sys.argv[sys.argv.index('--jobs') + 1]) if '--jobs' in sys.argv else 3
    has = {r['file'] for r in json.load(open(panels)) if r['panels']}
    by = collections.defaultdict(list)
    for l in open(meta):
        d = json.loads(l)
        if d.get('file') in has:
            by[d['pmcid']].append(d['file'])
    todo = [(k, sorted(set(v))) for k, v in by.items() if len(set(v)) >= 2]
    print('papers with flow plots in 2+ figures:', len(todo), flush=True)
    with Pool(jobs) as P:
        res = [x for o in P.imap_unordered(run, todo) for x in o]
    json.dump(res, open(outp, 'w'))
    ok = [r for r in res if 'score' in r]
    print('pairs scoring >= 8:', len(ok), '; with M-S >= 20:', sum(r['M'] - r['S'] >= 20 for r in ok),
          '; papers:', len({r['pmcid'] for r in ok if r['M'] - r['S'] >= 20}), '; errors', sum('error' in r for r in res))
