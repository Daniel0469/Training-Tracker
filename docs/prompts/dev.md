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
> you handle done with **`resolve_suggestion_tool`**. Today I want: **‹your task›**.

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
- **No AI attribution in commit messages**, ever.

## Notes

- Pushing to `main` **auto-deploys** to <https://daniel0469.github.io/Training-Tracker/> (~1 min).
- The build order is in `docs/PROJECT-STATUS.md` -> *Build order remaining*.
- The Home Hub is a **separate app in its own repo with its own chat**. Don't build hub features
  here - see [../home-hub-link.md](../home-hub-link.md) for the shared data contract.
