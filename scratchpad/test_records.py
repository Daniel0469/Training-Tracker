"""Round trip: from_records(to_records(store copy)) must equal the store copy.

    python scratchpad/test_records.py

Run against the newest scratchpad/data-backup-*.json (a copy, never the live store). Lists
that hold records (logs, meals, suggestions...) are compared as sets: the table has no row
order. Empty containers and missing keys count as equal, and `exportedAt` is not stored.
"""
import copy, glob, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "mcp-coach"))
import tt_records

NOT_STORED = {"exportedAt"}
ORDERED_LISTS = {"people", "weights", "goals"}


def canon(data):
    out = {}
    for k, v in data.items():
        if k in NOT_STORED or v in ({}, [], None):
            continue
        if isinstance(v, list) and k not in ORDERED_LISTS:
            v = sorted(v, key=lambda x: json.dumps(x, sort_keys=True))
        if k == "coachQuestions":
            v = {p: sorted(q, key=lambda x: json.dumps(x, sort_keys=True)) for p, q in v.items()}
        out[k] = v
    return out


def latest_store():
    return sorted(glob.glob(os.path.join(ROOT, "scratchpad", "data-backup-*.json")))[-1]


def load_store():
    with open(latest_store(), encoding="utf-8") as f:
        return json.load(f)


def with_every_kind(data):
    """The store copy has no coach questions, features, progression or family PIN, and no weigh-in
    or meal tombstones, so add one of each to prove those kinds round trip too."""
    d = copy.deepcopy(data)
    d["coachQuestions"] = {"Daniel": [{"id": "cq-01", "question": "q", "updatedAt": 5},
                                      {"id": "cq-02", "question": "r", "updatedAt": 6}],
                           "Cerys": [{"id": "cq-01", "question": "s", "updatedAt": 7}]}
    d["features"] = {"Daniel": {"progression": {"on": True, "updatedAt": 9}}}
    d["progression"] = {"Cerys": {"on": {"value": True, "updatedAt": 3}, "ex": {"Squat": {"updatedAt": 4}}}}
    d["adminPin"] = {"salt": "s", "hash": "h", "updatedAt": 11}
    d["nutritionTargets"] = {"Daniel": {"kcal": 2500, "updatedAt": 2}}
    d["measurements"] = [{"person": "Daniel", "date": "2026-10-01", "waist": 80, "updatedAt": 1}]
    d["deletedBodyweights"] = [{"person": "Cerys", "date": "2026-09-01", "deletedAt": 55}]
    d["deletedMeals"] = [{"id": "meal-x", "deletedAt": 66}]
    return d


def wrapped(old):
    """The store copy as the app writes it now: one program wrapped as shared by the people, the
    way wrapProgram in js/app.js does it, with programIds and `program` as the first person's."""
    d = copy.deepcopy(old)
    names = [p for p in d["people"] if p]
    prog = dict(d["program"], id="p-" + "-".join(n.lower() for n in names), members=names, version=1)
    d["programs"] = {prog["id"]: prog}
    d["programIds"] = {n: {"id": prog["id"], "updatedAt": 0} for n in names}
    d["program"] = prog
    return d


def round_trip(data):
    return canon(tt_records.from_records(tt_records.to_records(data, now=1)))


def test_round_trip_old_shape_is_wrapped():
    store = load_store()
    assert round_trip(store) == canon(wrapped(store))


def test_round_trip_new_shape():
    new = wrapped(load_store())
    new["programs"]["p-extra"] = {"id": "p-extra", "members": [], "version": 4, "updatedAt": "2026-10-01T00:00:00.000Z",
                                  "order": ["a"], "sessions": {"a": {"name": "A", "exercises": []}}}
    new["programIds"]["Cerys"] = {"id": "p-extra", "updatedAt": 77}
    assert round_trip(new) == canon(new)


def test_round_trip_every_kind():
    data = with_every_kind(load_store())
    assert round_trip(data) == canon(wrapped(data))


def test_rows_survive_json():
    rows = tt_records.to_records(with_every_kind(load_store()), now=1)
    assert tt_records.from_records(json.loads(json.dumps(rows))) == tt_records.from_records(rows)


def test_each_person_is_pointed_at_a_program():
    rows = tt_records.to_records(load_store(), now=1)
    programs = [r for r in rows if r["kind"] == "program"]
    assert [r["key"] for r in programs] == ["p-daniel-cerys"]
    assert programs[0]["body"]["members"] == ["Daniel", "Cerys"] and programs[0]["body"]["version"] == 1
    refs = {r["key"]: r["body"]["programId"] for r in rows if r["kind"] == "person"}
    assert refs == {"Daniel": "p-daniel-cerys", "Cerys": "p-daniel-cerys"}


def test_prog_of_reads_either_shape():
    store = load_store()
    new = tt_records.from_records(tt_records.to_records(store, now=1))
    assert tt_records.prog_of(store, "Cerys")["sessions"] == store["program"]["sessions"]
    assert tt_records.prog_of(new, "Cerys") is new["programs"]["p-daniel-cerys"]
    assert tt_records.prog_of(new, "Nobody")["sessions"] == store["program"]["sessions"]


def test_coach_files_and_log_become_rows():
    files = {"Daniel/profile.md": "# Daniel\n", "Daniel/decisions.md": "x\n"}
    log = [{"id": 1788000000000, "date": "2026-09-01", "person": "Daniel", "overall": "hi"}]
    rows = tt_records.to_records({}, coach_files=files, coaching_log=log, now=1)
    parts = tt_records.coach_parts(rows)
    assert parts == (files, log)
    assert tt_records.from_records(rows)["logs"] == []


def test_a_second_family_keeps_its_own_program():
    other = json.loads(json.dumps(load_store()).replace("Daniel", "Alex").replace("Cerys", "Sam"))
    rows = tt_records.to_records(load_store(), now=1) + tt_records.to_records(other, now=1, slot_offset=2)
    assert sorted(r["key"] for r in rows if r["kind"] == "program") == ["p-alex-sam", "p-daniel-cerys"]
    data = tt_records.from_records(rows)
    assert data["people"] == ["Daniel", "Cerys", "Alex", "Sam"]
    assert data["program"] is data["programs"]["p-daniel-cerys"]
    snap = tt_records.snapshot(rows)
    assert tt_records.plan_writes(tt_records.to_records(data, prev=snap, now=1), snap, "t", now=1) == []


def test_server_copies_are_identical():
    with open(os.path.join(ROOT, "mcp-coach", "tt_records.py"), "rb") as a, \
         open(os.path.join(ROOT, "mcp-garmin", "tt_records.py"), "rb") as b:
        assert a.read() == b.read()


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("ok  ", name)
            except Exception as e:
                failed += 1
                print("FAIL", name, type(e).__name__, str(e)[:300])
    print("store copy:", os.path.basename(latest_store()))
    sys.exit(1 if failed else 0)
