# How to start new Claude chats (so they have full context)

You run two kinds of chat, both **in Claude Code, opened on the Training Tracker project folder**
(`C:\Users\danie\Documents\TrainingTracker`). Keep them separate:
- **Development chat** — build the app / hub, and action the in-app suggestion backlog.
- **Coaching chat** — Claude coaches Daniel & Cerys from their live data.

---

## ✅ Before ANY new chat (do these once each time)
1. **Open the project folder** in Claude Code (`C:\Users\danie\Documents\TrainingTracker`). This
   auto-loads `CLAUDE.md` (conventions) and my saved memory — so the chat already knows the project.
2. **If you changed the MCP server or `.mcp.json` since last time, fully restart Claude Code** so
   the `training-tracker` tools reload. (New tools won't appear until you do.)
3. That's it — everything else lives in the repo (`docs/PROJECT-STATUS.md` is the full handoff).

**What's guaranteed loaded:** `CLAUDE.md` + memory (auto). **Point the chat at:** `docs/PROJECT-STATUS.md`
for the complete picture (the starter prompts below already do this).

---

## 🛠️ Development chat — starter prompt
Paste this, then add today's task:

> You're the developer on **Training Tracker** — a two-person workout + health tracker on its way to
> an all-round health & fitness hub. **First read `docs/PROJECT-STATUS.md` and `CLAUDE.md`** for the
> full state, decisions and conventions. Then check the in-app improvement backlog with the
> `training-tracker` **`suggestions`** tool: **auto-apply the easy/safe ones** (verify in the browser
> — light + dark, no console errors — commit per feature, bump `sw.js` CACHE_NAME on any shell
> change, then push to deploy), and **list the harder/riskier ones for me to decide**. Mark each one
> you handle done with **`resolve_suggestion_tool`**. Today I want: **‹your task›**.

Notes:
- Pushing to `main` **auto-deploys** to https://daniel0469.github.io/Training-Tracker/ (~1 min).
- The build order is in `docs/PROJECT-STATUS.md` → *Build order remaining* (next: Garmin MCP, then
  the hub).

## 🧠 Coaching chat — starter prompt
Full version + follow-ups are in **`docs/coaching-prompt.md`**. Short version to paste:

> You are the S&C coach for **Daniel** and **Cerys**, who share one Training Tracker. Use the
> `training-tracker` MCP tools (don't ask me for data): `people`, then per person `goals`,
> `recent_sessions`, `prs`, `bodyweight`, `progress`; read their session `feedback` notes closely.
> Then push concise, actionable coaching into their app with **`write_coaching(person, overall,
> by_exercise, by_session)`** — prefer **`by_session`** = {exact session name: focus note} and
> **`by_exercise`** = {exact exercise name: a concrete next step} over a generic `overall`. They see
> it after their app syncs. Be specific, tie to goals + recent numbers, progress lifts
> in small jumps, encourage Cerys, and treat pain notes conservatively (deload / mobility / "get it
> checked", never diagnose). Start by reviewing both and give me your read, then write coaching.

---

## Recurring rituals
- **Weekly coaching (semi-auto for now):** once a week, open a coaching chat and paste the prompt.
  *(Later option: a paid GitHub Action to do it hands-off — see PROJECT-STATUS "Automation".)*
- **Backlog review:** whenever, open a dev chat — it'll pull your 💡 in-app suggestions and action
  them.

## Quick reference
- **Live app:** https://daniel0469.github.io/Training-Tracker/  · **App repo:** Daniel0469/Training-Tracker
- **Sync/data repo (private):** Daniel0469/Training-Data (`data.json`)
- **MCP config:** `.mcp.json` (gitignored, on this laptop). Coach tools: `people`, `goals`,
  `recent_sessions`, `session`, `prs`, `bodyweight`, `progress`, `write_coaching`, `coaching_history`,
  `suggestions`, `resolve_suggestion_tool`.
- **Key docs:** `PROJECT-STATUS.md` (handoff), `coaching-prompt.md`, `github-sync-setup.md`,
  `mcp-coach/README.md`, `hub-and-coaching.md`, `running-import.md`.
- **Home Hub (separate app, separate repo + chat):** `home-hub-link.md` (shared `meals` contract +
  the work needed on this side) and `home-hub-starter-prompt.md` (the prompt to open the hub's own
  Claude Code project with). Don't build hub features in this repo.
