"""Read-only look at the live store for the 22 Oct answers (warm-up headers, retired coach cards)."""
import os, json, importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
g = importlib.util.spec_from_file_location("ttg", os.path.join(ROOT, "mcp-garmin", "server.py"))
G = importlib.util.module_from_spec(g); g.loader.exec_module(G); G._load_server_env("training-tracker")
c = importlib.util.spec_from_file_location("ttc", os.path.join(ROOT, "mcp-coach", "server.py"))
C = importlib.util.module_from_spec(c); c.loader.exec_module(C)
d, *_ = C._github_read_with_sha()
S = d["program"]["sessions"]
names = {s["name"] for s in S.values()}
for k, s in S.items():
    print(k, "|", s["name"], "|", (s.get("warmupNote") or "").splitlines()[:1])
print("top keys:", list(d.keys()))
co = d.get("coaching") or {}
for p, v in co.items():
    bs = (v or {}).get("by_session") or {}
    print(p, "by_session keys:", list(bs.keys()))
    print(p, "retired:", [k for k in bs if k not in names])
for p, v in co.items():
    print(p, type(v).__name__, list(v.keys())[:20] if isinstance(v, dict) else v)
    for kk, vv in (v.items() if isinstance(v, dict) else []):
        if isinstance(vv, dict): print("  ", kk, "->", list(vv.keys()))
