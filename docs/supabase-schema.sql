-- Training Tracker: Supabase schema (Phase 4).
-- Paste the whole file into the Supabase SQL editor and run it. It is safe to run again.
-- Setup steps: docs/supabase-setup.md.

-- records: every synced thing is one row. (kind, key) is unique. The body is the app's own object.
-- updated_at is the record's own edit time in ms (0 when unstamped). deleted_at is the delete time
-- in ms, null while the record is live. server_at is when the server last changed the row and is
-- the cursor the apps pull by.
create table if not exists public.records (
  kind        text        not null,
  key         text        not null,
  person      text,
  body        jsonb       not null default '{}'::jsonb,
  updated_at  bigint      not null default 0,
  deleted_at  bigint,
  server_at   timestamptz not null default now(),
  by          text,
  primary key (kind, key)
);
create index if not exists records_server_at_idx on public.records (server_at);
create index if not exists records_person_kind_idx on public.records (person, kind);

-- drafts: the form being typed in right now, one row per person and session. Newest edit wins.
create table if not exists public.drafts (
  person       text        not null,
  session_key  text        not null,
  body         jsonb       not null default '{}'::jsonb,
  updated_at   bigint      not null default 0,
  deleted_at   bigint,
  device       text,
  server_at    timestamptz not null default now(),
  primary key (person, session_key)
);
create index if not exists drafts_server_at_idx on public.drafts (server_at);

-- heartbeat: one row, touched daily by tt_keepalive() so a free project is not paused.
create table if not exists public.heartbeat (
  id          int         primary key default 1 check (id = 1),
  touched_at  timestamptz not null default now()
);
insert into public.heartbeat (id) values (1) on conflict do nothing;

-- family_members: the sign-in users allowed to touch the data. Fill it with
--   insert into public.family_members select id from auth.users on conflict do nothing;
create table if not exists public.family_members (
  uid  uuid primary key references auth.users (id) on delete cascade
);

-- is_family(): true for a signed-in family member. Security definer so the policies can read
-- family_members, which nobody else can.
create or replace function public.is_family() returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.family_members where uid = (select auth.uid()));
$$;

-- records_merge(): reproduces the app's newest-wins merge for a row that already exists.
-- Incoming newer or equal: old keys survive unless the new body replaces them. Incoming older:
-- the old body wins and the incoming only adds keys it lacks. A body with "__replace": true
-- (the coach servers and save_program) replaces the whole body so a removed key stays removed.
-- On insert the merge is left to the update that ON CONFLICT runs, but the "__replace" marker
-- is kept until then.
create or replace function public.records_merge() returns trigger
language plpgsql set search_path = ''
as $$
begin
  if tg_op = 'INSERT' then
    if not exists (select 1 from public.records r where r.kind = new.kind and r.key = new.key) then
      new.body := new.body - '__replace';
    end if;
    new.server_at := now();
    return new;
  end if;
  if new.body ? '__replace' then
    new.body := new.body - '__replace';
  elsif new.updated_at >= old.updated_at then
    new.body := old.body || new.body;
  else
    new.body := new.body || old.body;
  end if;
  new.updated_at := greatest(new.updated_at, old.updated_at);
  new.deleted_at := greatest(new.deleted_at, old.deleted_at);
  new.server_at := now();
  return new;
end;
$$;

drop trigger if exists records_merge on public.records;
create trigger records_merge before insert or update on public.records
  for each row execute function public.records_merge();

-- drafts_merge(): an older draft never overwrites a newer one. server_at always moves.
create or replace function public.drafts_merge() returns trigger
language plpgsql set search_path = ''
as $$
begin
  if tg_op = 'UPDATE' and new.updated_at < old.updated_at then
    new.body := old.body;
    new.updated_at := old.updated_at;
    new.deleted_at := old.deleted_at;
    new.device := old.device;
  end if;
  new.server_at := now();
  return new;
end;
$$;

drop trigger if exists drafts_merge on public.drafts;
create trigger drafts_merge before insert or update on public.drafts
  for each row execute function public.drafts_merge();

-- Row level security: on for every table, with the policies written out. Only a signed-in family
-- member reaches records and drafts. heartbeat and family_members have a policy that refuses
-- everyone, so only the functions below (and the secret key, which skips RLS) can use them.
alter table public.records        enable row level security;
alter table public.drafts         enable row level security;
alter table public.heartbeat      enable row level security;
alter table public.family_members enable row level security;

drop policy if exists family_all on public.records;
create policy family_all on public.records
  for all to authenticated using (public.is_family()) with check (public.is_family());

drop policy if exists family_all on public.drafts;
create policy family_all on public.drafts
  for all to authenticated using (public.is_family()) with check (public.is_family());

drop policy if exists no_client_access on public.heartbeat;
create policy no_client_access on public.heartbeat
  for all to anon, authenticated using (false) with check (false);

drop policy if exists no_client_access on public.family_members;
create policy no_client_access on public.family_members
  for all to anon, authenticated using (false) with check (false);

-- Grants: the project does not expose new tables automatically, so every privilege is written out.
-- Signed-in users read, add and edit records and drafts (deletes are a deleted_at stamp, never a
-- DELETE). anon gets nothing on any table. The secret key (service_role) gets everything.
revoke all on public.records, public.drafts, public.heartbeat, public.family_members from anon, authenticated;
grant select, insert, update on public.records, public.drafts to authenticated;
grant all on public.records, public.drafts, public.heartbeat, public.family_members to service_role;
revoke execute on function public.is_family() from public, anon;
grant execute on function public.is_family() to authenticated;

-- save_program(id, body, base_version): replaces a program, but only if the stored version is the
-- one the caller started from. Returns 'conflict' when it is not, else 'ok'. The stored version
-- becomes base_version + 1.
create or replace function public.save_program(id text, body jsonb, base_version int) returns text
language plpgsql security definer set search_path = ''
as $$
declare
  stored jsonb;
begin
  if not public.is_family() then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  select r.body into stored from public.records r
    where r.kind = 'program' and r.key = save_program.id for update;
  if found and coalesce((stored ->> 'version')::int, 0) <> save_program.base_version then
    return 'conflict';
  end if;
  insert into public.records (kind, key, body, updated_at, by)
    values ('program', save_program.id,
            save_program.body || jsonb_build_object('version', save_program.base_version + 1, '__replace', true),
            (extract(epoch from clock_timestamp()) * 1000)::bigint, 'app')
    on conflict (kind, key) do update
      set body = excluded.body, updated_at = excluded.updated_at, by = excluded.by;
  return 'ok';
end;
$$;

revoke execute on function public.save_program(text, jsonb, int) from public, anon;
grant execute on function public.save_program(text, jsonb, int) to authenticated, service_role;

-- tt_keepalive(): the Home Hub calls this once a day with the publishable key. It touches
-- heartbeat so the free project stays active and soft-deletes drafts untouched for 24 hours.
create or replace function public.tt_keepalive() returns void
language sql security definer set search_path = ''
as $$
  update public.heartbeat set touched_at = now() where id = 1;
  update public.drafts set deleted_at = (extract(epoch from now()) * 1000)::bigint
    where deleted_at is null and updated_at < ((extract(epoch from now()) - 86400) * 1000)::bigint;
$$;

revoke execute on function public.tt_keepalive() from public;
grant execute on function public.tt_keepalive() to anon, authenticated, service_role;

-- Realtime: the apps listen for changes to records and drafts.
do $$
declare
  t text;
begin
  foreach t in array array['records', 'drafts'] loop
    if not exists (select 1 from pg_publication_tables
                   where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = t) then
      execute format('alter publication supabase_realtime add table public.%I', t);
    end if;
  end loop;
end;
$$;
