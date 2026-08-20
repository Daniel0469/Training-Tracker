"""Offline test for the write_run tool's logic. Touches nothing but a local copy.

_github_update is monkeypatched to run the mutation against the prototype state
and hand the result back, so every validation path can be exercised without a
network call or a token.

    python scratchpad/test_write_run.py
"""
import io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "mcp-coach"))
import server  # noqa: E402

DATA = json.load(io.open(os.path.join(HERE, "proto-run-state.json"), encoding="utf-8"))
FAILS = []


def fake_update(mutate, message, attempts=3):
    """Run the mutation against our in-memory copy, exactly as the real one does."""
    return mutate(DATA)


server._github_update = fake_update
server.load_data = lambda: DATA


def check(label, got, want):
    ok = got == want
    print(("  ok   " if ok else "  FAIL ") + label + ("" if ok else f"\n         got {got!r}\n         want {want!r}"))
    if not ok:
        FAILS.append(label)


print("read: run_session(Daniel)")
cur = server.get_run(DATA, "Daniel")
check("finds Daniel's session", cur["session"], "Run: Daniel")
check("and its exercises", [e["name"] for e in cur["exercises"]],
      ["Run reps", "Easy jog", "Plank pull through", "Russian twists"])
check("Cerys has her own", server.get_run(DATA, "Cerys")["session"], "Run: Cerys")

print("\nrefusals")
check("unknown person", server.set_run("Nobody", [{"name": "x", "target": "y", "sets": 1,
      "cols": ["a", "b"]}])["ok"], False)
r = server.set_run("Daniel", [])
check("empty exercise list", (r["ok"], "non-empty" in r["error"]), (False, True))
r = server.set_run("Daniel", [{"name": "", "target": "t", "sets": 1, "cols": ["a", "b"]}])
check("nameless exercise", (r["ok"], "no name" in r["error"]), (False, True))
r = server.set_run("Daniel", [{"name": "Run reps", "target": "t", "sets": 1, "cols": ["only one"]}])
check("bad columns", (r["ok"], "column names" in r["error"]), (False, True))
r = server.set_run("Daniel", [{"name": "Run reps", "target": "t", "sets": 99, "cols": ["a", "b"]}])
check("silly set count", (r["ok"], "1-30" in r["error"]), (False, True))
check("no-op write", server.set_run("Daniel", cur["exercises"])["ok"], False)
check("nothing was written by any refusal",
      [e["name"] for e in server.get_run(DATA, "Daniel")["exercises"]],
      ["Run reps", "Easy jog", "Plank pull through", "Russian twists"])

print("\na real re-prescription: hill repeats, a format neither session has used")
new = [
    {"name": "Run reps", "target": "6 x 400m @ 11.5 km/h, 4% incline, 90s walk", "sets": 6,
     "cols": ["Distance (km)", "Time (mm:ss)", "Pace"], "garminRun": True,
     "notes": "Incline is the progression this week, not the speed."},
    {"name": "Easy jog", "target": "12 min easy", "sets": 1,
     "cols": ["Distance (km)", "Time (mm:ss)", "Pace"]},
    {"name": "Plank pull through", "target": "3x15-20", "sets": 3,
     "cols": ["Weight (kg)", "Reps"], "groupId": "grp-run-core"},
    {"name": "Russian twists", "target": "3x10-15", "sets": 3,
     "cols": ["Weight (kg)", "Reps"], "groupId": "grp-run-core"},
]
res = server.set_run("Daniel", new, why="You held 4x800 at 11.0 with no fade, so the flat "
                     "rep is done telling us things. Same speed, add the hill.")
check("write accepted", res["ok"], True)
check("changed the exercises", res["changed"], ["exercises"])
check("new target is live", server.get_run(DATA, "Daniel")["exercises"][0]["target"],
      "6 x 400m @ 11.5 km/h, 4% incline, 90s walk")
check("previous came back for a revert", res["previous"]["exercises"][0]["target"],
      "4 x 800m @ 11.0 km/h, 90s walk")
check("why became the session's coach note",
      DATA["coaching"]["Daniel"]["bySession"]["Run: Daniel"][:20], "You held 4x800 at 11")
check("and went into the coaching history",
      DATA["coachingLog"][-1]["bySession"]["Run: Daniel"][:9], "You held ")
check("program stamped so the phones adopt it", DATA["program"]["updatedAt"][-1], "Z")
check("Cerys untouched", server.get_run(DATA, "Cerys")["exercises"][0]["target"],
      "6 x 400m @ 11.0 km/h, 90s walk")

print("\nreverting with what came back")
back = server.set_run("Daniel", res["previous"]["exercises"], why="Reverted.")
check("revert accepted", back["ok"], True)
check("target is back", server.get_run(DATA, "Daniel")["exercises"][0]["target"],
      "4 x 800m @ 11.0 km/h, 90s walk")

print("\nnotes and rename still work")
r = server.set_run("Cerys", warmup="10 min, active.\n\n- Easy cardio - 5 min")
check("warm-up note written", r["changed"], ["warmupNote"])
r = server.set_run("Daniel", name="Cardio: Endurance + Core")
check("a rename onto the backup session's name is refused",
      (r["ok"], "must be unique" in r["error"]), (False, True))
check("a genuine rename still works",
      server.set_run("Daniel", name="Run: Daniel (hyrox)")["changed"], ["name"])

print("\n" + ("FAILED: " + ", ".join(FAILS) if FAILS else "all checks passed"))
sys.exit(1 if FAILS else 0)
