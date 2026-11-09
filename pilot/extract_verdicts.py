import json, sys
def verdicts(path):
    out = None
    for l in open(path):
        try: d = json.loads(l)
        except Exception: continue
        m = d.get("message", {})
        if m.get("role") != "assistant" or not isinstance(m.get("content"), list): continue
        for c in m["content"]:
            if c.get("type") == "tool_use":
                for v in (c.get("input") or {}).values():
                    if isinstance(v, str) and v.strip().startswith("["):
                        try: out = json.loads(v)
                        except Exception: pass
    return out
def prompt(path):
    for l in open(path):
        d = json.loads(l); m = d.get("message", {})
        if m.get("role") == "user":
            c = m["content"]; return c if isinstance(c, str) else c[0].get("text")
if __name__ == "__main__":
    if sys.argv[1] == "prompt": print(prompt(sys.argv[2]))
    else:
        v = verdicts(sys.argv[2]); assert v, "no verdicts"
        json.dump(v, open(sys.argv[3], "w"), indent=1); print(sys.argv[3], len(v))
