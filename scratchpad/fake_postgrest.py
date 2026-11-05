"""An in-memory stand-in for the Supabase REST API (PostgREST) over the `records` table.

    from fake_postgrest import FakePostgrest
    fake = FakePostgrest("https://fake.test", "secret")
    urllib.request.urlopen = fake.urlopen        # what the MCP servers call

It answers GET /rest/v1/records (select, kind=eq., key=eq., key=in.(...), server_at=gt., order,
limit, offset) and POST /rest/v1/records?on_conflict=kind,key with
Prefer: resolution=merge-duplicates. Writes go through merge_trigger(), a line for line copy of
records_merge() in docs/supabase-schema.sql, so the newest-wins merge is exercised here too.
It refuses a call whose apikey or Bearer token is not the secret, and a bulk insert whose rows do
not all have the same columns, as PostgREST does.

It also answers POST /rest/v1/rpc/tt_pair_claim (the new phone's call, made with the publishable key
or the secret key), /rpc/tt_pair_cancel and /rpc/tt_keepalive over the `pairing` rows, with the
rules of those functions in docs/supabase-schema.sql: 10 claims a minute in total, a match is handed
over and deleted, expired rows are cleared. Tests set `fake.now_ms` to move the clock.
"""
import io, json, urllib.error, urllib.parse

COLUMNS = ("kind", "key", "person", "body", "updated_at", "deleted_at", "server_at", "by")
DEFAULTS = {"person": None, "body": {}, "updated_at": 0, "deleted_at": None, "by": None}


def merge_trigger(old, new, counter):
    """records_merge() from the schema. `old` is None on a plain insert."""
    new = dict(new)
    if old is None:
        new["body"] = {k: v for k, v in new["body"].items() if k != "__replace"}
    elif "__replace" in new["body"]:
        new["body"] = {k: v for k, v in new["body"].items() if k != "__replace"}
    elif new["updated_at"] >= old["updated_at"]:
        new["body"] = {**old["body"], **new["body"]}
    else:
        new["body"] = {**new["body"], **old["body"]}
    if old is not None:
        new["updated_at"] = max(new["updated_at"], old["updated_at"])
        ds = [d for d in (new["deleted_at"], old["deleted_at"]) if d is not None]
        new["deleted_at"] = max(ds) if ds else None
    new["server_at"] = "2026-11-03T12:00:00.%06d+00:00" % counter
    return new


def split_quoted(text):
    """The values of a PostgREST list such as ("a","b\\"c")."""
    out, i = [], 0
    while i < len(text):
        if text[i] == '"':
            i, val = i + 1, ""
            while text[i] != '"':
                if text[i] == "\\":
                    i += 1
                val += text[i]
                i += 1
            out.append(val)
            i += 1
        else:
            j = text.find(",", i)
            j = len(text) if j < 0 else j
            out.append(text[i:j])
            i = j
        i += 1
    return out


PAIR_LIMIT, PAIR_WINDOW_MS = 10, 60000


class FakePostgrest:
    def __init__(self, base, secret, publishable=None):
        self.base, self.secret, self.publishable = base.rstrip("/"), secret, publishable
        self.rows = {}
        self.pairing = {}         # code_hash -> {code_hash, salt, iv, ciphertext, expires_at (ms), attempts}
        self.pair_window = {"start": 0, "n": 0}
        self.now_ms = 1793000000000
        self.counter = 0
        self.log = []
        self.fail_posts = []      # [(code, kinds)]: the next POST touching one of kinds fails with code

    def _tick(self):
        self.counter += 1
        return self.counter

    def seed(self, rows, by="seed"):
        for r in rows:
            self._upsert({**DEFAULTS, **r, "by": r.get("by", by)})

    def touch(self, kind, key, body=None):
        """Another writer changes a row behind the caller's back."""
        self._upsert({**DEFAULTS, **(self.rows.get((kind, key)) or {"kind": kind, "key": key}),
                      "body": body or {}, "by": "someone else"})

    def _upsert(self, row):
        key = (row["kind"], row["key"])
        self.rows[key] = merge_trigger(self.rows.get(key), row, self._tick())

    def pair_insert(self, row):
        """What a signed-in family phone's insert into pairing does."""
        if row["code_hash"] in self.pairing:
            raise ValueError("duplicate code_hash")
        self.pairing[row["code_hash"]] = {"attempts": 0, **row}

    def clear_expired_pairing(self):
        self.pairing = {k: v for k, v in self.pairing.items() if v["expires_at"] > self.now_ms}

    def pair_claim(self, code_hash):
        """tt_pair_claim() from the schema."""
        self.clear_expired_pairing()
        if self.pair_window["start"] <= self.now_ms - PAIR_WINDOW_MS:
            self.pair_window = {"start": self.now_ms, "n": 0}
        self.pair_window["n"] += 1
        if self.pair_window["n"] > PAIR_LIMIT:
            return {"status": "slow"}
        row = self.pairing.pop(code_hash, None)
        if row is None:
            return {"status": "none"}
        return {"status": "ok", "salt": row["salt"], "iv": row["iv"], "ciphertext": row["ciphertext"]}

    def _rpc(self, name, body, fail):
        if name == "tt_pair_claim":
            return self.pair_claim((body or {}).get("p_code_hash"))
        if name == "tt_pair_cancel":
            self.pairing.pop((body or {}).get("p_code_hash"), None)
            return None
        if name == "tt_keepalive":
            self.clear_expired_pairing()
            return None
        fail(404, "unknown function")

    def urlopen(self, req, timeout=None):
        url, method = req.full_url, req.get_method()
        headers = {k.lower(): v for k, v in req.header_items()}
        body = json.loads(req.data) if req.data else None
        self.log.append({"method": method, "url": url, "body": body, "headers": headers})

        def fail(code, msg):
            raise urllib.error.HTTPError(url, code, msg, {}, io.BytesIO(json.dumps({"message": msg}).encode()))
        if not url.startswith(self.base + "/rest/v1/"):
            fail(404, "unknown host or path")
        parts = urllib.parse.urlsplit(url)
        if parts.path.startswith("/rest/v1/rpc/"):
            keys = {self.secret, self.publishable} - {None}
            if method != "POST" or headers.get("apikey") not in keys:
                fail(401, "Invalid API key")
            out = self._rpc(parts.path.rsplit("/", 1)[1], body, fail)
            return io.BytesIO(b"" if out is None else json.dumps(out).encode())
        if headers.get("apikey") != self.secret or headers.get("authorization") != f"Bearer {self.secret}":
            fail(401, "Invalid API key")
        if parts.path != "/rest/v1/records":
            fail(404, "unknown table")
        query = urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
        if method == "GET":
            return io.BytesIO(json.dumps(self._select(query, fail)).encode())
        if method != "POST":
            fail(405, "method not allowed")
        if "resolution=merge-duplicates" not in headers.get("prefer", "") or ("on_conflict", "kind,key") not in query:
            fail(400, "this fake only does upserts on kind,key")
        if not isinstance(body, list) or len({tuple(sorted(r)) for r in body}) > 1:
            fail(400, "All object keys must match")
        for r in body:
            if set(r) - set(COLUMNS) or not r.get("kind") or r.get("key") in (None, "") or r.get("body", {}) is None:
                fail(400, "bad row")
        for i, (code, kinds) in enumerate(self.fail_posts):
            if any(r["kind"] in kinds for r in body):
                del self.fail_posts[i]
                fail(code, "conflict")
        for r in body:
            self._upsert({**DEFAULTS, **r})
        return io.BytesIO(b"")

    def _select(self, query, fail):
        q = dict(query)
        rows = list(self.rows.values())
        for col, flt in query:
            if col in ("select", "order", "limit", "offset", "on_conflict"):
                continue
            op, _, val = flt.partition(".")
            if col not in COLUMNS:
                fail(400, f"no column {col}")
            if op == "eq":
                rows = [r for r in rows if str(r[col]) == val]
            elif op == "in":
                wanted = split_quoted(val[1:-1])
                rows = [r for r in rows if str(r[col]) in wanted]
            elif op == "gt":
                rows = [r for r in rows if r[col] is not None and str(r[col]) > val]
            else:
                fail(400, f"operator {op} not supported here")
        rows.sort(key=lambda r: (r["kind"], r["key"]))
        start = int(q.get("offset", 0))
        rows = rows[start:start + int(q.get("limit", 1000))]
        cols = COLUMNS if q.get("select", "*") == "*" else q["select"].split(",")
        return [{c: r[c] for c in cols} for r in rows]
