# Home Hub — starter prompt for its own Claude Code project

The Home Hub is a **separate repo and a separate Claude Code project** (see `home-hub-link.md` for
why). This file holds the prompt to open that project with. It lives here only because this repo
existed first — **move it into the hub repo** once that repo has its own `docs/`.

## Before pasting

1. Create the repo — **private** (it will hold Home Assistant config and device details).
2. Clone it under `Documents/`, e.g. `C:\Users\danie\Documents\HomeHub`.
3. Move `C:\Users\danie\Documents\home-hub-plan.md` into it as `docs/PLAN.md`.
4. Open that folder as a new Claude Code project and paste the prompt below.

---

## The prompt

> This is the Home Hub — a new project. Nothing is built yet; the repo is empty apart from
> `docs/PLAN.md`.
>
> **Read `docs/PLAN.md` first.** It's the agreed plan: a home dashboard for plants, chores, room
> climate/air quality, supplies, maintenance and bills, running on a home server (Raspberry Pi)
> alongside Home Assistant, reachable over Tailscale, with a PWA front end on our phones.
>
> **Then read the shared data contract** — it lives in my other app's repo, which is public:
> https://raw.githubusercontent.com/Daniel0469/Training-Tracker/main/docs/home-hub-link.md
> That file is the source of truth for how this app and my existing Training Tracker share data.
> **Don't copy it into this repo and don't redesign it** — if something in it looks wrong, tell me
> and I'll change it on that side.
>
> **Context you need:**
> - My Training Tracker is a working app (static site, GitHub Pages, two people — me and Cerys). It
>   is NOT being merged into this one. Both apps read and write one shared file, `data.json`, in a
>   private GitHub repo `Daniel0469/Training-Data`, via the GitHub Contents API.
> - The tracker side of the link is **already done**: `data.json` now has a `meals` array that syncs
>   to both phones, and its writers retry safely on conflict. This app is unblocked to write meals
>   whenever it's ready.
> - This app's job in that split: **capture** meals (barcode scan + free text) and write them to the
>   store. The tracker **displays** them and feeds them to its AI coach. Don't build nutrition
>   dashboards, targets, or charts here — that's the tracker's half.
>
> **Decisions already made — please don't reopen them unless you think one is actually wrong:**
> Python backend (reuses the tracker's existing GitHub-store code), SQLite, PWA front end, ntfy.sh
> for notifications first (Web Push later), Tailscale for remote access, Home Assistant owns all
> device integration and automations, one shared PIN gate with the token checked on every API
> request, and one generic "tracked item" engine underneath plants/chores/inventory/maintenance/bills
> rather than four bespoke systems.
>
> **Constraints:**
> - The GitHub token for the store is **server-side only**, never in the PWA. I handle tokens myself
>   — tell me what to create and where to put it, don't ask me to paste one into the chat.
> - Don't touch my Training Tracker repo from this project.
> - This app must never be something the tracker depends on. The tracker is used on our phones away
>   from home; this thing lives behind a home VPN.
>
> **What I want from you now — don't write any application code yet:**
> 1. Write this repo's `CLAUDE.md`: stack, conventions, layout, how the shared store works, and the
>    "hub captures / tracker displays" split. Keep it short and specific.
> 2. Tell me the **concrete next steps, split into two lists**: what *I* have to do myself
>    (hardware, accounts, tokens, physical setup) and what *you* can do once I have. Order them, and
>    say which of my steps actually block your work versus which can happen in parallel.
> 3. Flag anything in `docs/PLAN.md` that looks wrong or out of date now you've read the contract.
>
> Phase 1 in the plan is hardware — Home Assistant on a Pi with my existing devices paired (Levoit
> air purifier, Dreo fan, Pro Breeze dehumidifier, Echo Dot, Amazon Air Quality Monitor). Assume none
> of that exists yet. Ask me what I've actually got before assuming.

---

## Notes for later

- When the Pi is up, move the two **Garmin sync jobs** off the Windows laptop onto it — they're
  deterministic Python and currently only run while the laptop is on. Details in
  `home-hub-link.md` (tracker-side item 5).
- The hub needs its **own** fine-grained GitHub token (Contents: read+write on `Training-Data`
  only), separate from the coach and Garmin tokens so it can be revoked on its own. Only needed at
  hub phase 5 — not to get started.
