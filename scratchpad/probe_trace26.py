#!/usr/bin/env python3
"""Read-only: dump one activity's speed trace as blocks and show what the
segmenter makes of it. Written for the 26 Aug float-recovery bug (suggestion
1787791173601). Writes nothing, to Garmin or to the store.

    python scratchpad/probe_trace26.py training-garmin 24130020583 [--buckets]
"""
import sys, os, json, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("ttg", os.path.join(ROOT, "mcp-garmin", "server.py"))
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)
G._load_server_env(sys.argv[1]); G._ensure_ca_bundle()

aid = sys.argv[2]
s = G.fetch_detail_series(aid)
print("samples: %d  span: %.0fs" % (len(s), s[-1][0] - s[0][0] if s else 0))
pts = [(t, k) for t, k, _h, _c in s if k is not None]

if "--buckets" in sys.argv:
    print("\nspeed trace (20s buckets, km/h):")
    buck, cur, out = 20, None, []
    for t, kmh, hr, cad in s:
        if kmh is None:
            continue
        b = int(t // buck)
        if cur is None or b != cur[0]:
            if cur:
                out.append((cur[0] * buck, sum(cur[1]) / len(cur[1]),
                            sum(cur[2]) / len(cur[2]) if cur[2] else None))
            cur = [b, [], []]
        cur[1].append(kmh)
        if hr is not None:
            cur[2].append(hr)
    if cur:
        out.append((cur[0] * buck, sum(cur[1]) / len(cur[1]),
                    sum(cur[2]) / len(cur[2]) if cur[2] else None))
    for t, kmh, hr in out:
        print("  %5ds %5.1f %-40s hr=%s" % (t, kmh, "#" * int(round(kmh * 2)),
                                            int(hr) if hr else "-"))

print("\nclustered speed levels: %s"
      % ", ".join("%.1f" % v for v in G._speed_levels([k for _t, k in pts])))
print("\nblocks:")
for b in G._levels_from_trace(pts, G._LEVEL_MIN_SEC):
    print("   at %5ds  %4ds  %5.1f km/h" % (b["at"], b["sec"], b["kmh"]))

print("\nreps_from_speed_trace:")
print(json.dumps(G.reps_from_speed_trace(s), indent=1))
