# Training Tracker — MCP coaching server

Lets **Claude act as your coach**: it reads Daniel's & Cerys's workouts, PRs, bodyweight, runs
and goals straight from your data and gives feedback toward your goals. Runs locally on your
laptop, on your **Claude subscription — no API billing**.

## What it exposes

**Read:** `people`, `goals(person)`, `recent_sessions(person, limit)`, `session(session_id)`,
`prs(person)`, `bodyweight(person)`, `progress(person, exercise)`, `running_form(person)`,
`limiters(person)`, `coaching_history(person)`, `session_notes(session)`, `run_session(person)`,
`suggestions()`.

**Write** (needs the token to have Contents: **read and write**): `write_coaching`,
`write_limiter`, `write_session_notes`, `write_run`, `propose_suggestion_tool`,
`resolve_suggestion_tool`.
Everything written lands in the shared `data.json` and reaches the phones on their next sync.

Three of the writes are worth knowing the shape of before using them:
- `write_coaching` is **per person** — Daniel and Cerys can get different notes on the same
  session, and usually should.
- `write_session_notes` is **not**. Warm-up / cool-down notes live on the *program*, so one text
  is shared by both people; name whoever a line is for. It also **replaces** the field by default,
  and those notes are long hand-written mobility blocks — so call `session_notes(session)` first
  and pass `append=True` when you're adding a line rather than rewriting the lot. The previous
  text is returned on every write, so a bad one can be put straight back.
- `write_run` is the one place the coach owns program **structure**. Each person has their own
  run session (`Run: Daniel`, `Run: Cerys` — the `person` field on the session, which is also
  what hides it from the other one), and Daniel's instruction is that the coach prescribes the
  optimal run each week from the data, in whatever format the data calls for. It replaces the
  exercise list outright, so call `run_session(person)` first; the whole previous session comes
  back for a revert. `Cardio: Endurance + Core` stays as the untouchable backup.

Then in Claude you just ask, e.g. *"You're my coach — review my last two weeks against my goals
and tell me what to change,"* and it calls these tools itself.

## Setup (once, on the laptop)

### 1. Requirements
- Python 3.10+
- `python -m pip install mcp truststore`  (use `python -m pip`, not bare `pip`, if pip isn't on
  PATH). `truststore` makes SSL use the OS trust store — needed if antivirus/proxy TLS inspection
  causes `CERTIFICATE_VERIFY_FAILED`.
- Verify with `python mcp-coach/test_connection.py` after filling in `.mcp.json`.

### 2. Point it at your data
Use the **GitHub store** the app syncs to (recommended, always current):
- `TT_GITHUB_REPO`  — `Daniel0469/Training-Data`
- `TT_GITHUB_TOKEN` — a fine-grained token with **Contents: read** on that repo
- `TT_GITHUB_PATH`  — optional, default `data.json`

…or a local export file instead: `TT_DATA_FILE=/path/to/training-data-YYYY-MM-DD.json`.

Quick sanity check (no Claude needed):
```
python server.py --selftest /path/to/an-export.json
```

### 3. Register it with Claude

**Claude Desktop** — edit `claude_desktop_config.json`
(macOS: `~/Library/Application Support/Claude/`, Windows: `%APPDATA%\Claude\`):
```json
{
  "mcpServers": {
    "training-tracker": {
      "command": "python",
      "args": ["C:\\Users\\danie\\Documents\\TrainingTracker\\mcp-coach\\server.py"],
      "env": {
        "TT_GITHUB_REPO": "Daniel0469/Training-Data",
        "TT_GITHUB_TOKEN": "github_pat_…",
        "TT_GITHUB_PATH": "data.json"
      }
    }
  }
}
```
Restart Claude Desktop; you'll see the `training-tracker` tools available.

**Claude Code** — from the repo:
```
claude mcp add training-tracker -- python mcp-coach/server.py
```
then set the `TT_GITHUB_*` env vars in your shell (or use `claude mcp add -e KEY=value …`).

## Notes
- **Read-only** by design (it analyses; it never changes your logs). Writing goals / coach notes
  back is a possible later addition.
- The token is read from the environment — **don't commit it**. Keep it in the Claude config /
  your shell only.
- Data is fetched fresh on each call, so coaching always reflects your latest **synced** data —
  tap **Sync now** in the app after a workout so the coach sees it.
- Works on the laptop where you run Claude, not on the iPhone tracker (matches the split: log on
  the phone, coach on the laptop).
