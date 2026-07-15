# Training Tracker — MCP coaching server

Lets **Claude act as your coach**: it reads Daniel's & Cerys's workouts, PRs, bodyweight, runs
and goals straight from your data and gives feedback toward your goals. Runs locally on your
laptop, on your **Claude subscription — no API billing**.

## What it exposes (read-only)
`people`, `goals(person)`, `recent_sessions(person, limit)`, `session(session_id)`,
`prs(person)`, `bodyweight(person)`, `progress(person, exercise)`.

Then in Claude you just ask, e.g. *"You're my coach — review my last two weeks against my goals
and tell me what to change,"* and it calls these tools itself.

## Setup (once, on the laptop)

### 1. Requirements
- Python 3.10+
- `pip install mcp`  (or `pip install "mcp[cli]"`)

### 2. Point it at your data
Use the **GitHub store** the app syncs to (recommended, always current):
- `TT_GITHUB_REPO`  — e.g. `danielmorris/training-data`
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
        "TT_GITHUB_REPO": "danielmorris/training-data",
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
