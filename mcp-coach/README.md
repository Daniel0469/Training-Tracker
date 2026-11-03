# Training Tracker - MCP coaching server

Lets **Claude act as your coach**: it reads Daniel's & Cerys's workouts, PRs, bodyweight, runs
and goals straight from your data and gives feedback toward your goals. Runs locally on your
laptop, on your **Claude subscription - no API billing**.

## What it exposes

**Read:** `people`, `goals(person)`, `recent_sessions(person, limit)`, `session(session_id)`,
`prs(person)`, `bodyweight(person)`, `progress(person, exercise)`, `running_form(person)`,
`limiters(person)`, `coaching_history(person)`, `session_notes(session)`, `run_session(person)`,
`progression(person)`, `suggestions()`, and the coach's memory: `coach_profile(person)`,
`coach_decisions(person)`, `coach_questions(person, status)`.

**Write** (needs the token to have Contents: **read and write**): `write_coaching`,
`write_limiter`, `write_session_notes`, `write_run`, `write_machine_step`, `propose_suggestion_tool`,
`resolve_suggestion_tool`, and the memory writes `write_coach_profile`, `add_coach_decision`,
`review_coach_decision`, `add_coach_question`, `remind_coach_question`, `close_coach_question`.
Everything written lands in the shared `data.json` and reaches the phones on their next sync,
except the profile and decision files, which sit in the private store repo (below).

The coach's memory, per person (method: `docs/methods/coaching-behaviour-method.md`):
- `coach/<name>/profile.md` is the current truth and `write_coach_profile` replaces the whole file,
  so read `coach_profile` first and carry forward everything still true.
- `coach/<name>/decisions.md` is append-only. `add_coach_decision` adds an entry (change before and
  after, reason, expected result, review date, agreement, implementation and satisfaction kept
  apart). `review_coach_decision` sets the response and review fields on an existing entry and adds
  a dated review line. Both rebuild the index of active and due decisions at the top.
- Open questions live in `data.json` under `coachQuestions[person]`. `add_coach_question` shows one
  on that person's Home tab, they answer it there, and `close_coach_question` removes it.
  `remind_coach_question` counts a reminder. Ids are unique per person.
- The two files sit in the same folder as the coaching log (`TT_GITHUB_LOG_PATH`, or beside
  `TT_GITHUB_PATH`), and every tool checks the name against the people in `data.json`. The token
  needs Contents: read and write on the store repo, as for the other writes.

A person who turned **Garmin and coach** off in the app (`features[name].garmin.on` is false) gets
nothing written for them: `write_coaching`, `add_coach_question` and `remind_coach_question` refuse,
`write_run` changes the session but skips its note, and `people` and `progression` show the switch
(`coach_on`, `coach_off`).

Three of the writes are worth knowing the shape of before using them:
- `write_coaching` is **per person** - Daniel and Cerys can get different notes on the same
  session, and usually should. Its `targets` set the weight for one exercise's next session and
  need a why when the kg differs from what `progression(person)` says.
- `write_machine_step(exercise, step)` writes one `Step: <exercise> = <kg>` line into a session's
  setup note and touches no other text. `progression.py` reads it as the machine's smallest jump.
- `write_run` / `write_session_notes` carry **three** notes, not two: `recording` (how to
  record it on the watch - start, laps, end, what to report back) is deliberately separate
  from `warmup`, because the lap plan has to be rewritten whenever a session's structure
  changes and doing that shouldn't mean re-sending months of hand-written mobility work.
  The app draws it as its own collapsed block above the warm-up.
- `write_session_notes` is **not** per person. Warm-up / cool-down notes live on the *program*, so one text
  is shared by both people; name whoever a line is for. It also **replaces** the field by default,
  and those notes are long hand-written mobility blocks - so call `session_notes(session)` first
  and pass `append=True` when you're adding a line rather than rewriting the lot. The previous
  text is returned on every write, so a bad one can be put straight back.
- `write_run` is the one place the coach owns program **structure**. Each person has their own
  run session (`Run: Daniel`, `Run: Cerys` - the `person` field on the session, which is also
  what hides it from the other one), and Daniel's instruction is that the coach prescribes the
  optimal run each week from the data, in whatever format the data calls for. It replaces the
  exercise list outright, so call `run_session(person)` first; the whole previous session comes
  back for a revert. `Cardio: Endurance + Core` stays as the untouchable backup.

Then in Claude you just ask, e.g. *"You're my coach - review my last two weeks against my goals
and tell me what to change,"* and it calls these tools itself.

## Setup (once, on the laptop)

### 1. Requirements
- Python 3.10+
- `python -m pip install mcp truststore`  (use `python -m pip`, not bare `pip`, if pip isn't on
  PATH). `truststore` makes SSL use the OS trust store - needed if antivirus/proxy TLS inspection
  causes `CERTIFICATE_VERIFY_FAILED`.
- Verify with `python mcp-coach/test_connection.py` after filling in `.mcp.json`.

### 2. Point it at your data
Use the **GitHub store** the app syncs to (recommended, always current):
- `TT_GITHUB_REPO`  - `Daniel0469/Training-Data`
- `TT_GITHUB_TOKEN` - a fine-grained token with **Contents: read** on that repo
- `TT_GITHUB_PATH`  - optional, default `data.json`

…or a local export file instead: `TT_DATA_FILE=/path/to/training-data-YYYY-MM-DD.json`.

Quick sanity check (no Claude needed):
```
python server.py --selftest /path/to/an-export.json
```

### 3. Register it with Claude

**Claude Desktop** - edit `claude_desktop_config.json`
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

**Claude Code** - from the repo:
```
claude mcp add training-tracker -- python mcp-coach/server.py
```
then set the `TT_GITHUB_*` env vars in your shell (or use `claude mcp add -e KEY=value …`).

## Notes
- **Read-only** by design (it analyses; it never changes your logs). Writing goals / coach notes
  back is a possible later addition.
- The token is read from the environment - **don't commit it**. Keep it in the Claude config /
  your shell only.
- Data is fetched fresh on each call, so coaching always reflects your latest **synced** data -
  tap **Sync now** in the app after a workout so the coach sees it.
- Works on the laptop where you run Claude, not on the iPhone tracker (matches the split: log on
  the phone, coach on the laptop).
