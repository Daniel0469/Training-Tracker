# Supabase setup (Phase 4)

The tracker's shared store moves from `data.json` in a private GitHub repo to a Supabase project.
The schema is `docs/supabase-schema.sql`. The record shapes the app, the coach server, the Garmin
server and the Home Hub all agree on are in the second half of this page.

Keys are typed by Daniel, never pasted into a chat. The project URL and the publishable key are
not secret. The secret key is, and it only goes into `.mcp.json` and the Home Hub add-on options.

## Part 1 - Daniel's steps

There is no separate test project. The real project starts empty with no phones connected, so the
first move into it is the test. If anything goes wrong before the family phones join, empty the
tables and run the move again from the family exports and the GitHub `data.json` backup.

1. Create the project at supabase.com. Name and region do not matter to the SQL. Keep the Data API
   on. Leave "Automatically expose new tables" off and "Enable automatic RLS" on. The schema
   writes every grant and policy out, so it works with those settings.
2. Turn sign-ups off: Authentication, Sign In / Providers, switch off "Allow new users to sign up".
3. Add the one family login: Authentication, Users, Add user, "Create new user", with an email and
   a password. Tick the auto-confirm box. This one login is shared by everyone.
4. Open the SQL editor, paste the whole of `docs/supabase-schema.sql` and run it. It can be run
   again later without harm.
5. In the same SQL editor run this once, so the login from step 3 is a family member:

   ```sql
   insert into public.family_members select id from auth.users on conflict do nothing;
   ```

6. Find three values under Project Settings: the project URL, the publishable key and the secret
   key (API Keys). The publishable key is the one starting `sb_publishable_`, the secret key the
   one starting `sb_secret_`.
7. Put the secret key and the URL in `.mcp.json` on the laptop (gitignored). Wait with this step
   until the server adapters have shipped, because the moment `TT_SUPABASE_URL` is set the servers
   stop using GitHub. Add both lines to the `env` block of `training-tracker` (the coach) and of
   `training-garmin` and `training-garmin-cerys`:

   ```json
   "TT_SUPABASE_URL": "<project url>",
   "TT_SUPABASE_SECRET_KEY": "<secret key>"
   ```

   Type the key into the file yourself. Delete the `TT_SUPABASE_URL` line to go back to GitHub.
   Restart Claude Code afterwards, because the servers load once at startup.
8. Put the same two values into the `supabase_url` and `supabase_secret_key` options of both the
   Home Hub and the Garmin Sync add-ons (Home Assistant, each add-on's Configuration tab), typed by
   you. The hub uses them for its meals and weigh-ins, the daily keep-alive call and the nightly
   backup.
9. Move the data over (Part 2) and run the check.
10. On your phone and Cerys's open the app, then Admin, and enter the project URL, the publishable
    key and the family email and password. The first sign-in uploads that phone's own data, and the
    local copy stays until the upload reads back the same. The publishable key is safe to type on a
    phone. It does nothing without the sign-in. Use the two phones for a day or two.
11. Then the family phones, one at a time, the same way. Faster: on a connected phone open Admin, then Family
    storage, tap Show setup code and type the family password. Scan the code with the new phone in person, or
    paste the link into Paste a setup code and tap Use code, or type the short code (like K7P-4QX) into
    Type a pairing code and tap Pair. The codes hold the family password, so never screenshot them or send them
    in a message. If one leaks, change the family password in Supabase (Authentication, then Users) and
    show a new code on each phone.
12. Version 2.0.3 added the pairing table and its functions. If the project was set up earlier, open the SQL
    Editor, paste the whole of `docs/supabase-schema.sql` and run it again. It is safe to run again and
    changes nothing that already exists. Without this step the short code shows a message that it is not
    ready, and the QR code still works.
13. To save typing the project address and key on each new phone, open `js/family.js` and type the project URL
    and the publishable key between the quotes of `FAMILY_PROJECT`. Both are safe to commit, but the family
    email and password never go in that file. A phone's own saved values win over the file.

## Part 2 - Moving the data over

All three scripts are in `scratchpad/`. They read the URL and the secret key from the
environment, never from arguments or files, so type them into your own terminal:

```
set TT_SUPABASE_URL=<project url>
set TT_SUPABASE_SECRET_KEY=<secret key>
python scratchpad/migrate_to_supabase.py --dry-run --data data.json --log coaching-log.json --coach coach --family mum.json brother.json
python scratchpad/migrate_to_supabase.py            --data data.json --log coaching-log.json --coach coach --family mum.json brother.json
python scratchpad/verify_migration.py               --data data.json --log coaching-log.json --coach coach --family mum.json brother.json
```

`--data` is a copy of `data.json` from the data repo. `--log` is `coaching-log.json`. `--coach` is
the folder holding `<name>/profile.md` and `<name>/decisions.md`. `--family` takes any number of
export files from other phones. Running the migration twice is safe. The merge rules make it
idempotent. `--dry-run` only prints counts.

## Part 3 - Record shapes

Every synced thing is one row of `records`: `kind`, `key` (together the primary key), `person`,
`body` (jsonb), `updated_at` (ms, 0 when the record has no stamp), `deleted_at` (ms, null while
live), `server_at` (set by the server, the pull cursor) and `by` (who wrote it).
`body` is the app's own object, unchanged, unless the table says otherwise.

| kind | key | person | body | updated_at |
|---|---|---|---|---|
| `log` | the log id as text | log.person | the log | log.updatedAt |
| `bodyweight` | `<person>:<date>` | person | the entry | updatedAt |
| `measurement` | `<person>:<date>` | person | the entry | updatedAt |
| `meal` | the meal id | meal.person | the meal | updatedAt |
| `suggestion` | the id | suggestion.person | the suggestion | newest of updatedAt, doneAt, approvedAt, declinedAt |
| `program_change` | the id | change.person | the change | newest of updatedAt, at, appliedAt, declinedAt, withdrawnAt |
| `coach_question` | `<person>:<question id>` | person | the question | updatedAt |
| `person` | the name | the name | `{slot, weight, goal, programId, programIdAt}` | 0 |
| `person_data:<field>` | the person | the person | that person's value from `data[field]` | newest `updatedAt` or `updated` inside it |
| `program` | the program id, e.g. `p-daniel-cerys` | null | the app's program object | updatedAt as ms |
| `family` | `adminPin` | null | the PIN object | updatedAt |
| `coach_file` | `<person>/<file>`, e.g. `Daniel/profile.md` | the person | `{text}` | write time |
| `coach_log` | the entry id | entry.person | the coaching history entry | the entry id (it is a ms time) |

`<field>` is one of `coaching`, `hrZones`, `machineSettings`, `progression`, `features`,
`nutritionTargets`, `limiters`, `wellness`, `racePredictions`. A value that is not an object is
stored as `{"_v": value}`.

**Deleting.** A delete sets `deleted_at` and keeps the body. A row is deleted when `deleted_at` is
set and `updated_at` is not newer than it, so editing a deleted record to bring it back works.
This replaces `deletedLogs`, `deletedBodyweights` and `deletedMeals`. A tombstone with no record
behind it is a row with a stub body (`{id}`, or `{person, date}`) and `deleted_at`.

**Person.** `slot` is the position in `people`, `weights` and `goals`. `weight` and `goal` are the
text from those arrays. `programId` and `programIdAt` are `programIds[person].id` and
`programIds[person].updatedAt` from the app.

**Programs.** The app keeps `state.programs[id]` and `state.programIds[person]`, and the table
mirrors them exactly. A `program` row's key is the program id and its body is the app's program
object unchanged: `{id, name?, members, version, updatedAt, updatedBy, order, sessions}`. Daniel and
Cerys share one program, `p-daniel-cerys`, and each family phone has its own. A person row's
`programId` says which program that person trains. `version` is the number to pass as
`base_version` to `save_program`.

In the payload the servers and the app exchange, `programs` is `{id: program}`, `programIds` is
`{person: {id, updatedAt}}` and `program` is the first person's program, kept for the coach. An
old payload with only `program` is read the way the app reads it (`wrapProgram`): the id is `p-`
plus the people's names in lower case joined with `-`, `members` is the people, `version` is the
old version or 1, and every person is pointed at it. `tt_records.prog_of(data, person)` is the
Python `progOf`: the program the person's `programId` names, else one listing them, else `program`.
The servers have it as `_prog_of(data, person)`.

**Merging.** The table merges on every write, so a client sends whole records and the table keeps
the right keys. Incoming newer or equal: the stored keys stay unless the new body has the same key.
Incoming older: the stored body wins and the incoming only adds keys it lacks. `updated_at` and
`deleted_at` only ever go up. This is the app's `mergeRecord`. A body that carries
`"__replace": true` is stored as sent, so a removed key stays removed. The coach servers use it.
The app should not.

The coach and Garmin servers read the table, change the data, and send only the rows that changed.
A row they send is never older than the one they read, so their edit wins over what they read. If
another writer touched a row in between, the server reads again and redoes the change.

**Saving a program.** The app saves a program with the `save_program` function, not an upsert:
`supabase.rpc('save_program', { id, body, base_version })`. It returns `'ok'`, and the stored
version becomes `base_version + 1`. It returns `'conflict'` when the stored version is not
`base_version`. On `'conflict'` read the row again and redo the edit.

**Drafts.** One row per `(person, session_key)`. The body is the form being typed. A write with an
older `updated_at` than the stored one is ignored. Drafts untouched for 24 hours are given a
`deleted_at` by `tt_keepalive`.

**Keep-alive.** The Home Hub calls `tt_keepalive()` once a day with the publishable key
(`POST /rest/v1/rpc/tt_keepalive`). It touches `heartbeat` and soft-deletes old drafts.

**Reading and pulling.** Pull with `server_at > cursor` and keep the largest `server_at` seen as the
next cursor. The pulled `server_at` is a string, so pass it back unchanged.

**Not stored.** `exportedAt` is not a record. A log, meal, suggestion or program change with no
`id` is skipped, as is a bodyweight or measurement without a person and a date. The order of a list
is not stored. `scratchpad/test_records.py` is the round trip check for the old and the new payload shape, and
`mcp-coach/tt_records.py` is the Python mapping (`mcp-garmin/tt_records.py` is a copy).
