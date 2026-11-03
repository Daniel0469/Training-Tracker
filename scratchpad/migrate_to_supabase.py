"""Move the Training Tracker store into Supabase.

    set TT_SUPABASE_URL=<project url>
    set TT_SUPABASE_SECRET_KEY=<secret key>
    python scratchpad/migrate_to_supabase.py --data data.json --log coaching-log.json --coach coach ^
        --family mum.json brother.json [--dry-run]

--data is a copy of the store's data.json. --log is coaching-log.json and --coach the folder that
holds <name>/profile.md and <name>/decisions.md, both optional. --family takes any number of export
files from other phones. Their people sit after the ones before them, and each file brings its own
programs (an old single `program` is wrapped the way the app wraps it). The URL and the key come from the environment only. --dry-run reads the same
files, prints what would be sent and sends nothing (it does not need the environment).

Safe to run again: the table merges what is already there. verify_migration.py checks the result.
"""
import argparse, glob, json, os, sys, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "mcp-coach"))
import tt_records

BY = "migrate"


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def file_time(path, data):
    """When the file was made, in ms: its exportedAt, else the file's own time. It stands in for
    the time of deletes and of coach file edits, so running the migration again sends the same rows."""
    return tt_records._ms(data.get("exportedAt")) or int(os.path.getmtime(path) * 1000)


def load_sources(args):
    """One source per file: {"name", "data", "now", "log", "coach", "slot_offset"}. The coaching log and
    the coach files belong with --data."""
    coach = {}
    for path in sorted(glob.glob(os.path.join(args.coach, "*", "*.md")) if args.coach else []):
        person, name = os.path.basename(os.path.dirname(path)), os.path.basename(path)
        with open(path, encoding="utf-8", newline="") as f:
            coach[f"{person}/{name}"] = f.read()
    data = read_json(args.data)
    sources = [{"name": os.path.basename(args.data), "data": data, "now": file_time(args.data, data),
                "log": read_json(args.log) if args.log else [], "coach": coach, "slot_offset": 0}]
    offset = len(sources[0]["data"].get("people") or []) or 2
    for path in args.family or []:
        data = read_json(path)
        sources.append({"name": os.path.basename(path), "data": data, "now": file_time(path, data), "log": [],
                        "coach": {}, "slot_offset": offset})
        offset += len(data.get("people") or [])
    return sources


def source_rows(src):
    return tt_records.to_records(src["data"], now=src["now"], coach_files=src["coach"], coaching_log=src["log"],
                                 slot_offset=src["slot_offset"])


def source_parser(description):
    ap = argparse.ArgumentParser(description=description, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True)
    ap.add_argument("--log")
    ap.add_argument("--coach")
    ap.add_argument("--family", nargs="*", default=[])
    return ap


def parse(argv):
    ap = source_parser(__doc__)
    ap.add_argument("--dry-run", action="store_true")
    return ap.parse_args(argv)


def main(argv=None):
    args = parse(argv)
    url, secret = os.environ.get("TT_SUPABASE_URL"), os.environ.get("TT_SUPABASE_SECRET_KEY")
    if not args.dry_run and not (url and secret):
        sys.exit("Set TT_SUPABASE_URL and TT_SUPABASE_SECRET_KEY in the environment first.")
    sent = 0
    for src in load_sources(args):
        rows = [dict(r, by=BY) for r in source_rows(src)]
        counts = {}
        for r in rows:
            counts[r["kind"]] = counts.get(r["kind"], 0) + 1
        deleted = sum(r["deleted_at"] is not None for r in rows)
        print(f"{src['name']}: {len(rows)} rows ({deleted} deleted)")
        for kind, n in sorted(counts.items()):
            print(f"   {kind:28} {n}")
        if not args.dry_run:
            try:
                tt_records.upsert(url, secret, rows)
            except urllib.error.HTTPError as e:
                sys.exit(f"Supabase refused the rows: HTTP {e.code} {e.reason}. Check the URL and the secret key.")
            sent += len(rows)
    print("dry run: nothing sent" if args.dry_run else f"sent {sent} rows")


if __name__ == "__main__":
    main()
