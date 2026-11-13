"use strict";
// Cases for the Supabase sync engine in js/app.js (the Family storage block): the automatic first
// sign-in, a second phone holding the same accounts, edits made offline, pulling only newer rows,
// the draft relay between phones, deleted logs staying deleted, and a mismatch keeping GitHub.
// Run from the command line:
//
//   ELECTRON_RUN_AS_NODE=1 "<VS Code>/Code.exe" scratchpad/review/sync-cases.js
//
// Each "phone" is its own copy of the block and the app's merge code with its own fake localStorage,
// all talking to one JS fake of the Supabase server (sync-fake.js). No page opens, no network is used,
// and no real store is read.
const { grab, grabConst, familyBlock } = require("./sync-harness");
const { FakeServer } = require("./sync-fake");

const FUNCTIONS = ["slugify", "programSlug", "wrapProgram", "paintStatus", "autoSync", "clearCaches", "overwritePerPerson", "loadSync",
  "mergeInData", "mergeLogs", "tombstoneLogs", "tombstoneLog", "deletedLogIds", "upsertById", "mergeRecord", "mergeWeighIns",
  "mergeBodyweight", "bwTombstone", "bwIsDeleted", "tombstoneBodyweight", "mergeMachineSettings", "mergeProgression", "mergeNewestPerKey",
  "mergeAdminPin", "mergeCoachQuestions", "mergeMeasurements", "mergeNewestPerPerson", "mergeSuggestions", "sugRank", "mergeDecisions",
  "saveDrafts", "mergeProgramChanges", "mergeMeals", "mealIsDeleted", "mealTombstone", "tombstoneMeal", "mergeConfig", "mergePrograms",
  "incomingPrograms", "draftOnProgram", "syncWeightFromBw", "latestBw", "b64encode", "b64decode", "openFamilyStorage", "setupOpen", "setupReceive", "setupResume"];
const CONSTS = ["KEY", "SYNC_KEY", "DRAFT_KEY", "DRAFT_TTL_MS", "clone", "esc", "SETUP_PREFIX"];

// The page globals the block touches, as small fakes.
function fakeDom() {
  const els = {};
  const view = { innerHTML: "", insertAdjacentHTML(where, html) { view.innerHTML = html + view.innerHTML; } };
  els.view = view;
  const el = id => els[id] || (els[id] = { id, value: "", hidden: false, textContent: "", innerHTML: "", dataset: {}, open: false, onclick: null });
  return { els, document: { getElementById: el, addEventListener() {}, createElement: () => ({}), head: { appendChild() {} }, visibilityState: "visible" } };
}
// Timers the test steps by hand, so a debounce or a 30 s tick is exact.
function fakeTimers() {
  let now = 0, next = 1;
  const jobs = new Map();
  return {
    setTimeout: (fn, ms) => { jobs.set(next, { at: now + (ms || 0), fn }); return next++; },
    clearTimeout: id => jobs.delete(id),
    setInterval: (fn, ms) => { jobs.set(next, { at: now + ms, fn, every: ms }); return next++; },
    clearInterval: id => jobs.delete(id),
    pending: () => jobs.size,
    // runs everything due within ms, in order; async work started by a job is settled by the caller
    async advance(ms, settle) {
      const end = now + ms;
      for (;;) {
        const due = Array.from(jobs.entries()).filter(([, j]) => j.at <= end).sort((a, b) => a[1].at - b[1].at)[0];
        if (!due) break;
        const [id, job] = due;
        now = Math.max(now, job.at);
        if (job.every) job.at += job.every; else jobs.delete(id);
        job.fn();
        await settle();
      }
      now = end;
    },
  };
}
const settle = async () => { for (let i = 0; i < 6; i++) await new Promise(r => setTimeout(r, 2)); };

function makeState(people, extra) {
  return Object.assign({
    people: people.concat(["", ""]).slice(0, 2), weights: ["", ""], goals: ["", ""], colors: ["navy", "purple"], activePerson: 0,
    coaching: {}, suggestions: [], programChanges: [], limiters: {}, meals: [], nutritionTargets: {}, measurements: [], bodyweights: [],
    hrZones: {}, racePredictions: {}, machineSettings: {}, progression: {}, features: {}, coachQuestions: {}, wellness: {},
    programs: {}, programIds: {}, logs: [], deletedLogs: [], deletedBodyweights: [], deletedMeals: [],
  }, extra || {});
}
const SESSIONS = { a: { name: "Upper", day: "Monday", exercises: [] } };
function programFor(id, members, version, updatedAt) {
  return { id, members, version, updatedAt, updatedBy: members[0], order: ["a"], sessions: JSON.parse(JSON.stringify(SESSIONS)) };
}
function log(id, person, date, extra) { return Object.assign({ id, person, date, updatedAt: id, sessionKey: "a", sessionName: "Upper", entries: [] }, extra); }

// One phone: its own copy of the engine around `state`, talking to `server`.
function makePhone(server, state, opts) {
  opts = opts || {};
  const dom = fakeDom(), listeners = {}, timers = fakeTimers(), store = {}, counts = { saves: 0, renders: 0, toasts: [], dialogs: [], opened: 0, tab: "", replaced: [] };
  const token = opts.token || {}, lib = { createClient: () => server.client(token) };
  const win = { supabase: opts.noLib ? undefined : lib, addEventListener: (t, fn) => (listeners[t] = listeners[t] || []).push(fn) };
  dom.document.addEventListener = win.addEventListener;
  const nav = { onLine: true };
  const names = ["state", "env", "document", "window", "navigator", "localStorage", "setTimeout", "clearTimeout", "setInterval", "clearInterval", "Date", "location", "history"];
  const fns = FUNCTIONS.map(grab).join("\n");
  const block = familyBlock().replace("const SB_PAGE=1000", "const SB_PAGE=" + (opts.page || 1000));
  const body = "let progExIndex={}, bwIndex={}, personIndex={}, progIndex={};\n"
    + "let formDrafts={}, sessionTimers={}, formExtras={}, activeTab='home', curSession='a', restStarts={}, holdStarts={};\n"
    + "const draftKey=()=>state.people[state.activePerson]+'|'+curSession;\n"
    + "function captureDraft(){} function save(){ env.counts.saves++; } function renderPeople(){} function renderEdit(){ env.counts.edits = (env.counts.edits || 0) + 1; } function renderView(){ env.counts.renders++; }\n"
    + "function toast(m){ env.counts.toasts.push(m); } function autoSync(){} const ico=()=>'';\n"
    + "const FAMILY_PROJECT=env.project||{url:'', key:''};\n"
    + "let setupPending=null, adminUnlocked=false; const hasPin=()=>false; function renderAdminGate(){} function setSettingsTab(t){ env.counts.tab=t; } function showUpdateResult(t, b){ env.counts.dialogs.push([t, b]); }\n"
    + CONSTS.map(grabConst).join("\n") + "\n" + fns + "\n" + block
    + "\nfsField('fsPass').value=env.password||'';\n"
    + "return { get sb(){ return sb; }, get sbLines(){ return sbLines; }, get state(){ return state; }, get setupPending(){ return setupPending; }, formDrafts, sessionTimers, formExtras,\n"
    + "  ev: code => eval(code) };";
  const FakeDate = class extends Date { static now() { return env.clock.t; } };
  const env = { counts, password: opts.password, project: opts.project, clock: { t: opts.t || Date.now() }, timers, store };
  const localStorage = { getItem: k => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); }, removeItem: k => { delete store[k]; } };
  const api = new Function(...names, body)(state, env, dom.document, win, nav, localStorage, timers.setTimeout, timers.clearTimeout, timers.setInterval, timers.clearInterval, FakeDate, opts.location || { origin: "https://fam.example", pathname: "/Training-Tracker/", search: "", hash: "" }, { replaceState: (a, b, url) => counts.replaced.push(url) });
  const fire = t => { (listeners[t] || []).forEach(fn => fn()); return settle(); };
  const advance = ms => timers.advance(ms, settle);
  return Object.assign(api, { dom, timers, store, counts, env, nav, win, settle, fire, advance });
}

async function connect(phone, pass) {
  phone.dom.els.fsUrl = { value: "https://x.supabase.co" }; phone.dom.els.fsKey = { value: "pk" }; phone.dom.els.fsEmail = { value: "fam@x.example" };
  phone.dom.els.fsPass.value = pass || "family-pass";
  await phone.ev("sbConnect()"); await phone.settle();
  return phone.sb.mode === "supabase";
}

let failed = 0, passed = 0;
function check(label, ok, detail) {
  if (ok) passed++; else { failed++; console.log("FAIL " + label + (detail !== undefined ? " -> " + JSON.stringify(detail) : "")); }
}
const keys = rows => Array.from(rows.keys()).sort();

async function main() {
  // ---- first sign-in: upload, read back, compare, switch ----
  {
    const server = new FakeServer();
    const state = makeState(["Alex", "Sam"], {
      logs: [log(1793000000001, "Alex", "2026-10-30"), log(1793000000002, "Sam", "2026-10-31")],
      bodyweights: [{ person: "Alex", date: "2026-11-01", kg: 80 }],
      programs: { "p-alex-sam": programFor("p-alex-sam", ["Alex", "Sam"], 3, "2026-11-01T10:00:00.000Z") },
      programIds: { Alex: { id: "p-alex-sam", updatedAt: 0 }, Sam: { id: "p-alex-sam", updatedAt: 0 } },
      deletedLogs: [1793000000009],
    });
    const before = JSON.stringify(state);
    const phone = makePhone(server, state, { password: "family-pass" });
    check("a new phone is on github", phone.sb.mode === "github");
    phone.dom.els.fsUrl = { value: "https://x.supabase.co", id: "fsUrl" }; phone.dom.els.fsKey = { value: "pk", id: "fsKey" }; phone.dom.els.fsEmail = { value: "fam@x.example", id: "fsEmail" };
    await phone.ev("sbConnect()"); await phone.settle();
    check("first sign-in switches to supabase", phone.sb.mode === "supabase", phone.dom.els.fsStatus.textContent);
    check("every row reached the server", keys(server.records).length === 7, keys(server.records));
    check("the deleted log is a deleted row", server.records.get("log|1793000000009").deleted_at > 0);
    check("progress says what happened", phone.sbLines.some(l => /^All 7 records match/.test(l)), phone.sbLines);
    check("local data is untouched", JSON.stringify(phone.state.logs) === JSON.stringify(JSON.parse(before).logs) && phone.state.people.join() === "Alex,Sam");
    check("the password is not kept", !JSON.stringify(phone.store).includes("family-pass") && phone.dom.els.fsPass.value === "");
    check("the cursor is the newest server time", !!phone.sb.cursor);
    check("nothing is waiting to send", phone.ev("sbLocalRows().filter(r => sb.h[rkey(r)] !== rowHash(r)).length") === 0);
  }

  // ---- a second phone holding the same accounts: no duplicates, newest wins ----
  {
    const server = new FakeServer();
    const prog = (v, at) => ({ programs: { "p-alex-sam": programFor("p-alex-sam", ["Alex", "Sam"], v, at) }, programIds: { Alex: { id: "p-alex-sam", updatedAt: 0 }, Sam: { id: "p-alex-sam", updatedAt: 0 } } });
    const one = makePhone(server, makeState(["Alex", "Sam"], Object.assign({
      logs: [log(1793000000001, "Alex", "2026-10-30", { feedback: "old note", updatedAt: 1793000100000 }), log(1793000000002, "Sam", "2026-10-31")],
      bodyweights: [{ person: "Alex", date: "2026-11-01", kg: 80, updatedAt: 1793600000000 }] }, prog(5, "2026-11-01T10:00:00.000Z"))), { password: "family-pass" });
    const two = makePhone(server, makeState(["Alex", "Sam"], Object.assign({
      logs: [log(1793000000001, "Alex", "2026-10-30", { feedback: "newer note", updatedAt: 1793000900000 }), log(1793000000003, "Alex", "2026-11-02")],
      bodyweights: [{ person: "Alex", date: "2026-11-01", kg: 79.5, updatedAt: 1793600000900 }] }, prog(2, "2026-10-20T10:00:00.000Z"))), { password: "family-pass" });
    for (const [phone, n] of [[one, "one"], [two, "two"]]) {
      phone.dom.els.fsUrl = { value: "https://x.supabase.co" }; phone.dom.els.fsKey = { value: "pk" }; phone.dom.els.fsEmail = { value: "fam@x.example" };
      await phone.ev("sbConnect()"); await phone.settle();
      check("phone " + n + " switched", phone.sb.mode === "supabase", phone.dom.els.fsStatus.textContent);
    }
    const logRows = Array.from(server.records.values()).filter(r => r.kind === "log");
    check("no duplicate logs on the server", logRows.length === 3, logRows.map(r => r.key));
    check("the newer note won on the server", server.records.get("log|1793000000001").body.feedback === "newer note");
    check("the newer weigh-in won on the server", server.records.get("bodyweight|Alex:2026-11-01").body.kg === 79.5);
    check("phone two got the other phone's log", two.state.logs.some(l => l.id === 1793000000002) && two.state.logs.length === 3);
    check("phone two took the newer program", two.state.programs["p-alex-sam"].updatedAt === "2026-11-01T10:00:00.000Z");
    check("phone one still has just its own two logs", one.state.logs.length === 2);
  }

  // ---- a mismatch keeps GitHub ----
  {
    const server = new FakeServer(), state = makeState(["Alex"], { logs: [log(1793000000001, "Alex", "2026-10-30"), log(1793000000002, "Alex", "2026-10-31")] });
    server.dropOnUpsert = r => (r.kind === "log" ? null : r);
    const phone = makePhone(server, state, { password: "family-pass" });
    phone.dom.els.fsUrl = { value: "https://x.supabase.co" }; phone.dom.els.fsKey = { value: "pk" }; phone.dom.els.fsEmail = { value: "fam@x.example" };
    await phone.ev("sbConnect()"); await phone.settle();
    check("a mismatch stays on github", phone.sb.mode === "github");
    check("the mismatch is named", phone.sbLines.some(l => /log 1793000000001 is missing/.test(l)) && /Check failed: 2 differ/.test(phone.dom.els.fsStatus.textContent), phone.sbLines);
    check("the mismatch deleted nothing", phone.state.logs.length === 2);
    server.dropOnUpsert = null;
    phone.dom.els.fsPass.value = "family-pass";
    await phone.ev("sbConnect()"); await phone.settle();
    check("connecting again once the server is right switches", phone.sb.mode === "supabase");
    const failing = makePhone(server, makeState(["Alex"], { logs: [log(1793000000005, "Alex", "2026-10-31")] }), { password: "family-pass" });
    failing.dom.els.fsUrl = { value: "https://x.supabase.co" }; failing.dom.els.fsKey = { value: "pk" }; failing.dom.els.fsEmail = { value: "fam@x.example" };
    server.failUpserts = 1;
    await failing.ev("sbConnect()"); await failing.settle();
    check("a failed upload stays on github", failing.sb.mode === "github" && /Upload failed/.test(failing.dom.els.fsStatus.textContent), failing.dom.els.fsStatus.textContent);
    const wrong = makePhone(server, makeState(["Alex"]), { password: "nope" });
    wrong.dom.els.fsUrl = { value: "https://x.supabase.co" }; wrong.dom.els.fsKey = { value: "pk" }; wrong.dom.els.fsEmail = { value: "fam@x.example" };
    await wrong.ev("sbConnect()"); await wrong.settle();
    check("a wrong password stays on github", wrong.sb.mode === "github" && /Sign-in failed/.test(wrong.dom.els.fsStatus.textContent));

    const mkForm = (opts, over) => {
      const p = makePhone(server, makeState(["Alex"]), Object.assign({ password: "family-pass" }, opts));
      Object.assign(p.dom.els, { fsUrl: { value: "https://x.supabase.co" }, fsKey: { value: "pk" }, fsEmail: { value: "fam@x.example" }, fsConnect: { textContent: "Connect", disabled: false } }, over);
      return p;
    };
    const signedBefore = server.signedIn.size, badUrl = mkForm({}, { fsUrl: { value: "https://x.supabase.co/rest/v1" } });
    await badUrl.ev("sbConnect()"); await badUrl.settle();
    const urlMsg = badUrl.dom.els.fsStatus.textContent;
    check("a bad address names the Project URL field and sends nothing", badUrl.sb.mode === "github" && server.signedIn.size === signedBefore && /^Project URL must look like https:\/\/<name>\.supabase\.co/.test(urlMsg), urlMsg);
    check("the same message shows under Connect, marked bad", badUrl.dom.els.fsConnectMsg.textContent === urlMsg && badUrl.dom.els.fsConnectNote.hidden === false && badUrl.dom.els.fsConnectDot.dataset.s === "bad");
    check("the button is usable after a bad address", badUrl.dom.els.fsConnect.disabled !== true);
    for (const [field, value, name] of [["fsKey", "has space", "Publishable key"], ["fsEmail", "not-an-email", "Family email"]]) {
      const p = mkForm({}, { [field]: { value } });
      await p.ev("sbConnect()"); await p.settle();
      check(name + " is named when wrong", p.sb.mode === "github" && p.dom.els.fsStatus.textContent.indexOf(name) === 0, p.dom.els.fsStatus.textContent);
    }
    const noPass = mkForm({ password: "" });
    await noPass.ev("sbConnect()"); await noPass.settle();
    check("Password is named when empty", noPass.sb.mode === "github" && noPass.dom.els.fsStatus.textContent.indexOf("Password") === 0, noPass.dom.els.fsStatus.textContent);

    const noLib = mkForm({ noLib: true });
    const libRun = noLib.ev("sbConnect()");
    await noLib.settle();
    check("while the library loads the button says so", noLib.dom.els.fsConnect.disabled === true && noLib.dom.els.fsConnect.textContent === "Signing in..." && /^Signing in/.test(noLib.dom.els.fsConnectMsg.textContent));
    await noLib.advance(14000);
    check("nothing is reported before the 15 s are up", noLib.dom.els.fsConnect.disabled === true);
    await noLib.advance(2000); await libRun; await noLib.settle();
    check("a library that never loads times out with a clear error", noLib.sb.mode === "github" && noLib.dom.els.fsStatus.textContent === "Could not reach the storage library - check the connection and try again" && noLib.dom.els.fsConnect.disabled === false && noLib.dom.els.fsConnect.textContent === "Connect", noLib.dom.els.fsStatus.textContent);

    const hang = mkForm({});
    server.hangSignIn = true;
    const hangRun = hang.ev("sbConnect()");
    await hang.settle(); await hang.advance(16000); await hangRun; await hang.settle();
    server.hangSignIn = false;
    check("a sign-in that never answers times out with a clear error", hang.sb.mode === "github" && hang.dom.els.fsStatus.textContent === "Could not reach the family storage - check the connection and try again" && hang.dom.els.fsConnect.disabled === false, hang.dom.els.fsStatus.textContent);

    // The service worker must answer a request the network never does, or the storage library script hangs the Connect button.
    {
      let handler, answered; const pending = [];
      const swSource = require("fs").readFileSync(require("path").join(__dirname, "..", "..", "sw.js"), "utf8");
      require("vm").runInNewContext(swSource, {
        self: { addEventListener: (t, fn) => { if (t === "fetch") handler = fn; }, location: { origin: "https://app.example" } },
        caches: { match: async () => undefined, open: async () => ({ put() {} }) },
        fetch: () => new Promise(() => {}), setTimeout: fn => pending.push(fn), clearTimeout() {}, Response: { error: () => "ERROR" }, URL, Promise,
      });
      handler({ request: { method: "GET", url: "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.117.3/dist/umd/supabase.js", mode: "cors" }, respondWith: p => { answered = p; } });
      await settle(); pending.forEach(fn => fn());
      check("a library request the network never answers still settles in the service worker", (await answered) === "ERROR" && pending.length === 1, pending.length);
    }
  }

  // ---- ongoing sync: offline edits queue and flush, pulls fetch only newer rows, realtime ----
  {
    const server = new FakeServer(), mk = (extra) => makePhone(server, makeState(["Alex"], extra), { password: "family-pass" });
    const a = mk({ logs: [log(1793000000001, "Alex", "2026-10-30")] }), b = mk({});
    await connect(a); await connect(b);
    check("both phones are connected", a.sb.mode === "supabase" && b.sb.mode === "supabase");
    // an edit on A reaches the server after the debounce, and B hears it through realtime
    a.state.logs.push(log(1793000000010, "Alex", "2026-11-02"));
    await a.ev("autoSync()");
    await a.advance(1000);
    check("the save is debounced", !server.records.has("log|1793000000010"));
    await a.advance(600);
    check("the debounced save reaches the server", server.records.has("log|1793000000010"));
    await b.advance(300);
    check("the other phone gets it through realtime", b.state.logs.some(l => l.id === 1793000000010), b.state.logs.length);
    const renders = a.counts.renders;
    await a.advance(300);
    check("A's own echo does not redraw the screen", a.counts.renders === renders);
    // offline: edits wait, then go when the phone is back
    a.nav.onLine = false;
    a.state.logs.push(log(1793000000011, "Alex", "2026-11-03"));
    await a.ev("autoSync()"); await a.advance(1600);
    check("offline edits stay on the phone", !server.records.has("log|1793000000011") && /^Offline/.test(a.dom.els.fsStatus.textContent), a.dom.els.fsStatus.textContent);
    a.nav.onLine = true; await a.fire("online");
    check("the queued edit flushes when back online", server.records.has("log|1793000000011") && /^Synced/.test(a.dom.els.fsStatus.textContent), a.dom.els.fsStatus.textContent);
    // a failing server: the edit stays queued, then goes
    server.offline = true;
    a.state.logs.push(log(1793000000012, "Alex", "2026-11-04"));
    await a.ev("autoSync()"); await a.advance(1600);
    check("a failed send says so and keeps the edit", /^Sync failed/.test(a.dom.els.fsStatus.textContent) && !server.records.has("log|1793000000012"));
    server.offline = false;
    await a.advance(30000);
    check("the 30 s tick sends what is waiting", server.records.has("log|1793000000012"), a.dom.els.fsStatus.textContent);
    // pull only newer rows
    server.calls.length = 0;
    server.put("log", 1793000000020, { person: "Alex", body: log(1793000000020, "Alex", "2026-11-05"), updated_at: 1793000000020 });
    await b.fire("visibilitychange");
    const pulls = server.calls.filter(c => c.table === "records" && c.op === "select");
    check("a pull asks only for rows after the cursor", pulls.length > 0 && pulls.every(c => c.filters.some(f => f[1] === "server_at")), pulls.map(c => c.filters));
    check("the newer row arrived", b.state.logs.some(l => l.id === 1793000000020));
    server.calls.length = 0;
    await b.fire("visibilitychange");
    check("with nothing new a pull gets nothing", /0 received/.test(b.dom.els.fsStatus.textContent), b.dom.els.fsStatus.textContent);
    // paging: rows that share a server time are not skipped
    const small = makePhone(server, makeState(["Alex"], {}), { password: "family-pass", page: 3 });
    await connect(small);
    const onServer = Array.from(server.records.values()).filter(r => r.kind === "log").length;
    check("a small page size still reads every row", onServer === 5 && small.state.logs.length === onServer, [onServer, small.state.logs.length]);
  }

  // ---- a deleted log stays deleted ----
  {
    const server = new FakeServer(), L = 1793000000001;
    const mk = (extra) => makePhone(server, makeState(["Alex"], extra), { password: "family-pass" });
    const a = mk({ logs: [log(L, "Alex", "2026-10-30"), log(L + 1, "Alex", "2026-10-31")] }), b = mk({ logs: [log(L, "Alex", "2026-10-30")] });
    await connect(a); await connect(b);
    await a.ev("tombstoneLog(" + L + ")"); await a.ev("autoSync()"); await a.advance(1600);
    check("the delete is a deleted row on the server", server.records.get("log|" + L).deleted_at > 0);
    check("the log's body is kept on the server", server.records.get("log|" + L).body.date === "2026-10-30");
    await b.advance(300);
    check("the other phone drops the log", !b.state.logs.some(l => l.id === L) && b.state.deletedLogs.map(String).indexOf(String(L)) >= 0, b.state.deletedLogs);
    const late = mk({ logs: [log(L, "Alex", "2026-10-30")] });
    await connect(late);
    check("a phone that still held it loses it on first sign-in", !late.state.logs.some(l => l.id === L), late.state.logs.map(l => l.id));
    check("the server row is still deleted", server.records.get("log|" + L).deleted_at > 0);
    await late.advance(1600); await late.advance(30000);
    const t0 = server.records.get("log|" + L).deleted_at;
    await a.advance(30000); await b.advance(30000); await late.advance(30000);
    check("syncing again keeps the same delete time", server.records.get("log|" + L).deleted_at === t0);
  }

  // ---- drafts: relay between phones, the 10 s guard, deletes and the 12 h limit ----
  {
    const server = new FakeServer(), T = 1793700000000;
    const mk = () => makePhone(server, makeState(["Alex", "Sam"]), { password: "family-pass", t: T });
    const a = mk(), b = mk();
    await connect(a); await connect(b);
    const move = async ms => { a.env.clock.t += ms; b.env.clock.t += ms; };
    const form = (reps) => ({ entries: [{ rows: [["60", reps]], done: [false], warm: [false], rpe: null }], difficulty: null, feedback: "" });
    a.formDrafts["Alex|a"] = form("8"); a.formDrafts["Sam|a"] = form("5");
    a.formExtras["Alex|a"] = [{ name: "Curl", sets: 3, cols: ["Weight (kg)", "Reps"] }];
    a.sessionTimers["Alex|a"] = { elapsedSec: 0, running: true, lastStart: T };
    a.ev("saveDrafts()");
    await a.advance(1000);
    check("a draft waits out the 1.5 s debounce", server.drafts.size === 0);
    await a.advance(600);
    check("each person on the phone has their own draft row", server.drafts.size === 2 && server.drafts.has("Alex|a") && server.drafts.has("Sam|a"), Array.from(server.drafts.keys()));
    check("the row carries the extras and the timer", server.drafts.get("Alex|a").body.extras.length === 1 && server.drafts.get("Alex|a").body.timer.running === true);
    await b.advance(10);
    check("the other phone has Alex's draft", b.formDrafts["Alex|a"] && b.formDrafts["Alex|a"].entries[0].rows[0][1] === "8");
    check("and Sam's, kept apart", b.formDrafts["Sam|a"] && b.formDrafts["Sam|a"].entries[0].rows[0][1] === "5");
    check("with the extras and the timer", b.formExtras["Alex|a"].length === 1 && b.sessionTimers["Alex|a"].running);
    check("it did not send the draft back", server.drafts.get("Alex|a").device === a.sb.device);
    // B has the form open and types: a change from A inside 10 s waits behind the chip
    await b.ev("activeTab='log'"); b.ev("sbTyped()");
    await move(2000);
    a.formDrafts["Alex|a"] = form("9"); a.ev("saveDrafts()"); await a.advance(1600); await b.advance(10);
    check("typing inside 10 s keeps the local draft", b.formDrafts["Alex|a"].entries[0].rows[0][1] === "8");
    check("and shows the chip", b.ev("!!sbChips['Alex|a']") && /load\?/.test(b.dom.els.view.innerHTML), b.dom.els.view.innerHTML);
    check("the chip names Alex's form only", !b.ev("sbChips['Sam|a']"));
    b.dom.els.draftChipLoad.onclick();
    check("Load takes the other phone's draft", b.formDrafts["Alex|a"].entries[0].rows[0][1] === "9" && !b.ev("sbChips['Alex|a']"));
    // after 10 s without typing an incoming change applies straight away
    await move(11000);
    a.formDrafts["Alex|a"] = form("10"); a.ev("saveDrafts()"); await a.advance(1600); await b.advance(10);
    check("after 10 s idle the change just applies", b.formDrafts["Alex|a"].entries[0].rows[0][1] === "10" && !b.ev("sbChips['Alex|a']"));
    check("and redraws the open form", b.counts.renders > 0);
    // the newest edit wins: an older draft is ignored
    server.drafts.set("Alex|a", Object.assign({}, server.drafts.get("Alex|a"), { body: { draft: form("1"), extras: [], timer: null }, updated_at: T - 1, device: "d-other" }));
    await b.ev("sbPullDrafts()");
    check("an older draft does not overwrite a newer one", b.formDrafts["Alex|a"].entries[0].rows[0][1] === "10");
    // saving a session deletes the draft everywhere
    delete a.formDrafts["Alex|a"]; delete a.formExtras["Alex|a"]; delete a.sessionTimers["Alex|a"];
    await move(11000); a.ev("saveDrafts()"); await a.advance(1600); await b.advance(10);
    check("saving a session marks its draft deleted", server.drafts.get("Alex|a").deleted_at > 0);
    check("the other phone drops it", !b.formDrafts["Alex|a"] && b.formDrafts["Sam|a"], Object.keys(b.formDrafts));
    // older than 12 hours is ignored
    server.drafts.set("Sam|b", { person: "Sam", session_key: "b", body: { draft: form("3"), extras: [], timer: null }, updated_at: T - 13 * 3600000, deleted_at: null, device: "d-x", server_at: "2026-11-03T12:30:00.5+00:00" });
    await b.ev("sbPullDrafts()");
    check("a draft over 12 hours old is ignored", !b.formDrafts["Sam|b"]);
    // a draft for someone who has no account here is ignored
    server.drafts.set("Mum|a", { person: "Mum", session_key: "a", body: { draft: form("3"), extras: [], timer: null }, updated_at: T + 20000, deleted_at: null, device: "d-x", server_at: "2026-11-03T12:31:00.5+00:00" });
    await b.ev("sbPullDrafts()");
    check("a draft for another phone's person is ignored", !b.formDrafts["Mum|a"]);
    // a draft that was never sent is not deleted on the server when nothing changed
    const draftSends = () => server.calls.filter(x => x.table === "drafts" && x.op === "upsert").length, before = draftSends();
    const c = mk(); await connect(c);
    c.ev("saveDrafts()"); await c.advance(2000);
    check("no draft, nothing sent", draftSends() === before, [before, draftSends()]);
  }

  // ---- program saves go through save_program with a base version ----
  {
    const server = new FakeServer(), P = "p-x", rpcs = () => server.calls.filter(c => c.table === "rpc:save_program").length;
    const mk = () => makePhone(server, makeState(["Alex"], { programs: { [P]: programFor(P, ["Alex"], 3, "2026-11-01T10:00:00.000Z") }, programIds: { Alex: { id: P, updatedAt: 0 } } }), { password: "family-pass" });
    const a = mk(), b = mk();
    await connect(a); await connect(b);
    check("the stored version is known after sign-in", a.sb.pv[P] === 3 && b.sb.pv[P] === 3, [a.sb.pv, b.sb.pv]);
    const edit = (phone, name, version, at) => { const pr = phone.state.programs[P]; pr.sessions.a.name = name; pr.version = version; pr.updatedAt = at; };
    edit(a, "Upper A1", 4, "2026-11-02T10:00:00.000Z"); await a.ev("autoSync()"); await a.advance(1600);
    check("a member's save goes through the RPC", rpcs() === 1 && server.records.get("program|" + P).body.sessions.a.name === "Upper A1");
    check("the stored version counts up from the base", server.records.get("program|" + P).body.version === 4 && a.sb.pv[P] === 4 && a.state.programs[P].version === 4);
    await b.advance(300);
    check("the other phone adopts it", b.state.programs[P].sessions.a.name === "Upper A1" && b.sb.pv[P] === 4);
    check("nothing is sent twice", rpcs() === 1 && a.ev("sbOutbox().programs.length") === 0);
    // two edits from the same version: the second is a conflict and is not overwritten
    b.nav.onLine = false;
    edit(b, "Upper B1", 5, "2026-11-02T12:00:00.000Z"); await b.ev("autoSync()"); await b.advance(1600);
    edit(a, "Upper A2", 5, "2026-11-02T11:00:00.000Z"); await a.ev("autoSync()"); await a.advance(1600);
    check("A's second save went through", server.records.get("program|" + P).body.version === 5 && server.records.get("program|" + P).body.sessions.a.name === "Upper A2");
    b.nav.onLine = true; await b.fire("online");
    check("B's save is refused as a conflict", server.records.get("program|" + P).body.sessions.a.name === "Upper A2" && !!b.ev("sbClashes[" + JSON.stringify(P) + "]"));
    check("B keeps its own edit and the warning is shown", b.state.programs[P].sessions.a.name === "Upper B1" && (b.counts.edits || 0) === 0 && b.counts.toasts.some(t => /changed a program on another phone/.test(t)), b.counts.toasts);
    const n = rpcs();
    await b.advance(30000);
    check("a program in conflict is not retried behind the person's back", rpcs() === n);
    check("the stored version moved to the other phone's", b.sb.pv[P] === 5);
    b.ev("sbClashKeep(" + JSON.stringify(P) + ")"); await b.settle(); await b.advance(1600);
    check("Keep mine saves on top of the newer version", server.records.get("program|" + P).body.sessions.a.name === "Upper B1" && server.records.get("program|" + P).body.version === 6);
    // Reload takes the other phone's copy and drops the unsent edit
    await a.advance(300);
    edit(a, "Upper A3", 7, "2026-11-02T14:00:00.000Z");
    b.nav.onLine = false;
    edit(b, "Upper B2", 7, "2026-11-02T15:00:00.000Z"); await b.ev("autoSync()"); await b.advance(1600);
    await a.ev("autoSync()"); await a.advance(1600);
    b.nav.onLine = true; await b.fire("online");
    check("a second conflict is found", !!b.ev("sbClashes[" + JSON.stringify(P) + "]"));
    b.ev("sbClashReload(" + JSON.stringify(P) + ")"); await b.advance(30000);
    check("Reload takes the other phone's program and nothing more is sent", b.state.programs[P].sessions.a.name === "Upper A3" && !b.ev("sbClashes[" + JSON.stringify(P) + "]") && b.ev("sbOutbox().programs.length") === 0, b.state.programs[P].sessions.a.name);
  }

  // ---- a newer program held back by an open workout is not lost, and is never written over ----
  {
    const P = "p-held", NEW = "2026-11-02T16:06:56.407Z", OLD = "2026-11-02T12:53:39.716Z", T = 1793700000000;
    const prog = (sets, version, updatedAt) => Object.assign(programFor(P, ["Daniel", "Cerys"], version, updatedAt), {
      sessions: { a: { name: "Upper", day: "Monday", exercises: [{ name: "Row", sets, cols: ["Weight (kg)", "Reps"] }] }, b: { name: "Lower", day: "Tuesday", exercises: [] } } });
    const sets = body => body.sessions.a.exercises[0].sets;
    const stale = (server, version) => makePhone(server, makeState(["Daniel", "Cerys"], { programs: { [P]: prog(2, version, OLD) },
      programIds: { Daniel: { id: P, updatedAt: 0 }, Cerys: { id: P, updatedAt: 0 } } }), { password: "family-pass", t: T });
    const newer = (server, version) => server.put("program", P, { body: Object.assign(prog(3, version, NEW), { __replace: true }), updated_at: Date.parse(NEW) });
    const stored = server => server.records.get("program|" + P).body;
    const form = { entries: [{ rows: [["40", "8"]], done: [false], warm: [false], rpe: null }], difficulty: null, feedback: "" };
    const edit = phone => { const pr = phone.state.programs[P]; pr.sessions.b.name = "Lower 2"; pr.version = (+pr.version || 0) + 1; pr.updatedAt = new Date(phone.env.clock.t).toISOString(); };
    const clash = phone => !!phone.ev("sbClashes[" + JSON.stringify(P) + "]");

    for (const edited of [false, true]) {
      const server = new FakeServer(); newer(server, 12);
      const phone = stale(server, 9);
      phone.formDrafts["Cerys|a"] = form;
      await connect(phone);
      const tag = " (first sign-in, draft open" + (edited ? ", member edit" : "") + ")";
      check("the held program is not adopted while the draft is open" + tag, sets(phone.state.programs[P]) === 2 && sets(stored(server)) === 3);
      check("its server version is not recorded as seen" + tag, phone.sb.pv[P] === undefined && !!phone.sb.held[P], [phone.sb.pv[P], phone.sb.held]);
      delete phone.formDrafts["Cerys|a"];
      if (edited) {
        edit(phone); await phone.ev("sbSyncNow(true)"); await phone.settle();
        check("an edit before adoption is a conflict and the server keeps the newer program" + tag, sets(stored(server)) === 3 && stored(server).version === 12 && clash(phone), stored(server));
      } else {
        await phone.ev("sbSyncNow(true)"); await phone.settle();
        check("the next sync adopts it" + tag, sets(phone.state.programs[P]) === 3 && phone.sb.pv[P] === 12 && !phone.sb.held[P], [phone.state.programs[P].version, phone.sb.pv[P], phone.sb.held]);
        edit(phone); await phone.ev("sbSyncNow(true)"); await phone.settle();
        check("an edit after adoption goes through" + tag, stored(server).sessions.b.name === "Lower 2" && stored(server).version === 13 && !clash(phone));
      }
    }

    for (const edited of [false, true]) {
      const server = new FakeServer(), phone = stale(server, 9);
      await connect(phone);
      phone.formDrafts["Cerys|a"] = form;
      newer(server, phone.sb.pv[P] + 1);
      await phone.advance(300); await phone.advance(30000);
      const tag = " (connected phone, draft open" + (edited ? ", member edit" : "") + ")";
      check("a row that arrives under an open draft is held and its version not recorded" + tag, sets(phone.state.programs[P]) === 2 && phone.sb.pv[P] === 9 && !!phone.sb.held[P], [phone.sb.pv[P], phone.sb.held]);
      delete phone.formDrafts["Cerys|a"];
      if (edited) {
        edit(phone); await phone.ev("sbSyncNow(true)"); await phone.settle();
        check("an edit before adoption is a conflict and the server keeps the newer program" + tag, sets(stored(server)) === 3 && clash(phone), stored(server));
      } else {
        await phone.advance(30000);
        check("the next pull adopts it" + tag, sets(phone.state.programs[P]) === 3 && phone.sb.pv[P] === 10 && !phone.sb.held[P], [phone.state.programs[P].version, phone.sb.pv[P], phone.sb.held]);
      }
    }

    for (const edited of [false, true]) {
      const server = new FakeServer(), phone = stale(server, 6);
      await connect(phone);
      newer(server, 8); await phone.ev("sbSyncNow(true)"); await phone.settle();
      phone.state.programs[P] = prog(2, 6, OLD); phone.sb.pv[P] = 8; phone.sb.held = {}; phone.sb.fixed = 0;
      phone.sb.h["program|" + P] = phone.ev("rowHash(sbLocalRows().find(r => r.kind === 'program'))");
      const tag = " (phone upgraded from 2.0.4" + (edited ? ", edit before the first sync" : "") + ")";
      if (edited) { edit(phone); await phone.ev("sbSyncNow(true)"); await phone.settle();
        check("the edit is a conflict and the server keeps the newer program" + tag, sets(stored(server)) === 3 && stored(server).version === 8 && clash(phone), stored(server)); }
      else {
        await phone.ev("sbSyncNow(true)"); await phone.settle();
        check("the first sync adopts the server program" + tag, sets(phone.state.programs[P]) === 3 && phone.sb.pv[P] === 8 && !phone.sb.held[P], [phone.state.programs[P].version, phone.sb.pv[P], phone.sb.held]);
        edit(phone); await phone.ev("sbSyncNow(true)"); await phone.settle();
        check("a following edit builds on it" + tag, sets(stored(server)) === 3 && stored(server).sessions.b.name === "Lower 2" && stored(server).version === 9 && !clash(phone), stored(server));
      }
    }

    {
      const server = new FakeServer(), phone = stale(server, 9);
      await connect(phone);
      const draftRow = (extra) => Object.assign({ person: "Daniel", session_key: "a", body: { draft: form, extras: [], timer: null }, updated_at: T + 1000, deleted_at: null, device: "d-other", server_at: "2026-11-03T12:30:00.5+00:00" }, extra);
      server.drafts.set("Daniel|a", draftRow());
      await phone.advance(30000);
      newer(server, 10);
      await phone.advance(30000);
      check("a draft relayed from the other phone holds the program back (relayed draft)", !!phone.formDrafts["Daniel|a"] && sets(phone.state.programs[P]) === 2 && !!phone.sb.held[P], phone.sb.held);
      server.drafts.set("Daniel|a", draftRow({ updated_at: T + 2000, deleted_at: T + 2000, server_at: "2026-11-03T12:31:00.5+00:00" }));
      await phone.advance(30000);
      await phone.advance(30000);
      check("it is adopted after that draft is deleted (relayed draft)", !phone.formDrafts["Daniel|a"] && sets(phone.state.programs[P]) === 3 && phone.sb.pv[P] === 10 && !phone.sb.held[P], [!!phone.formDrafts["Daniel|a"], phone.sb.pv[P], phone.sb.held]);
    }
  }

  // ---- the running version is the newest cache, with three-part versions in order ----
  {
    const body = [grab("shellVersionKey"), grab("compareShellKeys"),
      "return { newest: names => names.filter(k => shellVersionKey(k)).sort((a, b) => compareShellKeys(shellVersionKey(a), shellVersionKey(b))).pop() };"].join("\n");
    const { newest } = new Function(body)();
    check("2.0.0 is newer than 1.3", newest(["tt-1.3", "tt-2.0.0"]) === "tt-2.0.0" && newest(["tt-2.0.0", "tt-1.3"]) === "tt-2.0.0");
    check("2.0.1 is newer than 2.0.0 and 2.1.0 than 2.0.9", newest(["tt-2.0.0", "tt-2.0.1"]) === "tt-2.0.1" && newest(["tt-2.0.9", "tt-2.1.0"]) === "tt-2.1.0");
    check("1.10.0 is newer than 1.9.0", newest(["tt-1.9.0", "tt-1.10.0"]) === "tt-1.10.0");
    check("sw.js has a three-part version", /const VERSION = "\d+\.\d+\.\d+";/.test(require("fs").readFileSync(require("path").join(__dirname, "..", "..", "sw.js"), "utf8")));
  }
  console.log((failed ? "FAILED " : "ok ") + passed + " passed, " + failed + " failed");
  process.exit(failed ? 1 : 0);
}
if (require.main === module) main().catch(e => { console.log("CRASH", e && e.stack || e); process.exit(1); });
module.exports = { makePhone, makeState, connect, log, programFor };
