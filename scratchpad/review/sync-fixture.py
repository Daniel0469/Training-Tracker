"""Writes the shared fixture that proves the app's toRecords / fromRecords (js/app.js) give the same
rows as mcp-coach/tt_records.py.

    python scratchpad/review/sync-fixture.py                      writes scratchpad/review/sync-parity.json
    python scratchpad/review/sync-fixture.py --input data.json --out out.json
                                                                  maps a real copy of the store too

The output is {"cases": [{name, now, input, prev, rows, payload}]}: `rows` is to_records(input) and
`payload` is from_records(rows). sync-cases.js runs the JS mapping on `input` and compares. --records
names the folder that holds tt_records.py (default mcp-coach next to this repo's root).
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
NOW = 1793700000000


def ex(name, sets=3):
    return {"name": name, "warmup": "", "target": f"{sets}x8", "sets": sets, "cols": ["Weight (kg)", "Reps"]}


def program(pid, members, version, updated, names):
    return {"id": pid, "members": members, "version": version, "updatedAt": updated, "updatedBy": members[0] if members else "",
            "order": ["a", "b"], "sessions": {"a": {"name": names[0], "day": "Monday", "exercises": [ex("Bench press")]},
                                              "b": {"name": names[1], "day": "Thursday", "exercises": [ex("Squat", 5)]}}}


def synthetic():
    new_shape = {
        "people": ["Alex", "", "Sam"], "weights": ["80", "", 72.5], "goals": ["squat 100", "", ""],
        "programs": {"p-alex": program("p-alex", ["Alex"], 4, "2026-11-01T10:00:00.123Z", ["Upper", "Lower"]),
                     "p-sam": program("p-sam", ["Sam"], 1, "2026-11-02T08:30:15.123456Z", ["Full", "Legs"])},
        "programIds": {"Alex": {"id": "p-alex", "updatedAt": 1793600000000}, "Sam": {"id": "p-sam", "updatedAt": 0}},
        "logs": [{"id": 1793000000001, "person": "Alex", "date": "2026-10-30", "updatedAt": 1793000500000, "entries": []},
                 {"id": 1793000000002, "person": "Sam", "date": "2026-10-31", "entries": [{"name": "Squat", "rows": [["60", "8"]]}]},
                 {"id": 1793000000003, "date": "2026-11-01"}, {"person": "Alex", "date": "no id"}, "not a log"],
        "bodyweights": [{"person": "Alex", "date": "2026-11-01", "kg": 80.2, "updatedAt": 1793600000123},
                        {"person": "Sam", "date": "2026-11-01", "kg": 72.5}, {"person": "Sam", "kg": 1}],
        "measurements": [{"person": "Alex", "date": "2026-10-01", "waist": 82, "updatedAt": "2026-10-01T09:00:00Z"}],
        "meals": [{"id": "m-1", "person": "Alex", "name": "Oats", "kcal": 350, "updatedAt": 1793650000000}, {"id": 7, "name": "No owner"}],
        "suggestions": [{"id": 11, "person": "Sam", "text": "more legs", "status": "done", "updatedAt": 1793000000000,
                         "doneAt": "2026-11-02T10:00:00Z", "approvedAt": 1793100000000}],
        "programChanges": [{"id": "pe-abc", "kind": "person", "programId": "p-alex", "from": "Sam", "createdAt": "2026-11-02T12:00:00.000Z",
                            "status": "pending", "at": "2026-11-02T12:00:00.000Z"}],
        "coachQuestions": {"Alex": [{"id": 5, "question": "Sleep?", "updatedAt": 1793500000000}, {"question": "no id"}, "x"], "Sam": "not a list"},
        "coaching": {"Alex": {"notes": "ok", "updated": "2026-11-01T00:00:00Z"}, "Sam": "plain text"},
        "hrZones": {"Alex": {"max": 190}}, "racePredictions": {"Alex": [1, 2, 3]},
        "machineSettings": {"Alex": {"Leg press": {"text": "seat 4", "updatedAt": 1793400000000}}},
        "progression": {"Sam": {"on": {"value": False, "updatedAt": 1793300000000}}},
        "features": {}, "nutritionTargets": {"Alex": {"kcal": 2800, "protein": 160, "updatedAt": 1793200000000}},
        "limiters": {"Alex": None}, "wellness": {"Alex": {"2026-11-01": {"sleep": 80}}},
        "adminPin": {"salt": "s", "hash": "h", "updatedAt": 1793100000000},
        "deletedLogs": [1793000000099, 1793000000003], "deletedBodyweights": [{"person": "Alex", "date": "2026-09-01", "deletedAt": 1793000000000},
                                                                              {"person": "Sam", "date": "2026-09-02"}, {"person": "Sam"}],
        "deletedMeals": [{"id": "m-0", "deletedAt": 1793000100000}, {"id": 8}],
    }
    old_shape = {
        "version": 1, "people": ["Alex", "Sam"], "weights": ["80", ""], "goals": ["", "get fit"],
        "program": {"order": ["a"], "version": "3", "updatedAt": "2026-10-20T10:00:00Z",
                    "sessions": {"a": {"name": "Full body", "exercises": [ex("Row")]}}},
        "logs": [{"id": 5, "person": "Alex", "date": "2026-10-20"}], "deletedLogs": [], "deletedBodyweights": [], "deletedMeals": [],
    }
    unmatched = {"people": ["Alex", "Sam"], "programs": {"p-1": program("p-1", ["Alex", "Sam"], 2, "", ["A", "B"])}, "programIds": {"Alex": {"id": "gone"}}}
    blank = {"people": ["", ""], "logs": [], "programs": {}, "programIds": {}}
    prev_rows = [{"kind": "person", "key": "Sam", "person": "Sam", "body": {"slot": 4, "extra": 1}, "updated_at": 0, "deleted_at": None},
                 {"kind": "log", "key": "1793000000099", "person": None, "body": {"id": 1793000000099}, "updated_at": 0, "deleted_at": 1793111111111},
                 {"kind": "log", "key": "1793000000003", "person": None, "body": {"id": 1793000000003}, "updated_at": 0, "deleted_at": 1793222222222}]
    return [("new shape", new_shape, None), ("new shape with a previous sync", new_shape, prev_rows),
            ("old shape", old_shape, None), ("program that no person names", unmatched, None), ("blank install", blank, None)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", help="a data.json shaped file to map as well")
    ap.add_argument("--out", default=os.path.join(HERE, "sync-parity.json"))
    ap.add_argument("--records", default=os.path.join(ROOT, "mcp-coach"))
    args = ap.parse_args()
    sys.path.insert(0, args.records)
    import tt_records
    cases = synthetic()
    if args.input:
        with open(args.input, encoding="utf-8") as f:
            cases = [("input file", json.load(f), None)]
    out = []
    for name, data, prev_rows in cases:
        prev = tt_records.snapshot(prev_rows) if prev_rows else None
        rows = tt_records.to_records(data, now=NOW, prev=prev)
        out.append({"name": name, "now": NOW, "input": data, "prev": prev_rows, "rows": rows,
                    "payload": tt_records.from_records(rows)})
    times = ["2026-11-01T10:00:00.123Z", "2026-11-01", "2026-11-01T10:00:00", "2026-11-01T10:00", "2026-11-01 10:00:00+01:00",
             "2026-11-01T10:00:00.1234567Z", "", "nope", 12.9, -5.5, None, True, 1793700000000]
    times += [f"2026-{m:02d}-{d:02d}T{h:02d}:{(h * 7) % 60:02d}:{(d * 11) % 60:02d}.{(m * 137 + d * 11 + h) % 1000:03d}Z"
              for m in range(1, 13) for d in (1, 9, 17, 28) for h in (0, 13, 23)]
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"cases": out, "ms": [[t, tt_records._ms(t)] for t in times]}, f, indent=1, ensure_ascii=False)
    print(f"wrote {len(out)} case(s), {sum(len(c['rows']) for c in out)} rows, to {args.out}")


if __name__ == "__main__":
    main()
