#!/usr/bin/env python3
"""Read-only: what the per-second detail series actually carries, and what the
speed trace looks like as a step function. Writes nothing."""
import sys, os, importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("ttg", os.path.join(ROOT, "mcp-garmin", "server.py"))
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)
G._load_server_env(sys.argv[1]); G._ensure_ca_bundle()

aid = sys.argv[2]
d = G.garmin_client().get_activity_details(aid, maxchart=2000, maxpoly=0)
descs = d.get("metricDescriptors") or []
print("metrics available:")
for m in sorted(descs, key=lambda m: m.get("metricsIndex", 0)):
    print("   %-32s idx=%s" % (m.get("key"), m.get("metricsIndex")))

s = G.fetch_detail_series(aid)
print("\nsamples: %d  span: %.0fs" % (len(s), s[-1][0]-s[0][0] if s else 0))
# print the trace as levels, 20s buckets, to see the step function
print("\nspeed trace (20s buckets, km/h):")
buck, cur, out = 20, None, []
for t, kmh, hr in s:
    b = int(t//buck)
    if cur is None or b != cur[0]:
        if cur: out.append((cur[0]*buck, sum(cur[1])/len(cur[1]), sum(cur[2])/len(cur[2]) if cur[2] else None))
        cur = [b, [], []]
    cur[1].append(kmh)
    if hr is not None: cur[2].append(hr)
if cur: out.append((cur[0]*buck, sum(cur[1])/len(cur[1]), sum(cur[2])/len(cur[2]) if cur[2] else None))
for t, kmh, hr in out:
    bar = "#" * int(round(kmh*2))
    print("  %5ds %5.1f %-32s hr=%s" % (t, kmh, bar, int(hr) if hr else "-"))
