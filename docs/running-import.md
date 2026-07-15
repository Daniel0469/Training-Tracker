# Running import (Garmin / Strava) → Training Tracker

**Status: BUILT (file import).** The log form now imports a run file into a running exercise's
Distance/Time/Pace fields. This doc records how it works and why file-import — not the
Garmin/Strava APIs — is the right approach for this app.

## How to use it (on the laptop)
1. Export the run as a file:
   - **Garmin Connect** (web): open the activity → gear/⋯ menu → *Export to TCX* (or GPX).
     TCX is preferred — it carries per-lap splits and exact distance/time.
   - **Strava**: *Export GPX* on an activity, or *Export Original* (the underlying TCX/FIT).
     Strava also has a full account *Bulk Export* that includes every connected device's files.
2. In the tracker, open **Log**, pick a cardio session with a running exercise
   (Distance/Time/Pace columns), and click **⬆ Import run (TCX/GPX)** on that exercise.
3. Each lap becomes a **split row** (TCX); a GPX with no laps imports as one summary row. Pace is
   auto-computed. Review, then **Save session** as normal.

## Implementation notes
- Client-side only, no libraries: parsed with the browser `DOMParser`
  (`parseTcx`/`parseGpx`/`importRunIntoCard` in `js/app.js`).
- **TCX:** each `<Lap>` → `{DistanceMeters, TotalTimeSeconds}` → a split row.
- **GPX:** sums haversine distance across `<trkpt>` legs; time from first/last `<time>`; one
  summary row (GPX has no lap structure).
- Time is written as `M:SS` (minutes may exceed 59) so the pace calc round-trips.

## Why file import, not the APIs
- **Strava API forbids AI use.** Its policy (June 2026) bars using API data "in connection with
  the development, training, evaluation, or operation of any AI Application," explicitly including
  "ingestion into a context window or working memory." Since the goal is Claude-as-coach, routing
  runs through the Strava API would breach its terms. It also now needs a paid subscription, only
  shows a user their own data, and blocks intermediaries.
- **Garmin's Connect Developer Program is on hold** to new sign-ups, and needs OAuth + a server.
- **Files you export yourself are your own data** and sidestep both API agreements — and work
  offline with no approvals, no backend, no secrets.

## Possible later enhancements
- Derive **per-km splits from GPX** (segment trackpoints by distance) so GPX matches TCX's split
  granularity.
- Pull **heart rate / cadence** columns if present.
- FIT support (binary; would need a small parser bundled — only if TCX/GPX prove insufficient).
