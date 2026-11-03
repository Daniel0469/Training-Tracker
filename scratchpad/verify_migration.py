"""Check that a Supabase project holds everything the files given to migrate_to_supabase.py hold.

    set TT_SUPABASE_URL=<project url>
    set TT_SUPABASE_SECRET_KEY=<secret key>
    python scratchpad/verify_migration.py --data data.json --log coaching-log.json --coach coach ^
        --family mum.json brother.json

Takes the same files as the migration and reads the project back. For each source and each person
it checks the logs (count and ids), weigh-in and measurement dates, meal ids, program session
names and delete records, then that every row the files produce is there with the same content,
and that the coach files and coaching history arrived. It also lists logs whose session is not in
their person's program (a warning) and any log id used by two people (a failure, because the two
logs would share one row). Prints one line per check and exits 1 when anything failed.
"""
import os, sys, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import migrate_to_supabase as mig
tt_records = mig.tt_records


def alive_rows(rows, kind):
    return [r for r in rows.values() if r["kind"] == kind and tt_records._alive(r)]


def check_source(src, rows, db, problems, warnings):
    data, name = src["data"], src["name"]
    tombs = {"log": {str(i) for i in data.get("deletedLogs") or []},
             "bodyweight": {f"{t['person']}:{t['date']}" for t in data.get("deletedBodyweights") or []},
             "meal": {str(t["id"]) for t in data.get("deletedMeals") or []}}

    def report(label, expected, found, fail=True):
        missing = sorted(expected - found, key=str)
        line = f"{label}: {len(expected & found)}/{len(expected)}"
        if missing:
            line += f" MISSING {missing[:5]}"
            (problems if fail else warnings).append(f"{name} {label}: {len(missing)} missing")
        print("   " + line)

    for person in [p for p in data.get("people") or [] if p]:
        print(f"{name} / {person}")
        report("logs", {str(l["id"]) for l in data.get("logs") or [] if l.get("person") == person} - tombs["log"],
               {r["key"] for r in alive_rows(rows, "log") if r["person"] == person})
        report("bodyweights", {b["date"] for b in data.get("bodyweights") or [] if b.get("person") == person},
               {r["body"]["date"] for r in alive_rows(rows, "bodyweight") if r["person"] == person})
        report("measurements", {m["date"] for m in data.get("measurements") or [] if m.get("person") == person},
               {r["body"]["date"] for r in alive_rows(rows, "measurement") if r["person"] == person})
        wanted = {s["name"] for s in tt_records.prog_of(data, person).get("sessions", {}).values()}
        found = {s["name"] for s in tt_records.prog_of(db, person).get("sessions", {}).values()}
        report("program sessions", wanted, found)
        keys = set(tt_records.prog_of(db, person).get("sessions", {}))
        orphans = sorted(str(l["id"]) for l in db["logs"] if l.get("person") == person and l.get("sessionKey") not in keys)
        print(f"   logs whose session is not in {person}'s program: {len(orphans)}" + (f" {orphans[:5]}" if orphans else ""))
        if orphans:
            warnings.append(f"{name} / {person}: {len(orphans)} logs have a sessionKey missing from the program")
    report("meals", {str(m["id"]) for m in data.get("meals") or [] if m.get("id") is not None} - tombs["meal"],
           {r["key"] for r in alive_rows(rows, "meal")})
    for kind, label in (("log", "deleted logs"), ("bodyweight", "deleted weigh-ins"), ("meal", "deleted meals")):
        report(label, tombs[kind], {k for (kd, k), r in rows.items() if kd == kind and r["deleted_at"] is not None})

    mine = tt_records.snapshot(mig.source_rows(src))
    wrong = [k for k, want in mine.items()
             if k not in rows or (want["deleted_at"] is None and tt_records._core(rows[k]) != tt_records._core(want))]
    print(f"   rows with the same content: {len(mine) - len(wrong)}/{len(mine)}")
    if wrong:
        problems.append(f"{name}: {len(wrong)} rows differ or are missing, e.g. {wrong[:3]}")
    files, log = tt_records.coach_parts(list(rows.values()))
    report("coach files", set(src["coach"]), {k for k in files if files[k] == src["coach"].get(k)})
    report("coaching history", {str(e["id"]) for e in src["log"]}, {str(e["id"]) for e in log})


def main(argv=None):
    args = mig.source_parser(__doc__).parse_args(argv)
    url, secret = os.environ.get("TT_SUPABASE_URL"), os.environ.get("TT_SUPABASE_SECRET_KEY")
    if not (url and secret):
        sys.exit("Set TT_SUPABASE_URL and TT_SUPABASE_SECRET_KEY in the environment first.")
    sources = mig.load_sources(args)
    try:
        rows = {(r["kind"], r["key"]): r for r in tt_records.fetch_rows(url, secret)}
    except urllib.error.HTTPError as e:
        sys.exit(f"Supabase refused the request: HTTP {e.code} {e.reason}. Check the URL and the secret key.")
    db = tt_records.from_records(list(rows.values()))
    problems, warnings = [], []
    owners = {}
    for src in sources:
        for log in src["data"].get("logs") or []:
            owners.setdefault(str(log.get("id")), set()).add(log.get("person"))
    shared = sorted(i for i, people in owners.items() if len(people) > 1)
    print(f"log ids used by two people: {len(shared)}" + (f" {shared[:5]}" if shared else ""))
    if shared:
        problems.append(f"{len(shared)} log ids belong to more than one person")
    for src in sources:
        check_source(src, rows, db, problems, warnings)
    for line in warnings:
        print("warning:", line)
    for line in problems:
        print("FAILED:", line)
    print("migration verified" if not problems else f"{len(problems)} problems")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
