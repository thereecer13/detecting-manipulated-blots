"""Download figures (and the article XML, for captions) of open-access papers matching a Europe PMC
query, from PMC's open-data bucket on AWS (pmc-oa-opendata, intended for bulk text and data mining).

    python pilot/fetch_pmc_figures.py --query '"colony formation assay"' --n 500 --out pmc_colony [--seed 1]

Europe PMC REST is used only to list matching PMCIDs (open access, full text). Papers are sampled at
random from the first --pool hits. One request per --delay seconds; resumable.
"""
import argparse, json, random, re, time, urllib.parse, urllib.request
from pathlib import Path

UA = "blot-integrity-research/0.1 (academic image-integrity study; low-rate)"
S3 = "https://pmc-oa-opendata.s3.amazonaws.com"
_last = [0.0]


def get(url, delay):
    w = delay - (time.time() - _last[0])
    if w > 0: time.sleep(w)
    _last[0] = time.time()
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=120) as r:
        return r.read()


def pmcids(query, pool, delay):
    q = urllib.parse.quote(f"({query}) AND OPEN_ACCESS:Y AND HAS_FT:Y")
    out, cursor = [], "*"
    while len(out) < pool:
        d = json.loads(get(f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={q}&format=json&pageSize=1000&resultType=lite&cursorMark={urllib.parse.quote(cursor)}", delay))
        out += [(r["pmcid"], r.get("title"), r.get("journalTitle"), r.get("pubYear"), r.get("doi")) for r in d["resultList"]["result"] if r.get("pmcid")]
        if d.get("nextCursorMark") in (None, cursor): break
        cursor = d["nextCursorMark"]
    return out[:pool]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--query", required=True); ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--pool", type=int, default=20000); ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=1); ap.add_argument("--delay", type=float, default=1.0)
    a = ap.parse_args(); (a.out / "papers").mkdir(parents=True, exist_ok=True)
    plan_f = a.out / "plan.json"
    if plan_f.exists(): plan = json.loads(plan_f.read_text())
    else:
        ids = pmcids(a.query, a.pool, a.delay); random.Random(a.seed).shuffle(ids); plan = ids[:a.n]
        plan_f.write_text(json.dumps(plan, indent=1))
    for i, (pmcid, title, journal, year, doi) in enumerate(plan):
        d = a.out / "papers" / pmcid
        if (d / "done").exists(): continue
        d.mkdir(exist_ok=True)
        try:
            lst = get(f"{S3}/?list-type=2&prefix={pmcid}.&max-keys=200", a.delay).decode()
            keys = re.findall(r"<Key>([^<]+)</Key>", lst)
            for k in keys:
                if re.search(r"\.(jpg|jpeg|png|gif|tif)$", k, re.I) or k.endswith(".xml"):
                    p = d / k.split("/")[-1]
                    if not p.exists(): p.write_bytes(get(f"{S3}/{urllib.parse.quote(k)}", a.delay))
            (d / "meta.json").write_text(json.dumps({"pmcid": pmcid, "title": title, "journal": journal, "year": year, "doi": doi, "keys": keys}))
            (d / "done").write_text("")
            print(f"  [{i + 1}/{len(plan)}] {pmcid} {len(keys)} files", flush=True)
        except Exception as e:
            print("  fail", pmcid, str(e)[:80], flush=True)


if __name__ == "__main__":
    main()
