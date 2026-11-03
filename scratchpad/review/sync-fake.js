"use strict";
// A JS stand-in for the Supabase side of the sync engine, for sync-cases.js: an in-memory server holding
// the records and drafts tables, and a client with the small part of the supabase-js v2 interface the
// app uses (from().select/upsert, rpc, auth, channel). The merge rules are a line for line copy of
// records_merge(), drafts_merge() and save_program() in docs/supabase-schema.sql.

// Postgres prints a timestamp without its trailing zeros, so the times here do too.
function stamp(n) {
  const micros = 1000000 + n * 100000 + (n % 7);
  const frac = String(micros % 1000000).padStart(6, "0").replace(/0+$/, "");
  return "2026-11-03T12:00:" + String(Math.floor(micros / 1000000) % 60).padStart(2, "0") + (frac ? "." + frac : "") + "+00:00";
}
const without = (o, k) => { const c = Object.assign({}, o); delete c[k]; return c; };

class FakeServer {
  constructor() {
    this.records = new Map();
    this.drafts = new Map();
    this.tick = 0;
    this.password = "family-pass";
    this.listeners = new Set();
    this.offline = false;
    this.calls = [];
    this.failUpserts = 0;
    this.dropOnUpsert = null;   // (row) => row or null: makes the server lose or change a row it was sent
  }
  now() { return stamp(++this.tick); }
  recordsMerge(old, row, at) {
    const next = Object.assign({}, row, { server_at: at });
    if (!old) next.body = without(row.body, "__replace");
    else {
      if ("__replace" in row.body) next.body = without(row.body, "__replace");
      else if (row.updated_at >= old.updated_at) next.body = Object.assign({}, old.body, row.body);
      else next.body = Object.assign({}, row.body, old.body);
      next.updated_at = Math.max(row.updated_at, old.updated_at);
      next.deleted_at = row.deleted_at == null ? old.deleted_at : old.deleted_at == null ? row.deleted_at : Math.max(row.deleted_at, old.deleted_at);
    }
    return next;
  }
  upsertRecords(rows, from) {
    const at = this.now();
    rows.forEach(r => {
      if (this.dropOnUpsert) { r = this.dropOnUpsert(r); if (!r) return; }
      const k = r.kind + "|" + r.key, old = this.records.get(k);
      const row = Object.assign({ person: null, body: {}, updated_at: 0, deleted_at: null }, r);
      const next = this.recordsMerge(old, row, at);
      this.records.set(k, next);
      this.emit("records", old ? "UPDATE" : "INSERT", next, from);
    });
  }
  upsertDrafts(rows, from) {
    const at = this.now();
    rows.forEach(r => {
      const k = r.person + "|" + r.session_key, old = this.drafts.get(k);
      let next = Object.assign({ deleted_at: null, device: null }, r, { server_at: at });
      if (old && next.updated_at < old.updated_at) next = Object.assign({}, old, { server_at: at });
      this.drafts.set(k, next);
      this.emit("drafts", old ? "UPDATE" : "INSERT", next, from);
    });
  }
  saveProgram(id, body, base) {
    const old = this.records.get("program|" + id);
    if (old && (+old.body.version || 0) !== base) return "conflict";
    const at = this.now(), next = {
      kind: "program", key: id, person: null, body: Object.assign({}, body, { version: base + 1 }), updated_at: Date.now(),
      deleted_at: old ? old.deleted_at : null, by: "app", server_at: at };
    this.records.set("program|" + id, next);
    this.emit("records", old ? "UPDATE" : "INSERT", next, null);
    return "ok";
  }
  emit(table, eventType, row, from) {
    this.listeners.forEach(l => { if (l.table === table) setTimeout(() => l.cb({ eventType, new: JSON.parse(JSON.stringify(row)) }), 0); });
  }
  client(token) { return new FakeClient(this, token || {}); }
  // test helpers: another writer (the coach, the hub) changes a row behind the phones' backs
  put(kind, key, fields) { this.upsertRecords([Object.assign({ kind, key: String(key) }, fields)], null); }
}

class Query {
  constructor(client, table) { this.c = client; this.table = table; this.filters = []; this.orders = []; this.max = Infinity; this.op = "select"; }
  select() { this.op = "select"; return this; }
  upsert(rows, opts) { this.op = "upsert"; this.rows = Array.isArray(rows) ? rows : [rows]; this.opts = opts || {}; return this; }
  order(col, o) { this.orders.push([col, !(o && o.ascending === false)]); return this; }
  gt(col, v) { this.filters.push(["gt", col, v]); return this; }
  gte(col, v) { this.filters.push(["gte", col, v]); return this; }
  eq(col, v) { this.filters.push(["eq", col, v]); return this; }
  limit(n) { this.max = n; return this; }
  then(res, rej) { return Promise.resolve().then(() => this.run()).then(res, rej); }
  run() {
    const s = this.c.server;
    if (s.offline) return { data: null, error: { message: "Failed to fetch" } };
    s.calls.push({ table: this.table, op: this.op, n: this.rows ? this.rows.length : 0, filters: this.filters });
    if (!s.signedIn.has(this.c.token)) return { data: null, error: { message: "permission denied" } };
    if (this.op === "upsert") {
      if (s.failUpserts > 0) { s.failUpserts--; return { data: null, error: { message: "upsert failed" } }; }
      const cols = new Set(this.rows.map(r => Object.keys(r).sort().join()));
      if (cols.size > 1) return { data: null, error: { message: "All object keys must match" } };
      if (this.table === "records") s.upsertRecords(JSON.parse(JSON.stringify(this.rows)), this.c);
      else s.upsertDrafts(JSON.parse(JSON.stringify(this.rows)), this.c);
      return { data: null, error: null };
    }
    let rows = Array.from((this.table === "records" ? s.records : s.drafts).values());
    const norm = v => String(v).replace(/\.(\d+)/, (m, f) => "." + f.padEnd(6, "0"));
    this.filters.forEach(([op, col, v]) => {
      rows = rows.filter(r => {
        const a = col === "server_at" ? norm(r[col]) : r[col], b = col === "server_at" ? norm(v) : v;
        return op === "gt" ? a > b : op === "gte" ? a >= b : a === b;
      });
    });
    const key = (r, col) => col === "server_at" ? norm(r[col]) : r[col];
    rows.sort((x, y) => { for (const [col, asc] of this.orders) { const a = key(x, col), b = key(y, col); if (a !== b) return (a < b ? -1 : 1) * (asc ? 1 : -1); } return 0; });
    return { data: JSON.parse(JSON.stringify(rows.slice(0, this.max))), error: null };
  }
}

class FakeClient {
  constructor(server, token) {
    this.server = server;
    this.token = token;
    server.signedIn = server.signedIn || new Set();
    this.auth = {
      signInWithPassword: async ({ password }) => {
        if (server.offline) return { data: null, error: { message: "Failed to fetch" } };
        if (password !== server.password) return { data: null, error: { message: "Invalid login credentials" } };
        server.signedIn.add(this.token);
        return { data: { session: {} }, error: null };
      },
      signOut: async () => { server.signedIn.delete(this.token); return { error: null }; },
      getSession: async () => ({ data: { session: server.signedIn.has(this.token) ? {} : null }, error: null }),
    };
    this.channels = [];
  }
  from(table) { return new Query(this, table); }
  async rpc(name, args) {
    const s = this.server;
    if (s.offline) return { data: null, error: { message: "Failed to fetch" } };
    s.calls.push({ table: "rpc:" + name, op: "rpc", n: 1, filters: [] });
    if (name === "save_program") return { data: s.saveProgram(args.id, args.body, args.base_version), error: null };
    return { data: null, error: { message: "no such function" } };
  }
  channel() {
    const ch = { handlers: [], on(type, filter, cb) { ch.handlers.push({ table: filter.table, cb }); return ch; },
      subscribe: cb => { ch.handlers.forEach(h => this.server.listeners.add(Object.assign(h, { client: this }))); ch.live = true; if (cb) cb("SUBSCRIBED"); return ch; } };
    this.channels.push(ch);
    return ch;
  }
  removeChannel(ch) { ch.handlers.forEach(h => this.server.listeners.delete(h)); ch.live = false; return Promise.resolve("ok"); }
}

module.exports = { FakeServer, FakeClient, stamp };
