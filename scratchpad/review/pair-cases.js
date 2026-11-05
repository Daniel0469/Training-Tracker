"use strict";
// Cases for the typed pairing code (version 2.0.3) and the project defaults file: the alphabet and how a code is
// made and read, the encryption round trip, the sending phone storing only encrypted values and showing a countdown,
// the new phone claiming the row once, a wrong, expired or rate-limited code, a storage that has not run the schema
// again, and the password never being kept. Run from the command line:
//
//   ELECTRON_RUN_AS_NODE=1 "<VS Code>/Code.exe" scratchpad/review/pair-cases.js
//
// Phones are the ones sync-cases.js builds, talking to the JS fake of Supabase. The pairing code runs the real
// WebCrypto here. No page opens, no network is used, and no real store is read.
const fs = require("fs");
const path = require("path");
const nodeCrypto = require("crypto");
const { src } = require("./sync-harness");
const { FakeServer } = require("./sync-fake");
const { makePhone, makeState, connect } = require("./sync-cases");

let failed = 0, passed = 0;
function check(label, ok, detail) {
  if (ok) passed++; else { failed++; console.log("FAIL " + label + (detail !== undefined ? " -> " + JSON.stringify(detail) : "")); }
}
const root = file => fs.readFileSync(path.join(__dirname, "..", "..", file), "utf8");
const PASS = "family-pass", FAMILY = { url: "https://x.supabase.co", key: "pk", email: "fam@x.example" };
const stored = phone => JSON.stringify(phone.store);

// The elements the sending phone's dialog uses, as small fakes.
function sendDom(phone) {
  const els = phone.dom.els;
  const ctx = { fillStyle: "", fillRect() {} };
  Object.assign(els, {
    setupQr: { width: 0, height: 0, getContext: () => ctx },
    setupDlg: { open: false, showModal() { this.open = true; }, close() { this.open = false; } },
    settingsBtn: { onclick() { phone.counts.opened++; } },
    setupPass: { value: "", focus() {} }, setupShow: { hidden: true }, setupAsk: { hidden: false },
    setupQrPart: { hidden: false }, setupPairPart: { hidden: true },
    setupMsg: { hidden: true, textContent: "", className: "" }, setupText: { value: "" }, setupCount: { textContent: "" },
    pairCode: { textContent: "" }, pairCount: { textContent: "" }, pairMsg: { hidden: true, textContent: "", className: "" },
  });
  function QRCode() { this._oDrawing = { draw() {} }; }
  QRCode.CorrectLevel = { M: 0 };
  QRCode.prototype.makeCode = function () { this._oDrawing.draw({ getModuleCount: () => 21, isDark: () => true }); };
  phone.win.QRCode = QRCode;
}
// A phone that has never connected: the project fields filled, nothing else.
function newPhone(server, clock, opts) {
  const phone = makePhone(server, makeState(["Alex"]), Object.assign({ t: clock.t }, opts));
  phone.env.clock = clock;
  Object.assign(phone.dom.els, { fsUrl: { value: FAMILY.url }, fsKey: { value: FAMILY.key }, fsEmail: { value: "" }, fsPair: { value: "x" }, fsPairUse: { disabled: false } });
  return phone;
}
// A connected phone that has shown its codes: returns the phone and the short code as the person sees it.
async function sender(server, clock) {
  const phone = makePhone(server, makeState(["Alex"]), { password: PASS, t: clock.t });
  phone.env.clock = clock;
  sendDom(phone);
  check("the sending phone is connected", await connect(phone, PASS));
  phone.ev("setupAsk()");
  phone.dom.els.setupPass.value = PASS;
  await phone.ev("setupGo()"); await phone.settle();
  return { phone, shown: phone.dom.els.pairCode.textContent };
}
const claim = async (phone, text) => { await phone.ev("pairUse(" + JSON.stringify(text) + ")"); await phone.settle(); return phone.dom.els.fsConnectMsg.textContent; };
const sha = text => nodeCrypto.createHash("sha256").update(text).digest("hex");

async function main() {
  // ---- the alphabet and making a code ----
  {
    const server = new FakeServer(), phone = makePhone(server, makeState(["Alex"]));
    const alphabet = phone.ev("PAIR_ALPHABET");
    check("the alphabet has no lookalikes: no 0, O, 1, I or L", !/[01OIL]/.test(alphabet), alphabet);
    check("the alphabet is the digits 2 to 9 and capital letters, each once", alphabet.length === 31 && new Set(alphabet).size === 31 && /^[2-9A-Z]+$/.test(alphabet));
    const codes = Array.from({ length: 3000 }, () => phone.ev("pairNew()"));
    check("every code is 6 characters from the alphabet", codes.every(c => c.length === 6 && [...c].every(ch => alphabet.includes(ch))));
    check("codes are not repeated", new Set(codes).size > 2990);
    const seen = new Set(codes.join(""));
    check("every character of the alphabet turns up", seen.size === 31, [...alphabet].filter(c => !seen.has(c)));
    check("a code is shown with a dash after 3 characters", /^[2-9A-Z]{3}-[2-9A-Z]{3}$/.test(phone.ev("pairShown(" + JSON.stringify(codes[0]) + ")")));
    check("the code comes from crypto.getRandomValues, not Math.random", /const pairRandom=n=>crypto\.getRandomValues\(/.test(src) && !/Math\.random\(\)[^\n]*pair|pair[^\n]*Math\.random\(\)/.test(src));
    check("the key is derived with PBKDF2 SHA-256 and a salt, at least 200000 times, into AES-GCM",
      phone.ev("PAIR_ITERATIONS") >= 200000 && /name:"PBKDF2", salt, iterations:PAIR_ITERATIONS, hash:"SHA-256"/.test(src) && /name:"AES-GCM", length:256/.test(src));
    check("the pairing lasts 10 minutes", phone.ev("PAIR_TTL_MS") === 600000);
  }

  // ---- reading what a person types ----
  {
    const phone = makePhone(new FakeServer(), makeState(["Alex"]));
    const norm = t => phone.ev("pairNormalise(" + JSON.stringify(t) + ")"), valid = t => phone.ev("pairValid(pairNormalise(" + JSON.stringify(t) + "))");
    check("with the dash, without it, in lower case and with spaces all read the same", ["K7P-4QX", "k7p-4qx", "K7P4QX", " k7p 4qx ", "K7P - 4QX\n"].every(t => norm(t) === "K7P4QX"));
    check("a good code is valid", valid("K7P-4QX"));
    check("a code that is too short, too long or empty is not valid", !valid("K7P-4Q") && !valid("K7P-4QXX") && !valid(""));
    check("a lookalike character is not valid", ["K7P-4Q0", "K7P-4QO", "K7P-4Q1", "K7P-4QI", "K7P-4QL", "K7P-4Q!"].every(t => !valid(t)));
  }

  // ---- encrypting and decrypting ----
  {
    const phone = makePhone(new FakeServer(), makeState(["Alex"]));
    const seal = (code, email, pass) => phone.ev("pairSeal(" + JSON.stringify(code) + "," + JSON.stringify(email) + "," + JSON.stringify(pass) + ")");
    const open = (code, row) => phone.ev("pairOpen(" + JSON.stringify(code) + "," + JSON.stringify(row) + ")");
    const row = await seal("K7P4QX", "fam@x.example", "p@ss w\u00f6rd");
    check("the row has a hash, salt, iv and ciphertext and nothing else", JSON.stringify(Object.keys(row)) === '["code_hash","salt","iv","ciphertext"]', Object.keys(row));
    check("the hash is the SHA-256 of the prefix and the normalised code, in hex", row.code_hash === sha(phone.ev("PAIR_PREFIX") + "K7P4QX") && /^[0-9a-f]{64}$/.test(row.code_hash));
    check("the salt is 16 bytes and the iv 12", Buffer.from(row.salt, "base64").length === 16 && Buffer.from(row.iv, "base64").length === 12);
    check("the stored values hold neither the email nor the password nor the code", !JSON.stringify(row).includes("fam") && !JSON.stringify(row).includes("p@ss") && !JSON.stringify(row).includes("K7P"));
    const opened = await open("K7P4QX", row);
    check("the right code gives the email and the password back, odd characters kept", opened.email === "fam@x.example" && opened.password === "p@ss w\u00f6rd", opened);
    let wrong = "";
    try { await open("K7P4QY", row); } catch (e) { wrong = e.message; }
    check("a wrong code fails with a clear message", /could not be read/.test(wrong), wrong);
    const other = await seal("K7P4QX", "fam@x.example", "p@ss w\u00f6rd");
    check("a second seal of the same values differs: new salt, new iv, new ciphertext", other.salt !== row.salt && other.iv !== row.iv && other.ciphertext !== row.ciphertext);
    const subtle = nodeCrypto.webcrypto.subtle, base = await subtle.importKey("raw", Buffer.from("K7P4QX"), "PBKDF2", false, ["deriveKey"]);
    const key = await subtle.deriveKey({ name: "PBKDF2", salt: Buffer.from(row.salt, "base64"), iterations: phone.ev("PAIR_ITERATIONS"), hash: "SHA-256" }, base, { name: "AES-GCM", length: 256 }, false, ["decrypt"]);
    const plain = await subtle.decrypt({ name: "AES-GCM", iv: Buffer.from(row.iv, "base64") }, key, Buffer.from(row.ciphertext, "base64"));
    check("a standard WebCrypto PBKDF2 and AES-GCM decrypt reads it", JSON.parse(Buffer.from(plain).toString("utf8")).password === "p@ss w\u00f6rd");
  }

  // ---- the sending phone ----
  {
    const server = new FakeServer(), clock = { t: Date.now() };
    server.pairClock = () => clock.t;
    const { phone, shown } = await sender(server, clock);
    const els = phone.dom.els, rows = Array.from(server.pairing.values());
    check("the short code is shown in the dialog with a dash", /^[2-9A-Z]{3}-[2-9A-Z]{3}$/.test(shown) && els.setupPairPart.hidden === false, shown);
    check("one row was stored, keyed by the hash of the code", rows.length === 1 && rows[0].code_hash === sha(phone.ev("PAIR_PREFIX") + shown.replace("-", "")), rows.map(r => r.code_hash));
    check("the row expires 10 minutes from now", rows[0].expires_at === new Date(clock.t + 600000).toISOString(), rows[0].expires_at);
    check("the row holds only the hash, salt, iv, ciphertext, expiry and attempts", JSON.stringify(Object.keys(rows[0]).sort()) === '["attempts","ciphertext","code_hash","expires_at","iv","salt"]', Object.keys(rows[0]));
    check("what the server holds has no plaintext: no email, password or code", !JSON.stringify(rows).includes(PASS) && !JSON.stringify(rows).includes("fam@x") && !JSON.stringify(rows).includes(shown.replace("-", "")));
    check("the stored values open with the code shown", await phone.ev("pairOpen(" + JSON.stringify(shown.replace("-", "")) + "," + JSON.stringify(rows[0]) + ")").then(o => o.password === PASS && o.email === FAMILY.email));
    check("the countdown starts at 10:00", els.pairCount.textContent === "Expires in 10:00", els.pairCount.textContent);
    clock.t += 30000; await phone.advance(1000);
    check("the countdown runs down", els.pairCount.textContent === "Expires in 9:30", els.pairCount.textContent);
    clock.t += 30000; await phone.advance(1000);
    check("the QR code goes after 60 seconds but the short code stays", els.setupQrPart.hidden === true && els.setupPairPart.hidden === false && els.pairCode.textContent === shown && server.pairing.size === 1);
    check("nothing about the codes is stored on the sending phone", stored(phone).indexOf(PASS) < 0 && stored(phone).indexOf(shown.replace("-", "")) < 0 && JSON.stringify(phone.sb).indexOf(shown.replace("-", "")) < 0);
    check("the pairing timer runs only while a code is showing", phone.ev("!!pairTimer") === true);
    phone.ev("pairEnd('The pairing code was cancelled.')"); await phone.settle();
    check("Cancel removes the row and, with the QR code gone, closes the dialog back to the password step",
      server.pairing.size === 0 && els.pairCode.textContent === "" && els.setupShow.hidden === true && els.setupAsk.hidden === false && /cancelled/.test(els.setupMsg.textContent), els.setupMsg.textContent);
    check("the pairing timer is stopped", phone.ev("!pairTimer && pairLive === null"));
  }
  {
    // Cancel while the QR code is still showing removes only the short code. Hide, then, removes the row too.
    const server = new FakeServer(), clock = { t: Date.now() };
    server.pairClock = () => clock.t;
    const { phone } = await sender(server, clock), els = phone.dom.els;
    phone.ev("pairEnd('The pairing code was cancelled.')"); await phone.settle();
    check("Cancel with the QR code showing removes the row and keeps the QR code", server.pairing.size === 0 && els.setupPairPart.hidden === true && els.setupShow.hidden === false && els.setupQrPart.hidden === false && /cancelled/.test(els.pairMsg.textContent), els.pairMsg.textContent);
    phone.dom.els.setupPass.value = PASS;
    phone.ev("setupHide('')"); phone.dom.els.setupPass.value = PASS;
    await phone.ev("setupGo()"); await phone.settle();
    check("it can be made again", server.pairing.size === 1 && /^[2-9A-Z]{3}-[2-9A-Z]{3}$/.test(els.pairCode.textContent));
    phone.ev("setupHide('')"); await phone.settle();
    check("Hide, a closed dialog and the app going to the background also remove the row", server.pairing.size === 0 && els.pairCode.textContent === "" && els.setupPairPart.hidden === true);
    phone.dom.els.setupPass.value = PASS;
    await phone.ev("setupGo()"); await phone.settle();
    clock.t += 600000; await phone.advance(1000);
    check("when the 10 minutes are up with the QR code gone the dialog closes with a message", els.setupShow.hidden === true && /pairing code expired/.test(els.setupMsg.textContent) && els.pairCode.textContent === "", els.setupMsg.textContent);
    check("Cancel, Hide and the close all call the same stopping code", /pairCancel"\)\.onclick=\(\)=>pairEnd\("The pairing code was cancelled\."\)/.test(src) && /function setupHide\(msg\)\{\s*setupGen\+\+; clearInterval\(setupTimer\); setupTimer=null; pairStop\(\);/.test(src));
  }
  {
    // the schema has not been run again: the QR code still works and the short code says why it is missing
    const server = new FakeServer(), clock = { t: Date.now() };
    server.pairTables = false;
    const { phone } = await sender(server, clock), els = phone.dom.els;
    check("with no pairing table the QR code still shows", els.setupShow.hidden === false && els.setupQrPart.hidden === false && els.setupText.value.indexOf("#tt-setup=") > 0);
    check("the short code is not shown and the message says to run the schema again", els.setupPairPart.hidden === true && /Run supabase-schema\.sql in Supabase again/.test(els.pairMsg.textContent) && els.pairMsg.className === "hint pin-err", els.pairMsg.textContent);
  }

  // ---- the new phone ----
  {
    const server = new FakeServer(), clock = { t: Date.now() };
    server.pairClock = () => clock.t;
    const { shown } = await sender(server, clock);
    const phone = newPhone(server, clock);
    const status = await claim(phone, shown.toLowerCase().replace("-", " "));
    check("typing the code connects the phone", phone.sb.mode === "supabase" && phone.sb.email === FAMILY.email && phone.sb.url === FAMILY.url, status + " / " + phone.dom.els.fsStatus.textContent);
    check("the row is gone after the claim", server.pairing.size === 0);
    check("the code box is emptied", phone.dom.els.fsPair.value === "");
    check("the password was never put in a box or kept: not in storage, the connection, the data or a toast", stored(phone).indexOf(PASS) < 0 && JSON.stringify(phone.sb).indexOf(PASS) < 0 && JSON.stringify(phone.state).indexOf(PASS) < 0 && JSON.stringify(phone.counts.toasts).indexOf(PASS) < 0 && phone.dom.els.fsPass.value === "");
    check("the email from the code is the only new thing stored, and the code is not stored", stored(phone).indexOf(shown.replace("-", "")) < 0 && stored(phone).indexOf("fam@x.example") > 0);
    check("the button is free again", phone.dom.els.fsPairUse.disabled === false);
    const again = newPhone(server, clock);
    check("a second try with the same code says it is wrong or has run out", /^Pairing code not used\. That pairing code is wrong or has run out/.test(await claim(again, shown)) && again.sb.mode === "github");
  }
  {
    // the dash is optional, and a wrong or malformed code connects nothing
    const server = new FakeServer(), clock = { t: Date.now() };
    server.pairClock = () => clock.t;
    const { shown } = await sender(server, clock);
    const phone = newPhone(server, clock), msg = text => claim(phone, text);
    const wrongCode = shown.slice(0, 5) + (shown[5] === "2" ? "3" : "2") + shown[6];
    check("a wrong code gives a clear message", /^Pairing code not used\. That pairing code is wrong or has run out\. Check the code on the other phone, or make a new one there\.$/.test(await msg(wrongCode)));
    check("it is shown as a problem and nothing is connected", phone.dom.els.fsConnectDot.dataset.s === "bad" && phone.sb.mode === "github" && server.pairing.size === 1);
    check("an empty box asks for the code", /^Pairing code not used\. Type the code first\./.test(await msg("  ")));
    check("a short code says how long it should be", /^Pairing code not used\. It has 6 letters and numbers, like K7P-4QX/.test(await msg("K7P")));
    check("a lookalike character is refused before anything is sent", /^Pairing code not used\. It has 6 letters/.test(await msg("K7P-4Q0")) && server.calls.filter(c => c.table === "rpc:tt_pair_claim").length === 1);
    phone.dom.els.fsUrl.value = "https://x.supabase.co/rest/v1";
    check("a bad project address is named", /^Pairing code not used\. Project URL must look like/.test(await msg(shown)));
    phone.dom.els.fsUrl.value = FAMILY.url; phone.dom.els.fsKey.value = "";
    check("an empty key is named", /^Pairing code not used\. Publishable key is empty/.test(await msg(shown)));
    phone.dom.els.fsKey.value = FAMILY.key;
    check("the right code without the dash connects", /Connected|Syncing|Synced/.test(await msg(shown.replace("-", "")) + phone.dom.els.fsStatus.textContent) && phone.sb.mode === "supabase", phone.dom.els.fsStatus.textContent);
  }
  {
    // an old row is refused, and cleared by the claim
    const server = new FakeServer(), clock = { t: Date.now() };
    server.pairClock = () => clock.t;
    const { shown } = await sender(server, clock);
    clock.t += 600000 + 1000;
    const phone = newPhone(server, clock);
    check("a code used after 10 minutes is refused", /wrong or has run out/.test(await claim(phone, shown)) && phone.sb.mode === "github");
    check("the expired row was cleared by the claim", server.pairing.size === 0);
  }
  {
    // 10 tries a minute in total, whoever makes them
    const server = new FakeServer(), clock = { t: Date.now() };
    server.pairClock = () => clock.t;
    const { shown } = await sender(server, clock);
    const phones = [newPhone(server, clock), newPhone(server, clock)];
    let last = "";
    for (let i = 0; i < 10; i++) last = await claim(phones[i % 2], "ABC-DE" + "23456789AB"[i]);
    check("ten wrong tries across two phones are answered as wrong", /wrong or has run out/.test(last));
    const slow = await claim(phones[0], shown);
    check("the eleventh try says to slow down, even with the right code", /^Pairing code not used\. Too many tries just now\. Wait a minute, then try again\.$/.test(slow) && phones[0].sb.mode === "github", slow);
    check("the row is still there after a slow-down", server.pairing.size === 1);
    clock.t += 61000;
    await claim(phones[1], shown);
    check("after a minute the right code works again", phones[1].sb.mode === "supabase" && server.pairing.size === 0);
  }
  {
    // the schema has not been run again
    const server = new FakeServer(), clock = { t: Date.now() };
    server.pairTables = false;
    const phone = newPhone(server, clock);
    const msg = await claim(phone, "K7P-4QX");
    check("a storage without the pairing function says to run the schema again", /^Pairing code not used\. The family storage is not set up for pairing yet\. Run supabase-schema\.sql in Supabase again/.test(msg) && phone.sb.mode === "github", msg);
    const offline = new FakeServer(); offline.offline = true;
    const off = newPhone(offline, clock);
    check("no connection says so", /^Pairing code not used\. Could not reach the family storage/.test(await claim(off, "K7P-4QX")), off.dom.els.fsConnectMsg.textContent);
  }
  {
    // a connected phone is not switched to another storage by a code
    const server = new FakeServer(), clock = { t: Date.now() };
    const phone = newPhone(server, clock, { password: PASS });
    phone.dom.els.fsEmail = { value: FAMILY.email };
    check("the phone connects first", await connect(phone, PASS));
    phone.dom.els.fsUrl.value = "https://other.supabase.co";
    check("it will not pair to another storage", /^Pairing code not used\. This phone is already connected to another family storage/.test(await claim(phone, "K7P-4QX")) && server.calls.filter(c => c.table === "rpc:tt_pair_claim").length === 0);
  }

  // ---- the project defaults file ----
  {
    const defaults = new Function(root("js/family.js") + "; return FAMILY_PROJECT;")();
    check("js/family.js holds only a project address and a publishable key", Object.keys(defaults).join() === "url,key"
      && (defaults.url === "" || /^https:\/\/[a-z0-9-]+\.supabase\.co$/.test(defaults.url))
      && (defaults.key === "" || /^sb_publishable_/.test(defaults.key)), defaults);
    check("the code in js/family.js has no email or password in it", !/@|password/i.test(root("js/family.js").split("\n").filter(l => !/^\s*\/\//.test(l)).join("\n")));
    check("it loads before the app and the service worker caches it", /<script src="js\/family\.js" defer><\/script>\s*<script src="js\/app\.js" defer><\/script>/.test(root("index.html")) && root("sw.js").indexOf('"./js/family.js"') > 0);
    const project = { url: "https://default.supabase.co", key: "pk_default" };
    const server = new FakeServer(), clock = { t: Date.now() };
    const fresh = makePhone(server, makeState(["Alex"]), { project });
    fresh.ev("renderFamilyStorage()");
    check("a new phone's fields are filled from the defaults", fresh.dom.els.fsUrl.value === project.url && fresh.dom.els.fsKey.value === project.key, [fresh.dom.els.fsUrl.value, fresh.dom.els.fsKey.value]);
    check("the defaults are not saved on the phone", stored(fresh).indexOf("default.supabase") < 0 && fresh.sb.url === "");
    const saved = makePhone(server, makeState(["Alex"]), { project });
    saved.sb.url = "https://saved.supabase.co"; saved.sb.key = "pk_saved";
    saved.ev("renderFamilyStorage()");
    check("values saved on the phone win over the defaults", saved.dom.els.fsUrl.value === "https://saved.supabase.co" && saved.dom.els.fsKey.value === "pk_saved");
    const blank = makePhone(server, makeState(["Alex"]));
    blank.ev("renderFamilyStorage()");
    check("with the defaults empty the fields stay empty", blank.dom.els.fsUrl.value === "" && blank.dom.els.fsKey.value === "");
  }

  // ---- the schema file ----
  {
    const sql = root("docs/supabase-schema.sql");
    const has = re => re.test(sql);
    check("the pairing table has the columns Daniel specified", has(/create table if not exists public\.pairing \(\s*code_hash\s+text\s+primary key,\s*salt\s+text,\s*iv\s+text,\s*ciphertext\s+text,\s*created_at\s+timestamptz default now\(\),\s*expires_at\s+timestamptz not null,\s*attempts\s+int\s+default 0\s*\);/));
    check("row level security is on for the pairing tables", has(/alter table public\.pairing\s+enable row level security;/) && has(/alter table public\.pair_attempts\s+enable row level security;/));
    check("a family member may insert and nobody may select", has(/create policy family_insert on public\.pairing\s+for insert to authenticated with check \(public\.is_family\(\)\);/) && !/grant[^;]*select[^;]*public\.pairing/i.test(sql) && has(/revoke all on public\.pairing, public\.pair_attempts from anon, authenticated;/) && has(/grant insert on public\.pairing to authenticated;/));
    check("every policy is dropped before it is created, so the file can run again", [...sql.matchAll(/create policy (\w+) on (public\.\w+)/g)].every(m => sql.includes("drop policy if exists " + m[1] + " on " + m[2] + ";")));
    check("the claim function is security definer, clears expired rows, limits to 10 a minute and deletes the match",
      has(/create or replace function public\.tt_pair_claim\(p_code_hash text\) returns jsonb\s+language plpgsql security definer set search_path = ''/) && has(/delete from public\.pairing where expires_at <= now\(\);/) && has(/interval '1 minute'/) && has(/if tries > 10 then/) && has(/delete from public\.pairing where code_hash = p_code_hash and expires_at > now\(\) returning \* into claimed;/));
    check("anon and signed-in phones may call the claim", has(/grant execute on function public\.tt_pair_claim\(text\) to anon, authenticated, service_role;/));
    check("only a family member may cancel", has(/function public\.tt_pair_cancel[\s\S]*?if not public\.is_family\(\) then/) && has(/revoke execute on function public\.tt_pair_cancel\(text\) from public, anon;/));
    check("the daily keep-alive clears expired rows", has(/function public\.tt_keepalive\(\)[\s\S]*?delete from public\.pairing where expires_at <= now\(\);[\s\S]*?\$\$;/));
    check("the app calls the two functions and the table the schema defines", /rpc\("tt_pair_claim", \{p_code_hash:hash\}\)/.test(src) && /rpc\("tt_pair_cancel", \{p_code_hash:live\.hash\}\)/.test(src) && /from\("pairing"\)\.insert\(/.test(src));
    check("the Pair button and the Enter key are wired", /fsPairUse"\)\.onclick=\(\)=>pairUse\(fsField\("fsPair"\)\.value\)/.test(src) && /fsPair"\)\.onkeydown/.test(src));
  }
  finished = true;
  console.log((failed ? "FAILED " : "ok ") + passed + " passed, " + failed + " failed");
  process.exit(failed ? 1 : 0);
}
// A promise that never settles ends the run silently, so say so.
let finished = false;
process.on("exit", () => { if (!finished) { console.log("FAILED the run stopped before the end"); process.exitCode = 1; } });
main().catch(e => { console.log("CRASH", e && e.stack || e); process.exit(1); });
