# Training Tracker

A workout tracker for two people (Daniel & Cerys). Static site, no build step, no backend —
all data lives in the browser's `localStorage`. Deployable as-is on GitHub Pages.

## Files
- `index.html` — markup, PWA meta tags, dialogs.
- `css/styles.css` — all styling.
- `js/app.js` — state, program data, and all app logic (rendering, save/import/export,
  progressive-overload suggestions, PR detection, the muscle-map summary).
- `manifest.webmanifest`, `icons/`, `sw.js` — PWA installability + offline support.
- `claude-code-handoff.md` — original brief and backlog this project is being worked from.
- `docs/running-import.md` — how the built-in TCX/GPX run importer works (Garmin & Strava).
- `sample-daniel.json` / `sample-cerys.json` — real exported data, used as local test fixtures
  only (see "Notes & decisions" below — not committed to git).

## Running locally
No build step. Serve the folder with any static file server, e.g.:
```
python -m http.server 8080
```
then open `http://localhost:8080`. (Opening `index.html` directly via `file://` mostly works,
but the service worker won't register outside an http(s)/localhost context.)

## Deploying
Push to GitHub and enable Pages on the repo (serve from the root of the default branch, or
`/docs` if you prefer — no build step either way).

## Notes & decisions
- **Sample data is gitignored.** `sample-daniel.json` / `sample-cerys.json` contain real logged
  workout sessions. Since this repo will likely end up on public GitHub Pages, they're kept out
  of version control and used only as local fixtures for testing. If you want them tracked as
  fixtures later, remove the two lines from `.gitignore`.
- **PWA icons are placeholders.** The files under `icons/` were generated programmatically (a
  plain brand-blue icon) just to make the app installable. **TODO: replace with real branding**
  whenever you have a logo — same filenames, same sizes (192, 512, 512 maskable, 180
  apple-touch-icon), and it'll just work.
- **Single `js/app.js`, not further split.** The app logic is one cohesive module (state,
  rendering, save/import/export all interact tightly); splitting further didn't seem to earn
  its keep yet. Worth revisiting if the file grows a lot more.
- **Bump `CACHE_NAME` in `sw.js` on every deploy that touches `index.html`, `css/styles.css`,
  or `js/app.js`.** The service worker is cache-first, so without a version bump, installed
  users keep getting the old cached files indefinitely — the old cache only gets purged when a
  new cache name shows up in `install`/`activate`. (Hit this myself while testing: edited
  `app.js`, reloaded, and kept seeing the old behavior until I bumped the version.)
