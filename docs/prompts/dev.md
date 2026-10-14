# Development chat - starter prompt

Use this in a Claude Code chat **opened on the Training Tracker project folder**
(`C:\Users\danie\Documents\TrainingTracker`), which auto-loads `CLAUDE.md` and saved memory.
Coaching stays in its own chat; see [coaching.md](coaching.md) and [running.md](running.md).

**Before first use:** if `.mcp.json` or anything under `mcp-coach/` changed since last time, fully
restart Claude Code so the `training-tracker` tools reload. New tools do not appear until you do.

---

## Paste this to start

> You're the developer on **Training Tracker** - a two-person workout + health tracker on its way to
> an all-round health & fitness hub. **First read `docs/PROJECT-STATUS.md` and `CLAUDE.md`** for the
> full state, decisions and conventions. Then check the in-app improvement backlog with the
> `training-tracker` **`suggestions`** tool: **auto-apply the easy/safe ones** (verify in the browser
> - light + dark, no console errors - commit per feature, bump `sw.js` CACHE_NAME on any shell
> change, then push to deploy), and **list the harder/riskier ones for me to decide**. Mark each one
> you handle done with **`resolve_suggestion_tool`**. Also read
> **`docs/coach-tooling-brief.md`** - the coaching chat's own account of what it can and cannot do,
> with the blocked coach-owned jobs and a suggested build order. Today I want: **‹your task›**.

---

## What the chat must not get wrong

These are in `CLAUDE.md` too, and they are the ones that cost real time when missed.

- **Ask before implementing.** Investigate, put the open decisions up with `AskUserQuestion`, and
  only build once they are answered. A wrong guess means rework, or worse, silent changes to real
  training data.
- **Prototype before pushing.** Build locally against a **copy** of the store
  (`scratchpad/proto_term.py` is the pattern) and show screenshots - both people, both themes -
  before anything is committed. Pushing auto-deploys to both phones.
- **Bump `CACHE_NAME` in `sw.js`** on any change to a cached shell file. The service worker is
  cache-first; without a bump, installed users keep the old files.
- **Keep the Guide, the README and these prompts current** when a feature or a decision changes.
- **A coach-owned job can be impossible, not just undone.** Before assigning work to the coaching
  chat, check the tool can actually do it - `docs/coach-tooling-brief.md` lists what cannot be
  reached today. The 25 Sep settings-box cleanup and the 6 Oct warm-up ramps were both handed over
  as coach jobs and neither is possible on a lifting exercise, because `write_program_change` can
  only edit `sets` and `target`.
- **No AI attribution in commit messages**, ever.

## Notes

- Pushing to `main` **auto-deploys** to <https://daniel0469.github.io/Training-Tracker/> (~1 min).
- The build order is in `docs/PROJECT-STATUS.md` -> *Build order remaining*.
- **Design v3 restyle: dark done** - spec in `docs/design-v3.md` (dark first, light parked until
  Daniel asks). Step 1 (fonts, tokens, header + icon tabs, shared shapes) and every screen are built in dark,
  pushed on 13 Oct (tt-v151). Light mode is the remaining step, when Daniel asks for it. New UI uses the v3 tokens (`--line-2`,
  `--ink-2`, `--nav`, `--on-brand`, `--gold`, `--gold-ink`, `--pr-tint`), `var(--mono)` / `.num` for
  every number, line icons (`ico()` in `js/app.js`, `svg.ico` in CSS) rather than emoji, and
  `var(--on-brand)` - never `#fff` - for text on a brand fill. Session-only card styles are scoped
  under `#exForm` because `.ex`, `.superset` and `.notes` are shared with Program/Progress/History.
- **Lift targets are built, not typed** (14 Oct): the setup dialog has Sets, Reps min-max and an
  extra; `joinTarget` makes "3x8-12 each leg" and `splitTarget`/`parseRange` read it back (a
  single count like "2x5" is 5-5). Non-lifts keep a free-text target. `restSec` on an exercise is
  its suggested rest; the rest bar shows it and turns gold when reached, still counting. The
  header kicker shows the workout time on Session. The Smith tick covers any barbell lift.
- **Machine settings are per person** (13 Oct): `state.machineSettings[person][exercise name] =
  {text, updatedAt}`, read/written via `msGet`/`msSet`, merged per entry (newer wins). The program
  exercise has no `notes` any more, and the coach MCP cannot write settings. An install without
  sync migrates old `notes` on load; synced phones got them from `scratchpad/apply_machine_settings.py`.
- The Home Hub is a **separate app in its own repo with its own chat**. Don't build hub features
  here - see [../home-hub-link.md](../home-hub-link.md) for the shared data contract.
