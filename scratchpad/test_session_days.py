"""Offline test for sessions on several days in the coach server. Touches nothing but a local copy.

_github_update is monkeypatched to run the mutation against a small in-memory program, so no
network call or token is needed.

    python scratchpad/test_session_days.py
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "mcp-coach"))
import server  # noqa: E402

EX = [{"name": "Easy run", "target": "30:00", "sets": 1, "cols": ["Distance (km)", "Time (mm:ss)", "Pace"]}]
DATA = {"people": ["Daniel", "Cerys"], "program": {"order": ["old", "run"], "sessions": {
    "old": {"name": "Upper A", "day": "Tuesday", "exercises": []},
    "run": {"name": "Run: Daniel", "day": "Tuesday", "days": ["Tuesday", "Friday"], "person": "Daniel",
            "autoPick": {"Tuesday": True, "Friday": True}, "exercises": EX}}}}
FAILS = []
server._github_update = lambda mutate, message, attempts=3: mutate(DATA)
server.load_data = lambda: DATA


def check(label, got, want):
    ok = got == want
    print(("  ok   " if ok else "  FAIL ") + label + ("" if ok else f"\n         got {got!r}\n         want {want!r}"))
    if not ok:
        FAILS.append(label)


check("days of a session with a list", server._days_of(DATA["program"]["sessions"]["run"]), ["Tuesday", "Friday"])
check("days of an old session", server._days_of(DATA["program"]["sessions"]["old"]), ["Tuesday"])
check("days of an Optional session", server._days_of({"day": "Optional"}), [])
check("parse several days in week order", server._parse_days("friday, Tuesday"), ["Tuesday", "Friday"])
check("parse Optional", server._parse_days("Optional"), [])
try:
    server._parse_days("Someday")
    check("parse a word that is no weekday", "no error", "ValueError")
except ValueError:
    check("parse a word that is no weekday", "ValueError", "ValueError")

check("which= a second day finds the session", server._find_run_session(DATA, "Daniel", "friday")[0], "run")
check("get_run reports the days", server.get_run(DATA, "Daniel")["days"], ["Tuesday", "Friday"])
check("get_program_session finds a session by a day it is on", server.get_program_session(DATA, "friday")["session"], "Run: Daniel")

r = server.add_session("Mobility", "Wednesday, Sunday", [])
s = DATA["program"]["sessions"][r["key"]]
check("add_session writes days and day is the first", (s["days"], s["day"]), (["Wednesday", "Sunday"], "Wednesday"))
r = server.add_session("Later", "Optional", [])
s = DATA["program"]["sessions"][r["key"]]
check("add_session Optional has no days", (s["days"], s["day"]), ([], "Optional"))
check("add_session refuses a bad day", "not a weekday" in str(server.add_session("Bad", "Someday", []).get("error", "")), True)

res = server.set_run("Daniel", day="Thursday")
s = DATA["program"]["sessions"]["run"]
check("set_run moves the days", (s["days"], s["day"], res.get("ok")), (["Thursday"], "Thursday", True))
check("set_run drops an auto-pick on a day it no longer has", s.get("autoPick"), None)

print("\n%d failed" % len(FAILS) if FAILS else "\nall passed")
sys.exit(1 if FAILS else 0)
