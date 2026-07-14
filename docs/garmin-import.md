# Garmin running data → Training Tracker: feasibility & proposal

**Status: research only — nothing built yet.** This documents the options for getting
Garmin runs into the cardio session and recommends an approach for Daniel to approve before any
implementation.

## What we want
Pull a run recorded on a Garmin watch (Garmin Connect) into a cardio session as
distance / time / pace (and ideally splits) — the running fields added in the
"proper cardio/running fields" change. Ideally with as little manual copying as possible.

## The two realistic paths

### 1. Official Garmin Connect API (Activity API) — blocked for us right now
Garmin's **Connect Developer Program** has an **Activity API** that, with the user's consent,
gives approved apps second-by-second activity data (GPS, distance, pace, HR, cadence, splits,
etc.) as the device syncs. That's exactly the data we'd want.

Problems for this project:
- **The Developer Program is currently on hold to new sign-ups.** Existing developer accounts
  keep working, but we can't get new API credentials today, so this path isn't available to a
  fresh personal app.
- Even when open, it's approval-gated (you apply, describe the app, agree to terms) and is aimed
  at businesses/services. It needs **OAuth** and a **server** to receive Garmin's push
  notifications and hold secrets — which breaks our "plain static site, no backend" constraint.
  It only becomes reasonable if/when we add the sync backend (backlog item 2).

**Verdict:** not viable now. Revisit only alongside the sync backend, and only if the program
reopens.

### 2. File export → in-app import (recommended)
Garmin Connect lets you **export any activity** from the web UI as **GPX**, **TCX**, or the
**original FIT** file. We can let the user pick that file in the app and parse it into a run.

- **GPX / TCX are XML** → parseable in the browser with the built-in `DOMParser`, **no
  libraries, no build step** (fits our static-site constraint). TCX is the better source: it
  carries total distance, total time, and per-lap (split) data directly. GPX is trackpoints
  only, so distance/pace must be derived by summing GPS legs — doable but more code and slightly
  less accurate.
- **FIT is a binary format** → needs a parser library bundled in; heavier and against the
  no-dependency grain. Skip unless GPX/TCX prove insufficient.

**Verdict:** recommended. Manual (a few taps: export on phone/web, import here) but zero
approvals, zero backend, zero secrets, and it reuses the running fields we already have.

## Recommended plan (TCX-first import)
Only build once Daniel says go. Sketch:

1. Add an **"Import run (Garmin .tcx/.gpx)"** button on a cardio session's exercise (or in the
   log form), using the same `<input type="file">` pattern the existing data import already uses
   (see `importFile` handling in `js/app.js`).
2. Parse with `DOMParser`:
   - **TCX:** read `Activities/Activity/Lap` → sum `DistanceMeters` and `TotalTimeSeconds`;
     each `Lap` (or `Trackpoint`-derived km) becomes a **split row**.
   - **GPX fallback:** sum haversine distance across `<trkpt>` legs; total time from first/last
     `<time>`; derive pace.
3. Map into the running fields: **Distance (km)**, **Time (mm:ss)**, **Pace** (our existing
   auto-calc can fill pace, or take Garmin's). One row per split, one summary row, or both —
   Daniel's call.
4. Round/format to match manual entry; let the user review before saving (don't auto-save).

Estimated effort: ~half a day for a solid TCX importer with a GPX fallback, all client-side.

## Open questions for Daniel
- Is a **manual export-then-import** acceptable, or is hands-off auto-sync a hard requirement?
  (Auto-sync effectively requires the API + backend and isn't available now.)
- **Splits vs summary:** import each lap as its own row, just the totals, or both?
- Do Cerys's runs also come from Garmin, or another watch/app? (Affects whether we generalise
  beyond Garmin's TCX.)

## Sources
- [Activity API — Garmin Connect Developer Program](https://developer.garmin.com/gc-developer-program/activity-api/)
- [Garmin Connect Developer Program overview](https://developer.garmin.com/gc-developer-program/)
- [Connect API — Garmin Developer Portal](https://developerportal.garmin.com/developer-programs/connect-api)
