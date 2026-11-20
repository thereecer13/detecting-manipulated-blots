"""Re-run the matcher on the papers of a scan that had hits (their figures are still on disk).

    python3 rescore.py OUTDIR [dark 0/1]     rewrites OUTDIR/papers.jsonl in place
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import photo_dupes as P
out = Path(sys.argv[1]); dark = (sys.argv[2] == "1") if len(sys.argv) > 2 else True
recs = [json.loads(l) for l in (out / "papers.jsonl").open()]
for d in recs:
    if d["hits"]:
        d["area"], d["hits"] = P.paper([out / "figs" / f["file"] for f in d["figs"]], dark)
(out / "papers.jsonl").write_text("".join(json.dumps(d) + "\n" for d in recs))
print(sum(1 for d in recs if d["hits"]), "papers with hits", sum(len(d["hits"]) for d in recs), "hits")
