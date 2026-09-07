#!/usr/bin/env python3
"""Run garmin_refresh_metrics from a FRESH process, so it picks up the current
mcp-garmin/server.py rather than whatever the long-running MCP server loaded at
startup. Same function the tool exposes - no separate write path.

Backs the store up next to this script first, and prints a before/after diff of
everything it changed, so nothing lands unseen.

    python scratchpad/run_refresh.py training-garmin Daniel
"""
import sys, os, json, copy, datetime, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("ttg", os.path.join(ROOT, "mcp-garmin", "server.py"))
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)

server, person = sys.argv[1], sys.argv[2]
G._load_server_env(server); G._ensure_ca_bundle()

before, _sha, _u, _t = G._github_read_with_sha()
stamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
backup = os.path.join(ROOT, "scratchpad", "data-backup-%s.json" % stamp)
json.dump(before, open(backup, "w", encoding="utf-8"), indent=1)
print("backed up ->", os.path.basename(backup))

old = {str(l.get("id")): copy.deepcopy(l) for l in before.get("logs", []) if l}

res = G.refresh_metrics(person)
print("\n%s\n" % res.get("message"))

after, _sha, _u, _t = G._github_read_with_sha()
for l in after.get("logs", []):
    if not l or l.get("person") != person:
        continue
    o = old.get(str(l.get("id")))
    if not o or o == l:
        continue
    print("=" * 70)
    print("%s  %s" % (l.get("date"), l.get("sessionName")))
    og, ng = (o.get("garmin") or {}), (l.get("garmin") or {})
    orep, nrep = og.get("reps") or {}, ng.get("reps") or {}
    if orep != nrep:
        print("   reps  %s -> %s" % (orep.get("count"), nrep.get("count")))
        print("     was: %s" % [x.get("sec") for x in orep.get("reps", [])])
        print("     now: %s" % [x.get("sec") for x in nrep.get("reps", [])])
        print("     derived was: %s" % json.dumps(orep.get("derived")))
        print("     derived now: %s" % json.dumps(nrep.get("derived")))
    for k in sorted(set(og) | set(ng)):
        if k in ("reps",) or og.get(k) == ng.get(k):
            continue
        print("   %-14s %s -> %s" % (k, json.dumps(og.get(k))[:70], json.dumps(ng.get(k))[:70]))
    for oe, ne in zip(o.get("entries") or [], l.get("entries") or []):
        if oe.get("rows") != ne.get("rows"):
            print("   ROWS on %s" % ne.get("name"))
            print("     was: %s" % oe.get("rows"))
            print("     now: %s" % ne.get("rows"))
print("\ndone - backup is %s if any of that needs putting back" % os.path.basename(backup))
