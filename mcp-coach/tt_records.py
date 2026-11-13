"""Training Tracker - the Supabase record mapping shared by both MCP servers.

to_records(data) turns a data.json-shaped dict into rows of the `records` table
(docs/supabase-schema.sql) and from_records(rows) turns rows back. The shapes are in
docs/supabase-setup.md. The PostgREST calls at the bottom read the table and write only the rows
that changed.

mcp-garmin/tt_records.py is a copy of this file (a separate process, like progression.py's
callers) - keep in step with it. scratchpad/test_records.py fails when they differ.
"""
import copy, datetime, json, re, time, urllib.error, urllib.parse, urllib.request

PERSON_FIELDS = ("coaching", "hrZones", "machineSettings", "progression", "features",
                 "nutritionTargets", "limiters", "wellness", "racePredictions",
                 "bodyProfile", "dayMarks")
PROGRAM_META = ("members", "version")      # a program edit that changes only these is not a change
COLUMNS = ("kind", "key", "person", "body", "updated_at", "deleted_at", "by")
STUB_KINDS = {"log", "bodyweight", "meal"}                 # kinds with a tombstone list in data.json
ITEM_KINDS = STUB_KINDS | {"measurement", "suggestion", "program_change", "coach_question"}
ITEM_KINDS_AND_FIELDS = ITEM_KINDS | {f"person_data:{f}" for f in PERSON_FIELDS}   # body is the item itself
KNOWN_KINDS = ITEM_KINDS_AND_FIELDS | {"person", "program", "family"}
STAMPS = {"suggestion": ("updatedAt", "doneAt", "approvedAt", "declinedAt"),
          "program_change": ("updatedAt", "at", "appliedAt", "declinedAt", "withdrawnAt")}


def _ms(value):
    """A time as ms since 1970: a number, or an ISO date or datetime string. 0 when it is neither."""
    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str) and value:
        try:
            when = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return 0
        return int((when if when.tzinfo else when.replace(tzinfo=datetime.timezone.utc)).timestamp() * 1000)
    return 0


def _stamp(item, kind="log"):
    return max([_ms(item.get(f)) for f in STAMPS.get(kind, ("updatedAt",))] or [0])


def _deep_stamp(value, depth=3):
    """The newest `updatedAt` or `updated` anywhere near the top of a per-person object."""
    if depth < 0 or not isinstance(value, (dict, list)):
        return 0
    best = 0
    for k, x in (value.items() if isinstance(value, dict) else enumerate(value)):
        best = max(best, _ms(x) if k in ("updatedAt", "updated") else _deep_stamp(x, depth - 1))
    return best


def _natural(row):
    key = str(row["key"])
    return (row["kind"], (0, int(key), "") if key.lstrip("-").isdigit() else (1, 0, key))


# ---------------------------------------------------------------- data.json -> rows
def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-") or "session"


def programs_of(data):
    """({id: program}, {person: {id, updatedAt}}) of a payload. An old payload has one `program`,
    which is wrapped as shared by the people it names, with the id, members and version the app
    gives it (wrapProgram in js/app.js), and each person is pointed at a program that lists them."""
    named = [p for p in data.get("people") or [] if p]
    programs = {i: p for i, p in (data.get("programs") or {}).items() if isinstance(p, dict)}
    ids = {p: r for p, r in (data.get("programIds") or {}).items() if isinstance(r, dict)}
    old = data.get("program")
    if not programs and isinstance(old, dict) and old.get("sessions"):
        wrapped = dict(old, id="p-" + ("-".join(slugify(m) for m in named) or "main"), members=named[:],
                       version=int(old.get("version") or 1))
        programs[wrapped["id"]] = wrapped
    for person in named:
        if (ids.get(person) or {}).get("id") not in programs:
            ids.pop(person, None)
            found = next((i for i, pr in programs.items() if person in (pr.get("members") or [])), None)
            if found:
                ids[person] = {"id": found, "updatedAt": 0}
    return programs, ids


def prog_of(data, person):
    """The program `person` trains, as the app's progOf: the one their programId names, else one
    that lists them, else the old single `program`."""
    programs = data.get("programs") or {}
    ref = (data.get("programIds") or {}).get(person) or {}
    return (programs.get(ref.get("id")) or next((p for p in programs.values() if person in (p.get("members") or [])), None)
            or data.get("program") or {"order": [], "sessions": {}})


def to_records(data, now=None, coach_files=None, coaching_log=None, prev=None, slot_offset=0):
    """Rows for everything in `data`, plus the coach's text files ({"Daniel/profile.md": text}) and
    coaching history (a list of entries). `prev` is a snapshot() of the table: it keeps the extra
    keys of a person row and the time an earlier delete happened. `slot_offset` moves the people's
    slots up, so a second family's people sit after the first family's."""
    now = now or time.time_ns() // 1_000_000
    prev = prev or {}
    rows = {}

    def put(kind, key, person, body, updated_at):
        rows[(kind, str(key))] = {"kind": kind, "key": str(key), "person": person, "body": body,
                                  "updated_at": updated_at, "deleted_at": None}

    def tombstone(kind, key, person, stub, deleted_at):
        old = prev.get((kind, str(key)))
        at = int(deleted_at or 0) or (old or {}).get("deleted_at") or now
        row = rows.get((kind, str(key)))
        if row is None:
            put(kind, key, person, stub, 0)
            row = rows[(kind, str(key))]
        row["deleted_at"] = at

    people = [p for p in data.get("people") or [] if p]
    weights, goals = data.get("weights") or [], data.get("goals") or []
    programs, program_ids = programs_of(data)
    for slot, name in enumerate(data.get("people") or []):
        if not name:
            continue
        body = dict((prev.get(("person", name)) or {}).get("body") or {})
        body["slot"] = body["slot"] if isinstance(body.get("slot"), int) else slot + slot_offset
        for field, values in (("weight", weights), ("goal", goals)):
            if slot < len(values) and values[slot] not in ("", None):
                body[field] = values[slot]
            else:
                body.pop(field, None)
        ref = program_ids.get(name)
        if ref:
            body["programId"], body["programIdAt"] = ref["id"], ref.get("updatedAt") or 0
        else:
            body.pop("programId", None), body.pop("programIdAt", None)
        put("person", name, name, body, 0)
    for field in PERSON_FIELDS:
        for person, value in (data.get(field) or {}).items():
            put(f"person_data:{field}", person, person, value if isinstance(value, dict) else {"_v": value},
                _deep_stamp(value))
    for program_id, program in programs.items():
        put("program", program_id, None, program, _ms(program.get("updatedAt")))
    for list_key, kind, id_of in (
            ("logs", "log", lambda x: x.get("id")),
            ("bodyweights", "bodyweight", lambda x: f"{x['person']}:{x['date']}" if x.get("person") and x.get("date") else None),
            ("measurements", "measurement", lambda x: f"{x['person']}:{x['date']}" if x.get("person") and x.get("date") else None),
            ("meals", "meal", lambda x: x.get("id")),
            ("suggestions", "suggestion", lambda x: x.get("id")),
            ("programChanges", "program_change", lambda x: x.get("id"))):
        for item in data.get(list_key) or []:
            key = id_of(item) if isinstance(item, dict) else None
            if key is not None:
                put(kind, key, item.get("person"), item, _stamp(item, kind))
    for person, questions in (data.get("coachQuestions") or {}).items():
        for q in questions if isinstance(questions, list) else []:
            if isinstance(q, dict) and q.get("id") is not None:
                put("coach_question", f"{person}:{q['id']}", person, q, _stamp(q))
    if isinstance(data.get("adminPin"), dict):
        put("family", "adminPin", None, data["adminPin"], _ms(data["adminPin"].get("updatedAt")))
    for log_id in data.get("deletedLogs") or []:
        tombstone("log", log_id, None, {"id": log_id}, 0)
    for t in data.get("deletedBodyweights") or []:
        if isinstance(t, dict) and t.get("person") and t.get("date"):
            tombstone("bodyweight", f"{t['person']}:{t['date']}", t["person"],
                      {"person": t["person"], "date": t["date"]}, t.get("deletedAt"))
    for t in data.get("deletedMeals") or []:
        if isinstance(t, dict) and t.get("id") is not None:
            tombstone("meal", t["id"], None, {"id": t["id"]}, t.get("deletedAt"))
    for key, text in (coach_files or {}).items():
        put("coach_file", key, key.split("/")[0], {"text": text}, now)
    for entry in coaching_log or []:
        if isinstance(entry, dict) and entry.get("id") is not None:
            put("coach_log", entry["id"], entry.get("person"), entry, _ms(entry["id"]))
    return sorted(rows.values(), key=_natural)


# ---------------------------------------------------------------- rows -> data.json
def _alive(row):
    """A deleted record whose last edit is newer than the delete (it was added back) is alive."""
    return row.get("deleted_at") is None or (row.get("updated_at") or 0) > row["deleted_at"]


def from_records(rows):
    """A data.json-shaped dict from `records` rows. Coach files and the coaching history are not in
    data.json - see coach_parts."""
    data = {"version": 1, "people": ["", ""], "weights": ["", ""], "goals": ["", ""],
            "suggestions": [], "programChanges": [], "meals": [], "measurements": [], "bodyweights": [],
            "logs": [], "deletedLogs": [], "deletedBodyweights": [], "deletedMeals": [],
            "coachQuestions": {}, "programs": {}, "programIds": {}, "program": {"order": [], "sessions": {}}}
    for field in PERSON_FIELDS:
        data[field] = {}
    persons = []
    for row in sorted(copy.deepcopy(rows), key=_natural):
        kind, body, alive = row["kind"], row.get("body") or {}, _alive(row)
        person = row.get("person") or body.get("person")
        if row.get("deleted_at") is not None and kind in STUB_KINDS:
            at = row["deleted_at"]
            if kind == "log":
                data["deletedLogs"].append(body.get("id", row["key"]))
            elif kind == "bodyweight":
                data["deletedBodyweights"].append({"person": person, "date": body.get("date"), "deletedAt": at})
            else:
                data["deletedMeals"].append({"id": body.get("id", row["key"]), "deletedAt": at})
        if not alive:
            continue
        if kind == "log":
            data["logs"].append(body)
        elif kind == "bodyweight":
            data["bodyweights"].append(body)
        elif kind == "measurement":
            data["measurements"].append(body)
        elif kind == "meal":
            data["meals"].append(body)
        elif kind == "suggestion":
            data["suggestions"].append(body)
        elif kind == "program_change":
            data["programChanges"].append(body)
        elif kind == "coach_question":
            data["coachQuestions"].setdefault(person or row["key"].split(":")[0], []).append(body)
        elif kind == "person":
            persons.append(row)
        elif kind == "program":
            data["programs"][row["key"]] = body
        elif kind == "family" and row["key"] == "adminPin":
            data["adminPin"] = body
        elif kind.startswith("person_data:") and kind[12:] in PERSON_FIELDS:
            data[kind[12:]][person or row["key"]] = body["_v"] if list(body) == ["_v"] else body
    persons.sort(key=lambda r: ((r["body"].get("slot") if isinstance(r["body"].get("slot"), int) else 99), r["key"]))
    for row in persons:
        slot = row["body"].get("slot")
        if not (isinstance(slot, int) and 0 <= slot < len(data["people"]) and not data["people"][slot]):
            data["people"].append(""), data["weights"].append(""), data["goals"].append("")
            slot = len(data["people"]) - 1
        data["people"][slot] = row["key"]
        data["weights"][slot] = row["body"].get("weight", "")
        data["goals"][slot] = row["body"].get("goal", "")
    for row in persons:
        ref = row["body"].get("programId")
        if ref in data["programs"]:
            data["programIds"][row["key"]] = {"id": ref, "updatedAt": row["body"].get("programIdAt", 0)}
    first = next((data["programIds"][r["key"]]["id"] for r in persons if r["key"] in data["programIds"]), None)
    if data["programs"]:
        data["program"] = data["programs"][first or sorted(data["programs"])[0]]
    return data


def coach_parts(rows):
    """The coach's text files ({"Daniel/profile.md": text}) and coaching history (oldest first)."""
    live = [r for r in rows if _alive(r)]
    files = {r["key"]: r["body"].get("text", "") for r in live if r["kind"] == "coach_file"}
    log = [r["body"] for r in sorted(live, key=_natural) if r["kind"] == "coach_log"]
    return files, log


# ---------------------------------------------------------------- planning a write
def snapshot(rows):
    """(kind, key) -> row, as read. This stands in for the file sha: it says what the caller saw."""
    return {(r["kind"], r["key"]): r for r in rows}


def _core(row):
    body = row.get("body") or {}
    return {k: v for k, v in body.items() if k not in PROGRAM_META} if row["kind"] == "program" else body


def _column_values(row, by, **changes):
    return {c: ({**row, **changes, "by": by}).get(c) for c in COLUMNS}


def plan_writes(new_rows, snap, by, now=None):
    """The rows to upsert so the table matches `new_rows`: new and changed rows, a delete time on
    rows that are gone, and nothing for rows that did not change. A changed row is never older than
    the one read, so the table's merge lets the edit win over what the caller read. A row that lost a top-level key
    carries "__replace" so the table's merge trigger drops the key instead of keeping it."""
    now = now or time.time_ns() // 1_000_000
    out, seen = [], set()
    for new in new_rows:
        key = (new["kind"], new["key"])
        seen.add(key)
        old = snap.get(key)
        gone = new.get("deleted_at") is not None
        if old is None:
            out.append(_column_values(new, by))
            continue
        old_gone = old.get("deleted_at") is not None
        if old_gone and gone or (_core(old) == _core(new) and old_gone == gone):
            continue
        if gone:
            out.append(_column_values(old, by, deleted_at=new["deleted_at"]))
            continue
        row = _column_values(new, by, updated_at=max(new["updated_at"], old["updated_at"]))
        if new["kind"] == "program":
            row["body"] = dict(new["body"], version=(old["body"].get("version") or 1) + 1)
        elif new["kind"] in ITEM_KINDS_AND_FIELDS and set(_core(old)) - set(_core(new)):
            row["body"] = dict(new["body"], __replace=True)
        out.append(row)
    for key, old in snap.items():
        if key not in seen and key[0] in ITEM_KINDS_AND_FIELDS and _alive(old) and old.get("deleted_at") is None:
            out.append(_column_values(old, by, deleted_at=now))
    return out


# ---------------------------------------------------------------- PostgREST
def _request(base, secret, method, path, body=None, prefer=None):
    headers = {"apikey": secret, "Authorization": f"Bearer {secret}", "Content-Type": "application/json",
               "Accept": "application/json"}
    if prefer:
        headers["Prefer"] = prefer
    req = urllib.request.Request(base.rstrip("/") + "/rest/v1/" + path, method=method, headers=headers,
                                 data=None if body is None else json.dumps(body).encode("utf-8"))
    with urllib.request.urlopen(req, timeout=30) as r:
        text = r.read()
    return json.loads(text) if text else None


def fetch_rows(base, secret, kind=None, key=None):
    """Every row of `records`, or only those of one `kind` (and `key`)."""
    where = "".join(f"&{col}=eq.{urllib.parse.quote(str(v), safe='')}" for col, v in (("kind", kind), ("key", key)) if v)
    rows, page = [], 1000
    while True:
        part = _request(base, secret, "GET", f"records?select=*&order=kind,key&limit={page}&offset={len(rows)}{where}")
        rows += part
        if len(part) < page:
            return rows


def moved_rows(base, secret, snap, changes):
    """The changed rows that another writer touched since the snapshot: their server_at differs
    from the one read, or the row did not exist then and does now."""
    by_kind, moved = {}, []
    for row in changes:
        by_kind.setdefault(row["kind"], []).append(row["key"])
    for kind, keys in by_kind.items():
        for i in range(0, len(keys), 100):
            quoted = ",".join('"' + k.replace("\\", "\\\\").replace('"', '\\"') + '"' for k in keys[i:i + 100])
            path = (f"records?select=kind,key,server_at&kind=eq.{urllib.parse.quote(kind, safe='')}"
                    f"&key=in.({urllib.parse.quote(quoted, safe='')})")
            moved += [r for r in _request(base, secret, "GET", path)
                      if (snap.get((r["kind"], r["key"])) or {}).get("server_at") != r["server_at"]]
    return moved


def upsert(base, secret, rows):
    """Send complete rows (all of COLUMNS, `by` filled in), merged with any row already there."""
    for i in range(0, len(rows), 200):
        _request(base, secret, "POST", "records?on_conflict=kind,key", rows[i:i + 200],
                 prefer="resolution=merge-duplicates,return=minimal")


def write_rows(base, secret, snap, new_rows, by, now=None):
    """Upsert what changed. A row another writer touched since the snapshot raises a 409 HTTPError,
    which the servers' _github_update treats as "read again and redo the change". Returns the
    number of rows sent."""
    changes = plan_writes(new_rows, snap, by, now)
    if not changes:
        return 0
    if moved_rows(base, secret, snap, changes):
        raise urllib.error.HTTPError(base, 409, "a row changed since it was read", {}, None)
    upsert(base, secret, changes)
    return len(changes)
