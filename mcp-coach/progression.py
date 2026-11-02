"""Double progression: the weight to aim for next time on a lifting exercise.

Pure functions, mirrored in js/app.js (parseStepLines, progLadder, stepCore, progHistory,
progCore) and checked by the same progression_cases.json. Keep the two in step.
"""
import re

MERGE = 0.3            # typed weights this close are one machine setting
GAP_SAME = 0.5         # step gaps this close are the same gap
LADDER_REACH = 1.5     # the next rung counts only within this many steps
DUMBBELL_BIG = 10      # dumbbells go up by 2 from this weight, by 1 below it
BARBELL = re.compile(r"\b(barbell|deadlift|squat|bench press)\b", re.I)
NOT_BARBELL = re.compile(r"\b(hack|machine|smith|cable|goblet|bulgarian|split|db|dumbbell)\b", re.I)
DUMBBELL = re.compile(r"\b(db|dumbbell|hammer curl)\b", re.I)
LOWER_BODY = ("quads", "glutes", "hamstrings")


def _num(x):
    m = re.match(r"\s*(-?(?:\d+(?:\.\d*)?|\.\d+))", "" if x is None else str(x))
    return float(m.group(1)) if m else None


def _cell(row, i):
    return row[i] if row and len(row) > i else None


def _round2(x):
    return int(x * 100 + 0.5) / 100 if x >= 0 else -int(-x * 100 + 0.5) / 100


def parse_range(target):
    s = str(target or "")
    m = re.search(r"(\d+)\s*x\s*(\d+)(?:\s*-\s*(\d+))?", s, re.I)
    if m:
        return {"low": int(m.group(2)), "high": int(m.group(3) or m.group(2))}
    m = re.search(r"(\d+)\s*[-]\s*(\d+)", s)
    return {"low": int(m.group(1)), "high": int(m.group(2))} if m else None


def parse_step_lines(text):
    """"Step: Seated row = 2.5" lines to {name: step}. A line with anything but one number is ignored."""
    out = {}
    for line in str(text or "").splitlines():
        m = re.match(r"^\s*step:\s*(.+?)\s*=\s*(\d+(?:\.\d+)?)\s*$", line, re.I)
        if m and float(m.group(2)) > 0:
            out[m.group(1)] = float(m.group(2))
    return out


def prog_history(entries, low, assist=False):
    """One summary per logged session, oldest first: the working weight w, how many working
    rows are at it (n), their reps, and whether any working row was a miss."""
    out = []
    for e in entries:
        warm = e.get("warmup") or []
        done = e.get("done")
        rows = [(i, r) for i, r in enumerate(e.get("rows") or []) if i not in warm]
        weights = [w for w in (_num(_cell(r, 0)) for _, r in rows) if w is not None]
        if not weights:
            continue
        w = max(set(weights), key=lambda v: (weights.count(v), -v if assist else v))
        miss = False
        reps = []
        for i, r in rows:
            n = _num(_cell(r, 1))
            if n is None or n < low or (isinstance(done, list) and i not in done):
                miss = True
            if _num(_cell(r, 0)) == w:
                reps.append(n or 0)
        out.append({"w": w, "n": len(reps), "reps": reps, "total": sum(reps), "miss": miss})
    return out


def prog_ladder(weights):
    """The distinct weights a machine has been used at (typed weights within MERGE are one
    setting), and the step between them. The step is the finest gap seen at least twice.
    Confident needs three weights and every gap a whole multiple of the step."""
    counts = {}
    for w in weights:
        counts[w] = counts.get(w, 0) + 1
    groups = []
    for v in sorted(counts):
        if groups and v - groups[-1][-1] <= MERGE:
            groups[-1].append(v)
        else:
            groups.append([v])
    ladder = [max(g, key=lambda v: (counts[v], -v)) for g in groups]
    gaps = sorted(_round2(b - a) for a, b in zip(ladder, ladder[1:]))
    gap_groups = []
    for g in gaps:
        if gap_groups and g - gap_groups[-1][0] <= GAP_SAME:
            gap_groups[-1].append(g)
        else:
            gap_groups.append([g])
    repeated = [g for g in gap_groups if len(g) >= 2]
    if not repeated:
        return {"ladder": ladder, "step": None, "confident": False}
    g = repeated[0]
    mid = len(g) // 2
    step = _round2(g[mid] if len(g) % 2 else (g[mid - 1] + g[mid]) / 2)
    tolerance = max(0.4, 0.15 * step)
    whole = all(int(x / step + 0.5) >= 1 and abs(x - int(x / step + 0.5) * step) <= tolerance for x in gaps)
    return {"ladder": ladder, "step": step, "confident": len(ladder) >= 3 and whole}


def step_for(ex, w, override, pool):
    """The smallest increase to try from weight w, and where that came from: a step line,
    the barbell or dumbbell rule by name, a ladder learned from `pool` (every working
    weight logged on this exercise name by either person), else unknown."""
    name = ex.get("name") or ""
    if override:
        return {"step": override, "source": "line", "ladder": None}
    if BARBELL.search(name) and not NOT_BARBELL.search(name):
        lower = any(m in LOWER_BODY for m in ex.get("muscles") or [])
        return {"step": 5 if lower else 2.5, "source": "barbell", "ladder": None}
    if DUMBBELL.search(name):
        return {"step": 2 if w >= DUMBBELL_BIG else 1, "source": "dumbbell", "ladder": None}
    found = prog_ladder([x for x in pool if x > 0])
    if found["confident"]:
        return {"step": found["step"], "source": "ladder", "ladder": found["ladder"]}
    return {"step": None, "source": None, "ladder": None}


def _next_weight(w, step, ladder, assist):
    """One step up (down for assisted): the next rung of the ladder when it is within reach."""
    sign = -1 if assist else 1
    near = [v for v in ladder or [] if 0 < sign * (v - w) - MERGE and sign * (v - w) <= LADDER_REACH * step + 1e-9]
    if near:
        return min(near) if not assist else max(near)
    return max(0, _round2(w + sign * step))


def _streak(hist):
    n = 1
    while n < len(hist) and hist[-1 - n]["w"] == hist[-1]["w"]:
        n += 1
    return n


def _stalled(hist, streak):
    """Three sessions at one weight and neither of the last two beat the one before it."""
    if streak < 3:
        return False
    a, b, c = hist[-3:]
    return not any(not new["miss"] and new["total"] > old["total"] for old, new in ((a, b), (b, c)))


def _result(status, w=None, target=None, step=None, source=None, streak=0, stalled=False, flag=None, why=None):
    return {"status": status, "w": w, "target": target, "step": step, "source": source,
            "streak": streak, "stalled": stalled, "flag": flag, "why": why}


def _applies(ex):
    """Why the rule does not cover this exercise, or None when it does."""
    cols = ex.get("cols") or ["", ""]
    if not (re.search(r"kg|assist", cols[0], re.I) and re.search(r"rep", cols[1] if len(cols) > 1 else "", re.I)):
        return "not a weight x reps exercise"
    if ex.get("timed"):
        return "timed hold"
    rng = parse_range(ex.get("target"))
    if not rng or rng["low"] >= rng["high"]:
        return "fixed reps"
    return None


def prog_core(entries, ex, ctx):
    why = _applies(ex)
    if why:
        return _result("off", why=why)
    rng = parse_range(ex.get("target"))
    assist = ex.get("load") == "assist"
    hist = prog_history(entries, rng["low"], assist)
    if not hist:
        return _result("none")
    last = hist[-1]
    if last["w"] <= 0 and assist:
        return _result("zero", 0, flag="Ready for load")
    if last["w"] <= 0:
        return _result("off", why="bodyweight")
    streak = _streak(hist)
    due = last["n"] >= ex["sets"] and not last["miss"] and min(last["reps"]) >= rng["high"]
    stalled = not due and _stalled(hist, streak)
    flag = "Stalled" if stalled else None
    found = step_for(ex, last["w"], ctx.get("override"), ctx.get("pool") or [])
    step, source = found["step"], found["source"]
    if not due:
        return _result("hold", last["w"], last["w"], step, source, streak, stalled, flag)
    if step is None:
        return _result("unsure", last["w"], last["w"], streak=streak, flag="Up one step")
    return _result("progress", last["w"], _next_weight(last["w"], step, found["ladder"], assist),
                   step, source, streak)


# ---------------------------------------------------------------- reading the store
def _sessions(data, person=None):
    """The program's sessions as (key, session), leaving out another person's own."""
    return [(k, s) for k, s in ((data.get("program") or {}).get("sessions") or {}).items()
            if s and (not person or s.get("person") in (None, "", person))]


def program_exercises(data, person):
    """Each exercise name once, as (session key, session, exercise), in program order."""
    seen, out = set(), []
    for key, s in _sessions(data, person):
        for ex in s.get("exercises") or []:
            if ex and ex.get("name") and ex["name"] not in seen:
                seen.add(ex["name"])
                out.append((key, s, ex))
    return out


def _logged(data, person, name):
    """(log, entry) for the first entry called `name` in each of the person's logs, oldest first."""
    logs = sorted((l for l in data.get("logs") or [] if l and l.get("person") == person),
                  key=lambda l: (l.get("date") or "", l.get("id") or 0))
    pairs = []
    for l in logs:
        e = next((e for e in l.get("entries") or [] if e.get("name") == name and e.get("rows") is not None), None)
        if e:
            pairs.append((l, e))
    return pairs


def _step_line(data, name, session_key=None):
    """The step line for `name`: from the open session when it has one, else any session."""
    sessions = _sessions(data)
    sessions.sort(key=lambda ks: ks[0] != session_key)
    for _, s in sessions:
        step = parse_step_lines(s.get("setupNote")).get(name)
        if step:
            return step
    return None


def _pool(data, name):
    """Every working weight either person has logged on this exercise name."""
    weights = []
    for person in data.get("people") or []:
        for _, e in _logged(data, person, name):
            warm = e.get("warmup") or []
            weights += [w for i, r in enumerate(e["rows"]) if i not in warm
                        for w in [_num(_cell(r, 0))] if w is not None]
    return weights


def latest_log_id(data, person, name):
    logged = _logged(data, person, name)
    return logged[-1][0].get("id") if logged else None


def coach_target(data, person, name):
    """The coach's target for `name` while it still applies: the person's latest log of it
    is the one it was written against."""
    t = ((((data.get("coaching") or {}).get(person) or {}).get("targets")) or {}).get(name)
    return t if isinstance(t, dict) and t.get("asOfLog") == latest_log_id(data, person, name) else None


def progression_for(data, person, ex, session_key=None):
    """prog_core for one program exercise of one person, from the store."""
    name = ex["name"]
    entries = [e for _, e in _logged(data, person, name)]
    return prog_core(entries, ex, {"override": _step_line(data, name, session_key),
                                   "pool": _pool(data, name)})


def report(data, person):
    """Every weight x reps exercise in the person's program with what the rule says."""
    rows = []
    for _, s, ex in program_exercises(data, person):
        got = progression_for(data, person, ex)
        if got["why"] == "not a weight x reps exercise":
            continue
        row = {"exercise": ex["name"], "session": s.get("name"), **got, "coach": coach_target(data, person, ex["name"])}
        rows.append({k: v for k, v in row.items() if v is not None or k in ("target", "step")})
    return {"person": person, "exercises": rows}
