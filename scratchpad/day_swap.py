"""Option 1, agreed with Daniel 21 September 2026: swap which run sits on which day.

The uni timetable (docs/uni-timetable.md) has classes on Wed/Thu/Fri only, and
Daniel's rule for a lecture day is "running before, lifting after" - so the
morning run on a lecture day ends at the station, not at home. The easy run
therefore takes the lecture day and the threshold run takes a free one.

    Mon  Quality run + Upper A     (was Lower A)
    Tue  Lower A                   (was Zone 2 + Upper A)
    Wed  Mobility                  unchanged   - lecture 09:00-11:00
    Thu  Zone 2 + Upper B          (was Quality run + Upper B)
    Fri  Lower B                   unchanged   - lecture 14:00-16:00

The quality run gets three days clear of Friday's Lower B; Zone 2 sits two days
after Tuesday's Lower A, which is well past the window where lower-body lifting
hurts an easy run. Upper spacing improves from 2/5 days to 3/4.

DAYS ONLY. No exercise, target, set or note content changes - the run sessions'
notes still describe their old days and are the coach's to rewrite. Nothing
touches logged history: entries carry their own sessionKey and sessionName, so
past sessions keep the day they were actually done on.

Idempotent, and the expected current day is checked, so this refuses to run
against a program that has already moved underneath it.
"""

# key -> (expected current day, new day)
DAYS = {
    "upper1":          ("Tuesday",  "Monday"),    # Upper A
    "lower2":          ("Monday",   "Tuesday"),   # Lower A
    "runDaniel":       ("Thursday", "Monday"),    # Quality run: Daniel
    "runCerys":        ("Thursday", "Monday"),    # Quality run: Cerys
    "cardioEndurance": ("Tuesday",  "Thursday"),  # Zone 2: Daniel
    "easyCerys":       ("Tuesday",  "Thursday"),  # Zone 2: Cerys
}


def apply_to_program(program):
    """Move the days in place. Returns a list of human-readable changes."""
    sessions = program.get("sessions") or {}
    changed, already = [], []

    missing = [k for k in DAYS if k not in sessions]
    if missing:
        raise SystemExit("!! sessions missing from the program: %s" % ", ".join(missing))

    for key, (expect, new) in DAYS.items():
        s = sessions[key]
        cur = str(s.get("day") or "").strip()
        if cur == new:
            already.append("%s (%s) already on %s" % (s.get("name"), key, new))
            continue
        if cur != expect:
            raise SystemExit(
                "!! %s (%s) is on %s, expected %s - the program has moved on, "
                "re-read it before running this" % (s.get("name"), key, cur, expect))
        s["day"] = new
        changed.append("%-22s %-9s -> %s" % (s.get("name"), cur, new))

    for line in already:
        changed.append("(no change) " + line)
    return changed


def week(program):
    """The resulting week, day by day, in program.order - what the app opens first."""
    order = program.get("order") or list((program.get("sessions") or {}).keys())
    sessions = program["sessions"]
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "Optional"]
    out = []
    for d in days:
        on = [(k, sessions[k]) for k in order
              if k in sessions and str(sessions[k].get("day") or "").strip() == d]
        if on:
            out.append((d, on))
    return out
