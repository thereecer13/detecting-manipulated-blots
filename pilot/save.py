"""Save compact judge answers: lines 'id M|L p [x0,y0,x1,y1;...]' -> JSON in test2/runs/<cond>/<batch>.json"""
import json, sys
cond, batch = sys.argv[1], sys.argv[2]
out = []
for l in sys.stdin.read().strip().splitlines():
    parts = l.split()
    i, v, p = parts[:3]; r = parts[3] if len(parts) > 3 else "-"
    out.append({"id": i, "verdict": "manipulated" if v == "M" else "legitimate", "probability_manipulated": float(p),
                "regions": [] if r == "-" else [list(map(float, b.split(","))) for b in r.split(";")]})
json.dump(out, open(f"test2/runs/{cond}/{batch}.json", "w")); print(cond, batch, len(out))
