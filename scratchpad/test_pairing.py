"""The pairing rules in fake_postgrest.py, which copy tt_pair_claim, tt_pair_cancel and tt_keepalive in
docs/supabase-schema.sql.

    python scratchpad/test_pairing.py
"""
import json, os, sys, urllib.error, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fake_postgrest import FakePostgrest

BASE, SECRET, PUBLISHABLE = "https://fake.test", "secret", "publishable"
failed = 0


def check(label, ok):
    global failed
    print(("ok   " if ok else "FAIL ") + label)
    failed += 0 if ok else 1


def rpc(fake, name, body, key=PUBLISHABLE):
    req = urllib.request.Request(f"{BASE}/rest/v1/rpc/{name}", data=json.dumps(body).encode(), method="POST",
                                 headers={"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    raw = fake.urlopen(req).read()
    return json.loads(raw) if raw else None


def row(code_hash, fake, minutes=10):
    return {"code_hash": code_hash, "salt": "s", "iv": "i", "ciphertext": "c", "expires_at": fake.now_ms + minutes * 60000}


fake = FakePostgrest(BASE, SECRET, PUBLISHABLE)
fake.pair_insert(row("h1", fake))
check("a wrong hash finds nothing", rpc(fake, "tt_pair_claim", {"p_code_hash": "nope"}) == {"status": "none"})
check("the right hash returns only the salt, iv and ciphertext", rpc(fake, "tt_pair_claim", {"p_code_hash": "h1"}) == {"status": "ok", "salt": "s", "iv": "i", "ciphertext": "c"})
check("the row is deleted by the claim", "h1" not in fake.pairing)
check("a second claim finds nothing", rpc(fake, "tt_pair_claim", {"p_code_hash": "h1"}) == {"status": "none"})

fake.pair_insert(row("h2", fake))
fake.now_ms += 10 * 60000 + 1
check("an expired row is refused", rpc(fake, "tt_pair_claim", {"p_code_hash": "h2"}) == {"status": "none"})
check("and cleared by the claim", fake.pairing == {})

fake = FakePostgrest(BASE, SECRET, PUBLISHABLE)
fake.pair_insert(row("h3", fake))
answers = [rpc(fake, "tt_pair_claim", {"p_code_hash": f"x{i}"})["status"] for i in range(10)]
check("ten tries a minute are answered", answers == ["none"] * 10)
check("the eleventh is told to slow down, even with the right hash", rpc(fake, "tt_pair_claim", {"p_code_hash": "h3"}) == {"status": "slow"} and "h3" in fake.pairing)
fake.now_ms += 60001
check("a minute later the right hash works", rpc(fake, "tt_pair_claim", {"p_code_hash": "h3"})["status"] == "ok")

fake.pair_insert(row("h4", fake))
rpc(fake, "tt_pair_cancel", {"p_code_hash": "h4"}, SECRET)
check("cancel removes the row", fake.pairing == {})
fake.pair_insert(row("h5", fake))
fake.now_ms += 10 * 60000 + 1
rpc(fake, "tt_keepalive", {}, SECRET)
check("the keep-alive clears expired rows", fake.pairing == {})

try:
    rpc(fake, "tt_pair_claim", {"p_code_hash": "h"}, "wrong")
    check("an unknown key is refused", False)
except urllib.error.HTTPError as e:
    check("an unknown key is refused", e.code == 401)
sys.exit(1 if failed else 0)
