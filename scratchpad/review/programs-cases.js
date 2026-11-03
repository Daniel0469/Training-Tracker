"use strict";
// Cases for per-person programs: the load migration, importing an old-shape export, merging
// programs, progOf per person, and accepting a change with and without a clash, and a copied
// session. Run from the command line:
//
//   ELECTRON_RUN_AS_NODE=1 "<VS Code>/Code.exe" scratchpad/review/programs-cases.js
//
// It reads the source text of js/app.js, cuts out the functions it needs and runs them on small
// fixture stores, so it opens no page and reads and writes no real store.
const fs = require("fs");
const path = require("path");
const src = fs.readFileSync(path.join(__dirname, "..", "..", "js", "app.js"), "utf8");

// A whole `function name(...) {...}` out of the source, by brace matching.
function grab(name) {
  const at = src.indexOf("function " + name + "(");
  if (at < 0) throw new Error("function " + name + " not found in js/app.js");
  let depth = 0;
  for (let i = src.indexOf("{", at); i < src.length; i++) {
    if (src[i] === "{") depth++;
    else if (src[i] === "}" && --depth === 0) return src.slice(at, i + 1);
  }
  throw new Error("unbalanced braces in " + name);
}
// A one-line `const name = ...;` out of the source.
function grabConst(name) {
  const m = new RegExp("^const " + name + "\\s*=.*;\\s*$", "m").exec(src);
  if (!m) throw new Error("const " + name + " not found in js/app.js");
  return m[0].trim();
}

const FUNCTIONS = ["slugify", "programSlug", "wrapProgram", "migratePrograms", "uniqueProgramId", "progOf", "claimProgram",
  "incomingPrograms", "draftOnProgram", "mergePrograms", "saveProgram", "diffPrograms", "applyEdit", "renameInPrograms"];
const CONSTS = ["clone", "sameJson", "NO_PROGRAM"];

function makeApi(state, env) {
  const body = "const formDrafts=env.formDrafts||{};\nfunction captureDraft(){}\nfunction save(){ env.saved=(env.saved||0)+1; }\nfunction autoSync(){}\n"
    + CONSTS.map(grabConst).join("\n") + "\n" + FUNCTIONS.map(grab).join("\n")
    + "\nreturn { " + FUNCTIONS.concat(CONSTS).join(", ") + " };";
  return new Function("state", "env", body)(state, env || {});
}

const ex = (name, sets) => ({ name, warmup: "", target: sets + "x8", sets, cols: ["Weight (kg)", "Reps"] });
const sess = (name, day, exercises, extra) => Object.assign({ name, day, exercises }, extra || {});
const oldProgram = () => ({
  order: ["a", "b"], updatedAt: "2026-11-01T10:00:00.000Z",
  sessions: { a: sess("Upper A", "Tuesday", [ex("Bench press", 3), ex("Row", 3)]), b: sess("Lower", "Thursday", [ex("Squat", 3)]) }
});
const baseState = () => ({
  people: ["Daniel", "Cerys", ""], activePerson: 0, programs: {}, programIds: {}, programChanges: [],
  program: oldProgram()
});

let failed = 0, passed = 0;
function check(label, ok, detail) {
  if (ok) passed++; else { failed++; console.log("FAIL " + label + (detail !== undefined ? " -> " + JSON.stringify(detail) : "")); }
}
const json = JSON.stringify;

// ---- load migration ----
{
  const s = baseState();
  const api = makeApi(s);
  api.migratePrograms(s);
  const ids = Object.keys(s.programs);
  check("migration wraps the program once", ids.length === 1 && ids[0] === "p-daniel-cerys", ids);
  const p = s.programs[ids[0]];
  check("members are the named people", json(p.members) === json(["Daniel", "Cerys"]), p.members);
  check("sessions and stamp carried over", p.order.length === 2 && p.updatedAt === "2026-11-01T10:00:00.000Z" && p.version === 1, p);
  check("each person gets the programId", s.programIds.Daniel.id === p.id && s.programIds.Cerys.id === p.id, s.programIds);
  check("old key removed", !("program" in s));
  const before = json(s);
  api.migratePrograms(s);
  check("migration is idempotent", json(s) === before);
  const s2 = JSON.parse(before);
  makeApi(s2).migratePrograms(s2);
  check("migrating a saved copy changes nothing", json(s2) === before);
}

// ---- progOf per person ----
{
  const s = baseState();
  const api = makeApi(s);
  api.migratePrograms(s);
  s.people[2] = "Mum";
  const mum = api.progOf("Mum");
  check("a new person gets her own program", mum.id !== "p-daniel-cerys" && json(mum.members) === json(["Mum"]), mum);
  check("her programId is stored", s.programIds.Mum.id === mum.id);
  mum.sessions.x = sess("Walk", "Friday", []); mum.order.push("x");
  check("Daniel and Cerys share one program", api.progOf("Daniel") === api.progOf("Cerys"));
  check("Mum's sessions are not Daniel's", !api.progOf("Daniel").sessions.x && !!api.progOf("Mum").sessions.x);
  s.activePerson = 2;
  check("no argument reads the active person's", api.progOf() === mum);
  check("a name with no account reads nothing", api.progOf("Stranger") === api.NO_PROGRAM && Object.keys(s.programs).length === 2);
  const fresh = { people: ["Alex", "", ""], activePerson: 0, programs: {}, programIds: {} };
  const fapi = makeApi(fresh);
  const blank = fapi.progOf("");
  check("a blank install reads an empty program", blank.order.length === 0 && Object.keys(fresh.programs).length === 1);
  check("the first account claims it", fapi.progOf("Alex") === blank && blank.members[0] === "Alex");
  api.renameInPrograms("Mum", "Mother");
  check("a renamed person keeps her program", s.programs[mum.id].members[0] === "Mother" && s.programIds.Mother.id === mum.id && !s.programIds.Mum);
}

// ---- importing an old-shape export, and merging ----
{
  const s = baseState();
  const api = makeApi(s);
  api.migratePrograms(s);
  const mine = s.programs["p-daniel-cerys"];
  const old = { people: ["Daniel", "Cerys"], program: oldProgram() };
  let tally = { added: 0, updated: 0 };
  api.mergePrograms(old, false, true, tally);
  check("the same old export changes nothing", tally.updated === 0 && mine.sessions.a.exercises.length === 2, tally);

  old.program.updatedAt = "2026-11-02T10:00:00.000Z";
  old.program.sessions.a.exercises.push(ex("Fly", 2));
  tally = { added: 0, updated: 0 };
  api.mergePrograms(old, false, true, tally);
  const wrapped = s.programs["p-daniel-cerys"];
  check("a newer old-shape program wins, wrapped", tally.updated === 1 && wrapped.sessions.a.exercises.length === 3 && Array.isArray(wrapped.members), tally);

  old.program.updatedAt = "2026-10-01T00:00:00.000Z";
  old.program.sessions.a.exercises.pop();
  tally = { added: 0, updated: 0 };
  api.mergePrograms(old, false, true, tally);
  check("an older one never replaces it", tally.updated === 0 && s.programs["p-daniel-cerys"].sessions.a.exercises.length === 3);

  const noSync = { people: ["Daniel", "Cerys"], program: oldProgram() };
  noSync.program.updatedAt = "2027-01-01T00:00:00.000Z";
  tally = { added: 0, updated: 0 };
  api.mergePrograms(noSync, false, false, tally);
  check("a manual import does not adopt unless asked", tally.updated === 0 && s.programs["p-daniel-cerys"].updatedAt !== "2027-01-01T00:00:00.000Z");
  api.mergePrograms(noSync, true, false, tally);
  check("adopt replaces it", s.programs["p-daniel-cerys"].updatedAt === "2027-01-01T00:00:00.000Z");
}
{
  const s = baseState();
  const api = makeApi(s);
  api.migratePrograms(s);
  const a = s.programs["p-daniel-cerys"];
  a.updatedAt = "2026-11-02T08:00:00.000Z"; a.version = 4;
  const mumProg = { id: "p-mum", members: ["Mum"], version: 2, updatedAt: "2026-11-01T00:00:00.000Z", order: ["w"], sessions: { w: sess("Walk", "Friday", []) } };
  const sharedNewer = Object.assign(JSON.parse(json(a)), { version: 5, updatedAt: "2026-11-03T08:00:00.000Z", order: ["a"], sessions: { a: a.sessions.a } });
  const incoming = { programs: { "p-daniel-cerys": sharedNewer, "p-mum": mumProg }, programIds: { Mum: { id: "p-mum", updatedAt: 5 } } };
  const tally = { added: 0, updated: 0 };
  api.mergePrograms(incoming, false, true, tally);
  check("newest wins for the program both hold", s.programs["p-daniel-cerys"].version === 5 && s.programs["p-daniel-cerys"].order.length === 1);
  check("a program nobody here holds is added", !!s.programs["p-mum"] && s.programIds.Mum && s.programIds.Mum.id === "p-mum");
  const older = Object.assign(JSON.parse(json(mumProg)), { version: 1, updatedAt: "2026-10-01T00:00:00.000Z", order: [], sessions: {} });
  api.mergePrograms({ programs: { "p-mum": older } }, false, true, { added: 0, updated: 0 });
  check("an older copy of one program leaves it alone", s.programs["p-mum"].order.length === 1);
}
{
  const s = baseState();
  const env = { formDrafts: { "Cerys|a": { entries: [{}] } } };
  const api = makeApi(s, env);
  api.migratePrograms(s);
  const incoming = { programs: { "p-daniel-cerys": Object.assign(JSON.parse(json(s.programs["p-daniel-cerys"])), { updatedAt: "2027-01-01T00:00:00.000Z", order: [] }) } };
  api.mergePrograms(incoming, false, true, { added: 0, updated: 0 });
  check("a program is held back while someone on it has a draft open", s.programs["p-daniel-cerys"].order.length === 2);
  delete env.formDrafts["Cerys|a"];
  api.mergePrograms(incoming, false, true, { added: 0, updated: 0 });
  check("and adopted once the draft is saved", s.programs["p-daniel-cerys"].order.length === 0);
}

// ---- program ids never collide ----
{
  const s = { people: ["Mum", "Mum2"], activePerson: 0, programs: { "p-mum": { id: "p-mum", members: ["Someone"], order: [], sessions: {}, version: 1 } }, programIds: {} };
  const api = makeApi(s);
  const p = api.progOf("Mum");
  check("a new program takes a free id", p.id !== "p-mum" && !!s.programs[p.id] && Object.keys(s.programs).length === 2, p.id);
}

// ---- accepting a change ----
function mumStore() {
  const s = { people: ["Daniel", "Mum"], activePerson: 1, programs: {}, programIds: {}, programChanges: [] };
  s.programs["p-mum"] = {
    id: "p-mum", members: ["Mum"], version: 3, updatedAt: "2026-11-01T00:00:00.000Z", order: ["full", "walk"],
    sessions: { full: sess("Full body", "Tuesday", [ex("Leg press", 2), ex("Row", 2)]), walk: sess("Walk", "Friday", [ex("Walk", 1)]) }
  };
  s.programIds.Mum = { id: "p-mum", updatedAt: 0 };
  return s;
}
function proposal(s, mutate) {
  const api = makeApi(s), live = s.programs["p-mum"], work = JSON.parse(json(live));
  mutate(work);
  const d = api.diffPrograms(live, work);
  return { api, c: { id: "c1", kind: "person", programId: "p-mum", from: "Daniel", baseVersion: live.version, base: d.base, proposed: d.proposed, status: "pending" } };
}
{
  const s = mumStore();
  const { api, c } = proposal(s, w => { w.sessions.full.exercises[0].sets = 3; w.sessions.stretch = sess("Stretch", "Sunday", []); w.order.push("stretch"); });
  check("the record holds only the sessions that changed", json(Object.keys(c.proposed.sessions).sort()) === json(["full", "stretch"]) && !("walk" in c.proposed.sessions), c.proposed);
  const res = api.applyEdit(s.programs["p-mum"], c);
  const live = s.programs["p-mum"];
  check("accept with the version unmoved applies everything", res.clashes.length === 0 && live.sessions.full.exercises[0].sets === 3 && !!live.sessions.stretch && live.order.join() === "full,walk,stretch", res);
}
{
  const s = mumStore();
  const { api, c } = proposal(s, w => { w.sessions.full.exercises[0].sets = 3; w.sessions.walk.exercises[0].sets = 2; w.order = ["walk", "full"]; });
  const live = s.programs["p-mum"];
  live.version = 4;
  live.sessions.full.exercises[1].sets = 5;
  live.order = ["walk", "full"];
  const res = api.applyEdit(live, c);
  check("a session changed since is a clash and is left alone", json(res.clashes) === json(["full"]) && live.sessions.full.exercises[0].sets === 2 && live.sessions.full.exercises[1].sets === 5, res);
  check("a session unchanged since still applies", json(res.applied) === json(["walk"]) && live.sessions.walk.exercises[0].sets === 2, res);
  check("the order is not forced over a changed one", res.orderApplied === false);
}
{
  const s = mumStore();
  const { api, c } = proposal(s, w => { delete w.sessions.walk; w.order = ["full"]; });
  const live = s.programs["p-mum"], res = api.applyEdit(live, c);
  check("a removed session is removed", !live.sessions.walk && live.order.join() === "full" && res.clashes.length === 0, live);
}
{
  const s = mumStore();
  const { api, c } = proposal(s, w => { w.sessions.extra = sess("Extra", "Monday", []); w.order.push("extra"); });
  s.programs["p-mum"].sessions.extra = sess("Theirs", "Monday", []);
  s.programs["p-mum"].order.push("extra");
  const res = api.applyEdit(s.programs["p-mum"], c);
  check("a new session whose key is taken is a clash", json(res.clashes) === json(["extra"]) && s.programs["p-mum"].sessions.extra.name === "Theirs", res);
}

// ---- copy session ----
{
  const s = mumStore();
  const api = makeApi(s);
  s.programs["p-mum"].sessions["full-body"] = sess("Full body", "Monday", []);
  s.programs["p-mum"].order.push("full-body");
  const copy = { id: "c2", kind: "copy", programId: "p-mum", from: "Daniel", baseVersion: 3, base: { sessions: {} },
    proposed: { sessions: { upper1: sess("Full body", "Tuesday", [ex("Bench", 3)], { person: "Daniel", cardio: true }) } }, status: "pending" };
  const res = api.applyEdit(s.programs["p-mum"], copy);
  const live = s.programs["p-mum"], key = res.applied[0];
  check("a copy lands under a key nobody has", res.applied.length === 1 && key === "full-body-2" && live.sessions[key].exercises.length === 1 && live.order.indexOf(key) >= 0, res);
  check("a copy is offered to the new owner, not the old", !("person" in live.sessions[key]) && live.sessions[key].cardio === true);
  const again = api.applyEdit(live, copy);
  check("accepting twice would not overwrite", again.applied[0] === "full-body-3" && live.sessions[key].exercises.length === 1);
}

// ---- saveProgram stamps the version ----
{
  const s = mumStore();
  const api = makeApi(s);
  const live = s.programs["p-mum"];
  api.saveProgram(live);
  check("saving bumps the version and stamps the editor", live.version === 4 && live.updatedBy === "Mum" && live.updatedAt > "2026-11-02");
}

console.log(failed ? failed + " failed, " + passed + " passed" : "all " + passed + " passed");
process.exit(failed ? 1 : 0);
