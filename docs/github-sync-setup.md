# GitHub sync — one-time setup (free)

Cloud sync keeps Daniel's and Cerys's data in one place (and off-device **backup**), stored in a
private GitHub repo you control. Free. ~5 minutes to set up once.

**Your repos:** app = `Daniel0469/Training-Tracker`, sync data = `Daniel0469/Training-Data`.
Use the **Training-Data** repo for sync (keep code and data separate).

## 1. Create a private repo for the data
Already done: `Daniel0469/Training-Data`. (If starting fresh: **New repository** → **Private** →
Create, leave it empty — the app creates the data file on first sync.)

## 2. Create a fine-grained access token (scoped to just that repo)
GitHub → **Settings → Developer settings → Personal access tokens → Fine-grained tokens →
Generate new token**:
- **Repository access:** *Only select repositories* → pick `training-data`.
- **Permissions:** *Repository permissions → Contents → **Read and write***. (Nothing else.)
- **Expiration:** your choice (you'll re-paste a new one when it expires).
- Generate, then **copy the token** (starts `github_pat_…`) — you only see it once.

## 3. Connect the app
Open the tracker → gear icon → **Cloud sync (GitHub)**:
- **Repo (owner/name):** `Daniel0469/Training-Data`
- **File path:** `data.json` (default is fine)
- **Access token:** paste the token
- **Save sync settings**, then **Sync now**. First sync creates `data.json` in the repo.

Do the same on Cerys's phone/device with the **same repo + a token** (she can use her own
fine-grained token on that repo, or you share one — your call).

## How it behaves
- **Sync now** = pull the other person's changes, merge, then push yours. Workouts (by id) and
  bodyweight (by person+date) **merge safely** both ways — nothing is lost or duplicated.
- Program, names and goals use **last-sync-wins**, so sync after changing those. Each person's
  goal propagates as long as you both sync after editing.
- The **token is stored only on that device** and is **never** included in Export files.
- It's still offline-first: sync is manual (tap **Sync now**); if offline it just retries next time.

## Notes / safety
- A scoped fine-grained token limited to one private repo is the safe choice — if it ever leaks,
  it can only touch that one repo's contents.
- The repo doubles as your backup: even if a phone wipes its localStorage, **Sync now** on a fresh
  install pulls everything back.
- This is the shared store the planned **MCP coaching server** will read (see
  `docs/hub-and-coaching.md`).
