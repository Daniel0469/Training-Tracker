# Health & fitness hub + AI coaching — design proposal

**Status: proposal, nothing built.** Daniel wants this to grow into a shared health & fitness hub
for him and Cerys, with Claude acting as their coach. This lays out how to get there for **free**,
in phases he can approve one at a time. Decisions from the planning round: backend is fine *only
if free* (GitHub as a possible store); coaching saved for later; runs via file import; iPhone for
tracking, laptop for everything else.

---

## B1 · Free sync backend (so both people share one dataset)

Today data is per-device localStorage, shared by manual Export/Import. To make Daniel and Cerys
see one another's logs automatically we need a shared store. Three free options:

| Option | How it works | Free? | Trade-offs |
|---|---|---|---|
| **GitHub-as-store** (recommended) | App reads/writes one JSON file in a **private repo or gist** via the GitHub REST API using a fine-grained token. Sync = pull → merge → push, reusing our existing **upsert-by-id** merge. | Yes, unlimited | Token lives in the app (scope it to just that repo); not real-time (sync on open / on a button); needs conflict-tolerant merge (we have it). |
| **Supabase** free tier | Hosted Postgres + auth + realtime. | Yes (project **pauses after ~1 week idle**; limited rows) | Another account; realtime is nice but overkill for 2 people; pausing is annoying. |
| **Cloudflare Workers/Pages** free tier | Tiny serverless API + KV/D1 store; also the natural home if we ever do server-side Claude calls. | Yes (generous) | More setup than GitHub; only needed if we want a real API layer. |

**Recommendation:** **GitHub-as-store.** It's genuinely free, needs no server, fits the existing
merge logic, and Daniel already uses GitHub for hosting. The app gets a "Sync" button (and
optional sync-on-open) that pulls the shared JSON, merges, and pushes. Security: use a
**fine-grained PAT** limited to the one private repo; treat it like a password (it's a 2-person
personal app, so a scoped token in the app is an acceptable trade-off — documented, not ideal).

---

## B2 · The hub shape

**Recommendation: grow *this app* into the hub**, not a separate site. It already has workouts,
bodyweight, running, progress and a program editor. Add over time: a **Records/PRs** page,
**per-person goals**, and the coaching entry point. The B1 store provides the shared layer so both
see everything; the B3 MCP server lets Claude read that same shared data to coach. One app, one
dataset, two people.

---

## B3 · AI coaching — Claude as coach

Goal: Claude reviews each workout and coaches Daniel and Cerys toward their goals, "either linked
or automatically pulling up the history," with a per-person **goals** setting. Three ways to do
it, cheapest first:

### 1. MCP server (recommended) — free, automatic history pull
A small **local MCP server** on the laptop exposes the training data to Claude
Desktop/Code/claude.ai as tools + resources:
`list_sessions(person)`, `get_session(id)`, `get_prs(person)`, `get_bodyweight(person)`,
`get_runs(person)`, `get_goals`/`set_goals`, `add_coach_note`. Then in Claude you say *"review
Cerys's week and coach her toward her goals,"* and Claude **pulls the history itself** and
responds as coach.
- **Cost: free.** The reasoning runs on Daniel's **Claude subscription**, not the paid API.
- **Data source:** the server reads the shared dataset from the **B1 GitHub store** (or an
  exported JSON). So B1 and B3 pair up.
- **Effort:** ~a few hundred lines (Node or Python + Anthropic's MCP SDK); runs via one line in the
  Claude client config. Works on the laptop, not the iPhone tracker — which matches Daniel's split.

### 2. Manual "Coach brief" export — zero setup, also the Obsidian artifact
A button that bundles a person's recent history + PRs + bodyweight + goals into a **ready-to-paste
Markdown prompt**. Paste into Claude for coaching; drop the same file into an **Obsidian** vault
(Daniel asked about Obsidian — a phone PWA can't write a vault, but a Markdown export he syncs into
a vault on the laptop works). Free, no server; the fallback if the MCP server isn't running.

### 3. Automatic on-save analysis — **not free**
Call the Anthropic API from a Cloudflare Worker / GitHub Action (key held as a secret) to write
feedback on every save. This is the only path that **costs money** (per-analysis API billing), so
it's documented for completeness but **not recommended** given the "keep it free" constraint.

**Per-person goals** (small, needed by all three): a goals text field per person in settings,
stored in state and included in export/sync so the coach can read them.

Reference: Daniel pointed at the Skool "Athlete AI" community (an "Athlete OS" coaching-dashboard
course) as the direction. It's login-gated; we take it as inspiration for the *shape* (goals →
data → weekly review → plan), not as something to copy.

---

## B4 · Why file-import for runs, not the Strava/Garmin APIs
Covered in `docs/running-import.md`: Strava's API forbids feeding its data into AI; Garmin's dev
program is on hold; self-exported files are your own data and avoid both. The built-in TCX/GPX
importer is the terms-clean path and needs no backend.

---

## Suggested order (each is its own approval)
1. **Per-person goals** (tiny; unlocks coaching context) — could even land in Batch A if wanted.
2. **B1 GitHub sync** (shared dataset; also the safety net against localStorage loss).
3. **B3 MCP server** reading the B1 store (the actual coaching).
4. **Coach-brief / Obsidian Markdown export** (nice fallback; low effort).

Automatic backup / data-loss protection is effectively solved by step 2 (the shared store doubles
as an off-device backup) — worth prioritising since all data is still local today.

## Open questions for Daniel
- OK to store a scoped GitHub token in the app for sync, or prefer a different free store?
- Should goals be simple free-text, or structured (target lifts / bodyweight / weekly mileage)?
- Start coaching with the **MCP server**, or the **paste-in Coach-brief** first?
