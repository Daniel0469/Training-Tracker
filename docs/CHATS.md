# How to start new Claude chats (so they have full context)

You run three kinds of chat, all **in Claude Code, opened on the Training Tracker project folder**
(`C:\Users\danie\Documents\TrainingTracker`). Keep them separate - each has a different job and
loads different tools.

| Chat | Prompt | What it does |
|---|---|---|
| **Development** | [prompts/dev.md](prompts/dev.md) | Build the app, action the in-app suggestion backlog |
| **Coaching** | [prompts/coaching.md](prompts/coaching.md) | Coach Daniel & Cerys from their live data |
| **Running** | [prompts/running.md](prompts/running.md) | Pull runs off the watches, enrich them, write the next prescription |

The Home Hub is a **separate app in its own repo**, with its own chat and its own prompt -
[home-hub-starter-prompt.md](home-hub-starter-prompt.md). Don't build hub features in this repo.

---

## Before ANY new chat

1. **Open the project folder** in Claude Code. This auto-loads `CLAUDE.md` (conventions) and saved
   memory, so the chat already knows the project.
2. **If you changed `.mcp.json` or anything under `mcp-coach/` or `mcp-garmin/` since last time,
   fully restart Claude Code** so the tools reload. New tools will not appear until you do.
3. That's it. Everything else lives in the repo, and each starter prompt points the chat at what it
   needs.

**What's guaranteed loaded:** `CLAUDE.md` + memory. **The full handoff** is
[PROJECT-STATUS.md](PROJECT-STATUS.md); the starter prompts already point at it.

---

## Keeping the prompts honest

**When something is added, changed or decided, update the prompt that owns it** - the same rule the
in-app Guide and the README follow. A starter prompt describing a week, a tool or a convention that
no longer exists is worse than no prompt, because the chat acts on it confidently. These are the
only docs read by a chat that has no other context.

---

## Recurring rituals

- **Weekly coaching:** open a coaching chat and paste [prompts/coaching.md](prompts/coaching.md).
- **After a run block:** open a running chat and paste [prompts/running.md](prompts/running.md) to
  pull the watches and re-prescribe.
- **Backlog review:** open a dev chat - it pulls the in-app suggestions and actions them.

## Quick reference

- **Live app:** <https://daniel0469.github.io/Training-Tracker/> · **App repo:** Daniel0469/Training-Tracker
- **Sync/data repo (private):** Daniel0469/Training-Data (`data.json`)
- **MCP config:** `.mcp.json` (gitignored, on this laptop).
  - **`training-tracker`** (coach): `people`, `goals`, `recent_sessions`, `session`, `prs`,
    `bodyweight`, `progress`, `running_form`, `limiters`, `write_limiter`, `write_coaching`,
    `session_notes`, `write_session_notes`, `run_session`, `write_run`, `write_log_entry`,
    `coaching_history`, `program_changes`, `write_program_change`, `suggestions`,
    `propose_suggestion_tool`, `resolve_suggestion_tool`.
  - **`training-garmin`** (Daniel) and **`training-garmin-cerys`** (Cerys), one per person:
    `garmin_recent_runs`, `garmin_recent_activities`, `garmin_activity`, `garmin_import_run`,
    `garmin_enrich_session`, `garmin_fill_pending`, `garmin_wellness`, `garmin_hr_zones`,
    `garmin_refresh_metrics`.
- **Key docs:** [PROJECT-STATUS.md](PROJECT-STATUS.md) (handoff), [methods/](methods/) - all the
  training reasoning, indexed by [methods/coaching-method.md](methods/coaching-method.md) -
  [term-routine.md](term-routine.md) (the current week),
  [github-sync-setup.md](github-sync-setup.md), [running-import.md](running-import.md),
  `mcp-coach/README.md`.
