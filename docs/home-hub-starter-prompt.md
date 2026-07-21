# Home Hub — starter prompt for its own Claude Code project

The Home Hub is a **separate repo and a separate Claude Code project** (see `home-hub-link.md` for
why). This file holds the prompt to open that project with. It lives here only because this repo
existed first — **move it into the hub repo** once that repo has its own `docs/`.

## Before pasting

Checked against this laptop on 2026-07-21: git 2.45 is installed, the **GitHub CLI (`gh`) is not**,
and remotes use **HTTPS + Git Credential Manager** (so no token or SSH key is needed to clone or
push — the saved login is reused). Python is 3.14.1.

### Step 1 — create the repo on github.com

The GitHub CLI isn't installed, so do this in a browser.

1. Go to **https://github.com/new** (sign in as `Daniel0469` if prompted).
2. **Repository name:** `Home-Hub` (hyphen, matching `Training-Tracker`).
3. **Visibility:** select **Private**. It will hold Home Assistant config and device details.
4. Tick **"Add a README file"**. This matters — it makes the repo clonable immediately instead of
   leaving an empty repo that needs an extra push to initialise.
5. Leave .gitignore and licence as *None*.
6. Click **Create repository**.

### Step 2 — clone it

Open **PowerShell** and run these one at a time:

```powershell
cd $HOME\Documents
git clone https://github.com/Daniel0469/Home-Hub.git HomeHub
```

The folder is `HomeHub` (no hyphen) while the repo is `Home-Hub` — that's deliberate, it matches the
existing `Documents\TrainingTracker` ← `Training-Tracker` pattern. Other repos live in
`Documents\GitHub\`; this one goes directly in `Documents\` alongside TrainingTracker.

Expect: `Cloning into 'HomeHub'...` then a warning that you cloned an empty-ish repo, or nothing at
all. If a browser window asks you to sign in to GitHub, approve it — that's Git Credential Manager.

### Step 3 — move the plan in and push it

```powershell
cd $HOME\Documents\HomeHub
mkdir docs
move $HOME\Documents\home-hub-plan.md docs\PLAN.md
git add docs/PLAN.md
git commit -m "docs: initial Home Hub plan"
git push
```

Check it worked — this should print the file and the commit:

```powershell
dir docs
git log --oneline -1
```

If `move` says it can't find `home-hub-plan.md`, it's already been moved; check `dir docs` first.

### Step 4 — (optional) fix the commit email for this repo

Commits are currently authored as `27600885@students.lincoln.ac.uk` (university), not the email on
the GitHub account. It works either way, but commits won't link to the GitHub profile. To use the
account email **for this repo only**:

```powershell
cd $HOME\Documents\HomeHub
git config user.email "danielmorris6904@gmail.com"
```

### Step 5 — open it as a Claude Code project

Either open `C:\Users\danie\Documents\HomeHub` as the working folder in the Claude desktop app, or
from PowerShell:

```powershell
cd $HOME\Documents\HomeHub
claude
```

Then paste the prompt below as the first message.

---

## The prompt

> This is the Home Hub — a new project. Nothing is built yet; the repo contains only `README.md` and
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

## After that — what actually happens next

The hub chat will reply with a `CLAUDE.md` and a two-list plan. **Everything past that waits on
hardware**, so don't expect to be writing app code the same evening:

1. A **Raspberry Pi 4 or 5** (or any old mini PC / spare laptop that can stay on) with Home Assistant
   installed. This is the real phase 1, and it's a hardware evening, not a coding one.
2. **Pair the devices in Home Assistant** — Levoit (VeSync), Dreo (hass-dreo via HACS), Pro Breeze
   (LocalTuya or Midea, depending on the model number — find it on the unit's label first), Echo Dot
   and the Amazon Air Quality Monitor (both via Alexa Media Player).
3. **Confirm readings appear in HA** before building anything on top of them.

Only then does the hub's own code start. The GitHub token for the shared store isn't needed until
hub phase 5, which is several phases away.

## Notes for later

- When the Pi is up, move the two **Garmin sync jobs** off the Windows laptop onto it — they're
  deterministic Python and currently only run while the laptop is on. Details in
  `home-hub-link.md` (tracker-side item 5).
- The hub needs its **own** fine-grained GitHub token (Contents: read+write on `Training-Data`
  only), separate from the coach and Garmin tokens so it can be revoked on its own. Only needed at
  hub phase 5 — not to get started.
