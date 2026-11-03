"""Run migrate_to_supabase.py and verify_migration.py against fake_postgrest.py with the store copy.

    python scratchpad/run_migration_check.py

Builds a temporary data.json (the newest scratchpad/data-backup-*.json), a coaching log, coach
files and two family exports (a second family with its own ids, and one whose log ids clash with
the first), then checks: a dry run sends nothing, a migration verifies, a second migration
changes nothing, a missing row and a clashing id are both caught. No network, nothing is
written outside the temp folder. Exit status 1 when a check fails.
"""
import contextlib, io, json, os, sys, tempfile, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import migrate_to_supabase as migrate, verify_migration as verify
from fake_postgrest import FakePostgrest
from test_records import latest_store

URL, SECRET = "https://fake.test", "sb-secret-for-tests"
results = []


def check(name, ok, note=""):
    print(("ok   " if ok else "FAIL ") + name + (f"  ({note})" if note else ""))
    results.append(ok)


def run(script, fake, argv):
    """script.main(argv) with urlopen pointed at `fake`; returns (exit code, printed text)."""
    saved = urllib.request.urlopen, dict(os.environ)
    urllib.request.urlopen = fake.urlopen
    os.environ.update(TT_SUPABASE_URL=URL, TT_SUPABASE_SECRET_KEY=SECRET)
    out, code = io.StringIO(), 0
    try:
        with contextlib.redirect_stdout(out):
            script.main(argv)
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else 1
        out.write(str(e.code) if isinstance(e.code, str) else "")
    finally:
        urllib.request.urlopen = saved[0]
        os.environ.clear()
        os.environ.update(saved[1])
    return code, out.getvalue()


def family_copy(store, shift):
    text = json.dumps(store).replace("Daniel", "Alex").replace("Cerys", "Sam")
    data = json.loads(text)
    if shift:
        for key in ("logs", "suggestions", "programChanges"):
            for item in data[key]:
                item["id"] += 7
        data["deletedLogs"] = [i + 7 for i in data["deletedLogs"]]
        for meal in data["meals"]:
            meal["id"] += "x"
    return data


def write(path, value):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(value if isinstance(value, str) else json.dumps(value, indent=2))


def main():
    with open(latest_store(), encoding="utf-8") as f:
        store = json.load(f)
    tmp = tempfile.mkdtemp(prefix="tt_migration_")
    files = {name: os.path.join(tmp, name) for name in ("data.json", "log.json", "fam1.json", "fam2.json")}
    write(files["data.json"], store)
    write(files["log.json"], [{"id": 1788000000000 + i, "date": "2026-09-01", "person": store["people"][0],
                               "overall": f"note {i}"} for i in range(3)])
    write(files["fam1.json"], family_copy(store, shift=True))
    write(files["fam2.json"], family_copy(store, shift=False))
    coach = os.path.join(tmp, "coach")
    for person, name, text in ((store["people"][0], "profile.md", "# Profile\r\nline\r\n"),
                               (store["people"][0], "decisions.md", "# Decisions\n"),
                               (store["people"][1], "profile.md", "# Profile\n")):
        os.makedirs(os.path.join(coach, person), exist_ok=True)
        write(os.path.join(coach, person, name), text)
    args = ["--data", files["data.json"], "--log", files["log.json"], "--coach", coach]

    fake = FakePostgrest(URL, SECRET)
    code, text = run(migrate, fake, args + ["--family", files["fam1.json"], "--dry-run"])
    check("dry run prints counts and sends nothing", code == 0 and not fake.log and "log" in text and "nothing sent" in text)

    code, text = run(migrate, fake, args + ["--family", files["fam1.json"]])
    kinds = {k for k, _ in fake.rows}
    check("migration sends the rows", code == 0 and len(fake.rows) > 300, f"{len(fake.rows)} rows")
    check("every kind is there", {"log", "bodyweight", "meal", "program", "person", "suggestion", "program_change",
                                  "coach_file", "coach_log", "person_data:coaching"} <= kinds)
    check("a second family has its own program", {k for k in fake.rows if k[0] == "program"} ==
          {("program", "p-daniel-cerys"), ("program", "p-alex-sam")})
    check("coach files keep their line endings", fake.rows[("coach_file", "Daniel/profile.md")]["body"]["text"] == "# Profile\r\nline\r\n")

    code, text = run(verify, fake, args + ["--family", files["fam1.json"]])
    check("verification passes", code == 0 and "migration verified" in text, text.strip().splitlines()[-1])

    before = {k: (r["body"], r["updated_at"], r["deleted_at"]) for k, r in fake.rows.items()}
    run(migrate, fake, args + ["--family", files["fam1.json"]])
    check("a second migration changes nothing", before == {k: (r["body"], r["updated_at"], r["deleted_at"])
                                                           for k, r in fake.rows.items()})

    victim = next(k for k in fake.rows if k[0] == "log" and fake.rows[k]["person"] == store["people"][1])
    del fake.rows[victim]
    code, text = run(verify, fake, args + ["--family", files["fam1.json"]])
    check("a missing log is caught", code == 1 and "MISSING" in text and "FAILED" in text)

    clash = FakePostgrest(URL, SECRET)
    run(migrate, clash, args + ["--family", files["fam2.json"]])
    code, text = run(verify, clash, args + ["--family", files["fam2.json"]])
    check("log ids used by two people are caught", code == 1 and "used by two people" in text and "FAILED" in text)

    code, text = run(verify, FakePostgrest(URL, SECRET), args)
    check("an empty project fails verification", code == 1)
    code, text = run(migrate, FakePostgrest(URL, "other"), args)
    check("a wrong key is refused", code == 1 and "HTTP 401" in text)
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
