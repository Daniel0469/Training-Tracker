"use strict";
const KEY = "flLiveTracker_v1";

// There is deliberately NO default program baked into the app. A fresh install
// starts blank (see load()) and the Program tab is built from scratch or from a
// shared session; Daniel & Cerys's real plan lives in the synced store, not in
// here. A hardcoded copy only ever went stale - it drifted months behind the
// live program, and because saveProgram() stamps a fresh updatedAt and pushes,
// "reset to default" would have propagated that stale copy to BOTH phones.

const clone = o => JSON.parse(JSON.stringify(o));
let state = load();
if(!state.namesSet){ if(state.people[0]==="Me") state.people[0]="Daniel"; if(state.people[1]==="Partner") state.people[1]="Cerys"; state.namesSet=true; try{save();}catch(e){} }
let activeTab = "home";
let curSession = state.program.order[0];
let curDate = trainingDateStr();
let justSavedId = null;
// Per person+session drafts of the in-progress log form, so switching person
// (or session) mid-entry doesn't wipe unsaved sets. Lets both people log from
// one phone. Persisted (see loadDrafts) so a mid-workout reload keeps them.
let formDrafts = {};
// Per person+session workout timers (same keying as formDrafts), persisted
// alongside the drafts. Elapsed time is wall-clock, so a timer left running
// keeps counting across a reload exactly as it does across a backgrounded app.
let sessionTimers = {};
// Exercises added to today's log only (gym busy, something hurts, swapped a
// movement) - same person+session keying, and deliberately NOT written into
// state.program: the program is the plan, this is what actually happened.
// Cleared when the session is saved; the save summary offers to promote one.
let formExtras = {};
let timerInterval = null;

function load(){
  try{
    const s = JSON.parse(localStorage.getItem(KEY));
    if(s && s.program && s.program.sessions){
      if(!Array.isArray(s.weights)) s.weights=["",""];
      if(!Array.isArray(s.goals)) s.goals=["",""];
      // Existing installs get the exact colours they already look like today
      // (Daniel navy, Cerys purple) - no visual change from adding this feature.
      if(!Array.isArray(s.colors)) s.colors=["navy","purple"];
      if(!s.coaching || typeof s.coaching!=="object") s.coaching={};
      if(!Array.isArray(s.coachingLog)) s.coachingLog=[];
      // Garmin heart-rate zones, keyed by person name like `coaching`. Written by
      // mcp-garmin (`--hrzones`), read-only in the app.
      if(!s.hrZones || typeof s.hrZones!=="object") s.hrZones={};
      // Garmin's own race-time predictions, keyed by person. Input for the coach's
      // 5k estimate (and the unreviewed fallback on Home), never edited in the app.
      if(!s.racePredictions || typeof s.racePredictions!=="object") s.racePredictions={};
      if(!Array.isArray(s.suggestions)) s.suggestions=[];
      // What each person says is holding a session back, keyed person -> session
      // name. Written by the coach when they tell it (mcp-coach write_limiter),
      // read-only in the app.
      if(!s.limiters || typeof s.limiters!=="object") s.limiters={};
      if(!Array.isArray(s.meals)) s.meals=[];
      if(!Array.isArray(s.bodyweights)){
        // Migrate: seed history from each person's current single weight.
        s.bodyweights=[];
        var today=new Date().toISOString().slice(0,10);
        s.weights.forEach(function(w,i){
          var kg=parseFloat(w);
          if(!isNaN(kg)) s.bodyweights.push({person:s.people[i], date:today, kg:kg});
        });
      }
      // Migrate: the default warm-ups were fixed kg, so Daniel and Cerys both saw
      // the same numbers. Percentages resolve against each person's own last top
      // set, so convert — but only where the text still matches the old default,
      // leaving anything edited in Edit Program alone.
      if(!s.warmupPct){
        var WU={ "70x10, then 110x5":"50%x10, then 75%x5",
                 "light x8":"50%x8",
                 "empty x10, then ~60% x5":"empty x10, then 60%x5",
                 "10x10, then 14x5":"50%x10, then 75%x5" };
        Object.keys(s.program.sessions).forEach(function(k){
          (s.program.sessions[k].exercises||[]).forEach(function(ex){
            var repl=WU[(ex.warmup||"").trim()];
            if(repl) ex.warmup=repl;
          });
        });
        s.warmupPct=true;
      }
      return s;
    }
  }catch(e){}
  // Genuinely blank install: no accounts, no program - see renderCreateAccount().
  return { people:["",""], weights:["",""], goals:["",""], colors:["",""], coaching:{}, coachingLog:[], suggestions:[], limiters:{}, meals:[], bodyweights:[], hrZones:{}, racePredictions:{}, activePerson:0, program:{order:[], sessions:{}}, logs:[] };
}
function save(){ progExIndex=null; localStorage.setItem(KEY, JSON.stringify(state)); }
// Both people train the same plan, so the program is shared - but a plain sync
// only ever pushed it, never pulled one down, which left each phone with its own
// drifting copy and the store holding whichever synced last. Every program edit
// now stamps `updatedAt` and pushes straight away; a sync adopts the store's
// copy only when it is genuinely newer (see mergeInData), so an edit made on one
// phone is never replaced by an older one from the other. Devices with no sync
// configured are untouched by all of this - autoSync no-ops without a repo+token.
function saveProgram(){
  if(state.program) state.program.updatedAt=new Date().toISOString();
  save();
  autoSync();
}

// ---- Bodyweight & assisted movements ----
// A pull-up's real load isn't the number you type: it's your own bodyweight,
// plus anything hung off a belt or minus however much the machine is helping.
// Without this, everything downstream (volume, PRs, e1RM, the 🥇 medal) reads a
// bigger typed number as better - exactly backwards for assistance - and a
// bodyweight-only movement scores zero volume and never tracks a best.
//   ex.load  = "bw"     -> bodyweight + what you type
//            = "assist" -> bodyweight - what you type
//            (absent)   -> normal, the typed number IS the load
//   ex.bwPct = the share of bodyweight the movement actually lifts (pull-up
//              100, press-up ~65), so volume stays believable.
// Name -> program exercise, so a set logged before the flag existed still gets
// scored by how that exercise is defined today. Rebuilt whenever state is saved.
// The same name can be set up two different ways in two sessions - Tom's
// "Back extension" is a bodyweight movement on his upper day and a loaded one
// on his leg day. Taking the first match would then score an unstamped set by
// the wrong definition, so a name whose definitions disagree resolves to
// nothing and the set is read as the plain number typed. Stamped entries are
// unaffected - they carry their own load type.
let progExIndex=null;
function programExerciseByName(name){
  if(!progExIndex){
    progExIndex={};
    const clash={};
    Object.keys((state.program&&state.program.sessions)||{}).forEach(function(k){
      ((state.program.sessions[k].exercises)||[]).forEach(function(ex){
        if(!ex || !ex.name) return;
        const seen=progExIndex[ex.name];
        if(!seen){ progExIndex[ex.name]=ex; return; }
        if((seen.load||"")!==(ex.load||"") || (seen.bwPct||100)!==(ex.bwPct||100)) clash[ex.name]=true;
      });
    });
    Object.keys(clash).forEach(function(n){ progExIndex[n]=null; });
  }
  return progExIndex[name]||null;
}
function loadTypeOf(e){
  if(!e) return "";
  if(e.load) return e.load;
  const def=programExerciseByName(e.name);
  return (def && def.load) || "";
}
function loadPctOf(e){
  const src = (e && e.load) ? e : programExerciseByName(e && e.name);
  const pct = src && src.bwPct;
  return (pct && pct>0) ? Math.min(100, pct) : 100;
}
// Bodyweight as at a session's date: the nearest weigh-in on or before it (so
// old sessions stay scored at the weight you actually were), else the earliest
// one after, else the current figure from Settings.
function bodyweightOn(person, date){
  const list=bwFor(person);
  let best=null;
  for(let i=0;i<list.length;i++){ if(list[i].date<=date) best=list[i]; else break; }
  if(!best && list.length) best=list[0];
  if(best) return best.kg;
  const pi=state.people.indexOf(person);
  const w=parseFloat(pi>=0 ? state.weights[pi] : NaN);
  return isNaN(w) ? null : w;
}
// What one set actually loaded, in kg. Takes either a logged entry or a program
// exercise - both carry the load flags.
function setLoad(e, typed, person, date){
  const type=loadTypeOf(e);
  const v=parseFloat(typed);
  if(!type) return v;
  const bw=bodyweightOn(person, date);
  if(bw==null) return v; // never weighed in: nothing better to do than take the number typed
  const own=bw*(loadPctOf(e)/100);
  const add=isNaN(v)?0:v;
  return Math.max(0, type==="assist" ? own-add : own+add);
}

// ---- In-progress log form (drafts + timers) ----
// Kept in their own localStorage key, never in the export/sync payload: an
// unsaved half-entered form is this device's work-in-progress, not shared data.
// These used to be memory-only, which is why entries "cleared randomly during a
// workout" - a phone that backgrounds the app long enough for the browser to
// discard the page reloads into an empty form. Anything older than a session's
// worth of hours is dropped rather than resurfacing days later.
const DRAFT_KEY = KEY + "_drafts";
const DRAFT_TTL_MS = 12*60*60*1000;
function loadDrafts(){
  try{
    const d=JSON.parse(localStorage.getItem(DRAFT_KEY));
    if(d && d.savedAt && (Date.now()-d.savedAt) < DRAFT_TTL_MS)
      return {drafts:d.drafts||{}, timers:d.timers||{}, extras:d.extras||{}};
  }catch(e){}
  return {drafts:{}, timers:{}, extras:{}};
}
function saveDrafts(){
  try{
    if(!Object.keys(formDrafts).length && !Object.keys(sessionTimers).length && !Object.keys(formExtras).length){
      localStorage.removeItem(DRAFT_KEY); return;
    }
    localStorage.setItem(DRAFT_KEY, JSON.stringify({savedAt:Date.now(), drafts:formDrafts, timers:sessionTimers, extras:formExtras}));
  }catch(e){}
}
// Restored here rather than where they're declared: DRAFT_KEY isn't initialised
// yet at that point (const, same script).
const restoredDrafts = loadDrafts();
formDrafts = restoredDrafts.drafts;
sessionTimers = restoredDrafts.timers;
formExtras = restoredDrafts.extras;

function toast(msg){
  const t=document.getElementById("toast"); t.textContent=msg; t.classList.add("show");
  clearTimeout(t._t); t._t=setTimeout(()=>t.classList.remove("show"),1800);
}
const esc = s => String(s==null?"":s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const possessive = n => /s$/i.test(n) ? n+"'" : n+"'s";
const todayStr = ()=> new Date().toISOString().slice(0,10);
// The training day rolls over at ~5am, not midnight: a session logged at 1am
// Friday still belongs to Thursday's workout. Subtract the cutoff (in local
// time) before reading the date, so the default log date + auto-selected
// session both land on the right training day. `now` is injectable for tests.
function trainingDateStr(now){
  var d = now ? new Date(now) : new Date();
  d.setHours(d.getHours()-5);
  var m=d.getMonth()+1, day=d.getDate();
  return d.getFullYear()+"-"+(m<10?"0":"")+m+"-"+(day<10?"0":"")+day;
}
// Splits a session's exercises into render blocks: contiguous runs sharing a
// groupId become {type:"group", groupId, eis:[...]}, everything else is
// {type:"single", eis:[i]}. Shared by the Program editor and the Log form so
// both agree on what counts as a superset - grouped members are always kept
// adjacent (see move()/groupSelected()), so a simple contiguous scan suffices.
function exerciseBlocks(exercises){
  const blocks=[]; let i=0;
  while(i<exercises.length){
    const gid=exercises[i].groupId;
    if(gid){
      const eis=[i]; let j=i+1;
      while(j<exercises.length && exercises[j].groupId===gid){ eis.push(j); j++; }
      blocks.push({type:"group", groupId:gid, eis});
      i=j;
    } else {
      blocks.push({type:"single", eis:[i]});
      i++;
    }
  }
  return blocks;
}
// A session's `day` is a label plus these two lookups, nothing more. Anything
// that isn't a weekday name - "Optional" - falls through to 99 below, so it
// sorts to the bottom of the list, and can never match in sessionForDate, so
// the calendar never opens it for you. That's what "optional" means here: it
// exists in the program and you can pick it any day you fancy it, but it isn't
// part of the week and nothing nags you about it.
const DOW={monday:1,tuesday:2,wednesday:3,thursday:4,friday:5,saturday:6,sunday:7};
function orderedKeys(){
  return state.program.order.slice().sort(function(a,b){
    var da=DOW[String(state.program.sessions[a].day||"").toLowerCase()]||99;
    var db=DOW[String(state.program.sessions[b].day||"").toLowerCase()]||99;
    return da-db;
  });
}

function sessionForDate(dstr){
  var wd=new Date(dstr+"T12:00:00").getDay();
  var names=["sunday","monday","tuesday","wednesday","thursday","friday","saturday"];
  var target=names[wd];
  var keys=state.program.order.filter(function(k){return String(state.program.sessions[k].day||"").toLowerCase()===target;});
  if(keys.length<2) return keys[0];
  // More than one session on this weekday - the two cardio sessions share
  // Wednesday. Which one is it today?
  //   1. the coach's assignment, if it's still live (see nextCardioCard)
  //   2. otherwise alternate: whichever of them you did NOT do last
  //   3. otherwise program.order decides, as it always did
  var live=liveNextCardio();
  if(live){
    var picked=keys.filter(function(k){ return state.program.sessions[k].name===live.session; })[0];
    if(picked) return picked;
  }
  var alt=alternatedKey(keys);
  return alt || keys[0];
}
// Of several sessions sharing a day, the one whose turn it is: the one you did
// least recently. Previously order[0] always won, so the alternation was a
// convention you had to remember and a skipped week silently flipped it.
function alternatedKey(keys){
  var p=state.people[state.activePerson];
  var names={};
  keys.forEach(function(k){ names[state.program.sessions[k].name]=k; });
  var seen={}, logs=state.logs.filter(function(l){ return l.person===p; })
    .sort(function(a,b){ return a.date<b.date?1:a.date>b.date?-1:b.id-a.id; });
  // Newest first, so the first time we meet a name is the last time it was done.
  logs.forEach(function(l){ if(names[l.sessionName] && !(l.sessionName in seen)) seen[l.sessionName]=l.date; });
  // Anything never done comes first - that's the one that's overdue.
  var never=keys.filter(function(k){ return !(state.program.sessions[k].name in seen); });
  if(never.length) return never[0];
  var oldest=null;
  keys.forEach(function(k){
    var d=seen[state.program.sessions[k].name];
    if(oldest===null || d<seen[state.program.sessions[oldest].name]) oldest=k;
  });
  return oldest;
}
// The coach's next-cardio assignment, or null once it's been used up. It's spent
// the moment a cardio session is logged on or after the day it was written: the
// advice was for that session, and leaving it up would have a fortnight-old
// prescription still choosing which session Wednesday opens.
function liveNextCardio(){
  var p=state.people[state.activePerson];
  var nc=((state.coaching&&state.coaching[p])||{}).nextCardio;
  if(!nc || !nc.session || !nc.updated) return null;
  var since=String(nc.updated).slice(0,10);
  var done=state.logs.some(function(l){
    if(l.person!==p || String(l.date)<since) return false;
    return (l.entries||[]).some(function(e){ return isRunning(e)||isIntervalEntry(e); });
  });
  return done ? null : nc;
}
function isLifting(ex){ return /kg|assist/i.test(ex.cols[0]) && /rep/i.test(ex.cols[1]); }
// A running exercise carries both a distance and a time column (any order),
// which lets us auto-compute pace. Rows are splits.
function isRunning(ex){ return ex.cols.some(c=>/dist/i.test(c)) && ex.cols.some(c=>/time/i.test(c)); }
// Does a Garmin activity correspond to this exercise? Every run does, but so does
// an interval piece whose columns are paces rather than distance+time - those are
// still recorded on the watch. Kept separate from isRunning() on purpose: that one
// drives pace auto-compute, splits and the run importer, which only make sense for
// a real distance+time entry. This one only decides "expect a Garmin activity".
function isGarminCardio(ex){ return isRunning(ex) || ex.garminRun===true; }
function colIndex(ex, re){ for(var i=0;i<ex.cols.length;i++){ if(re.test(ex.cols[i])) return i; } return -1; }
function parseTimeToMin(s){
  s=String(s).trim(); if(!s) return NaN;
  if(s.indexOf(":")>=0){ var p=s.split(":"); return (parseFloat(p[0])||0) + (parseFloat(p[1])||0)/60; }
  return parseFloat(s); // bare number = decimal minutes
}
function fmtPace(minPerKm){
  if(!isFinite(minPerKm)||minPerKm<=0) return "";
  var m=Math.floor(minPerKm), s=Math.round((minPerKm-m)*60);
  if(s===60){ m++; s=0; }
  return m+":"+(s<10?"0":"")+s;
}
// Fill a running row's pace column (min/km) from its distance + time.
function updatePace(tr, ex){
  var di=colIndex(ex,/dist/i), ti=colIndex(ex,/time/i), pi=colIndex(ex,/pace/i);
  if(di<0||ti<0||pi<0) return;
  var dInp=tr.querySelector('[data-c="'+di+'"]'), tInp=tr.querySelector('[data-c="'+ti+'"]'), pInp=tr.querySelector('[data-c="'+pi+'"]');
  if(!dInp||!tInp||!pInp) return;
  var dist=parseFloat(dInp.value), tmin=parseTimeToMin(tInp.value);
  pInp.value = (!isNaN(dist)&&dist>0&&!isNaN(tmin)&&tmin>0) ? fmtPace(tmin/dist) : "";
}
function fmtMmSs(sec){ sec=Math.round(sec); var m=Math.floor(sec/60), s=sec%60; return m+":"+(s<10?"0":"")+s; }
// Parse a Garmin/Strava TCX: each <Lap> -> one split {km, sec}.
function parseTcx(doc){
  const laps=[], nodes=doc.getElementsByTagName("Lap");
  for(let i=0;i<nodes.length;i++){
    const dm=nodes[i].getElementsByTagName("DistanceMeters")[0];
    const tt=nodes[i].getElementsByTagName("TotalTimeSeconds")[0];
    const km=dm?parseFloat(dm.textContent)/1000:NaN, sec=tt?parseFloat(tt.textContent):NaN;
    if(!isNaN(km)&&!isNaN(sec)) laps.push({km, sec});
  }
  return laps;
}
function haversineM(la1,lo1,la2,lo2){
  const R=6371000, rad=x=>x*Math.PI/180;
  const dLa=rad(la2-la1), dLo=rad(lo2-lo1);
  const a=Math.sin(dLa/2)**2+Math.cos(rad(la1))*Math.cos(rad(la2))*Math.sin(dLo/2)**2;
  return 2*R*Math.asin(Math.sqrt(a));
}
// Parse a GPX: no laps, so sum trackpoint legs into one summary {km, sec}.
function parseGpx(doc){
  const pts=doc.getElementsByTagName("trkpt");
  if(pts.length<2) return [];
  let dist=0, t0=null, t1=null, prev=null;
  for(let i=0;i<pts.length;i++){
    const lat=parseFloat(pts[i].getAttribute("lat")), lon=parseFloat(pts[i].getAttribute("lon"));
    if(isNaN(lat)||isNaN(lon)) continue;
    if(prev) dist+=haversineM(prev.lat,prev.lon,lat,lon);
    prev={lat,lon};
    const te=pts[i].getElementsByTagName("time")[0];
    if(te){ const t=new Date(te.textContent); if(!isNaN(t)){ if(!t0)t0=t; t1=t; } }
  }
  const km=dist/1000; if(km<=0) return [];
  return [{km, sec:(t0&&t1)?(t1-t0)/1000:0}];
}
// Fill a running exercise's rows (splits) on the log form from a TCX/GPX file.
function importRunIntoCard(text, ex, card){
  let doc;
  try{ doc=new DOMParser().parseFromString(text, "application/xml"); }catch(e){ toast("Couldn't read that file"); return; }
  if(doc.getElementsByTagName("parsererror").length){ toast("That file isn't valid TCX/GPX"); return; }
  let laps=parseTcx(doc); if(!laps.length) laps=parseGpx(doc);
  if(!laps.length){ toast("No run data found in file"); return; }
  const di=colIndex(ex,/dist/i), ti=colIndex(ex,/time/i);
  const tb=card.querySelector("tbody");
  while(tb.rows.length<laps.length){
    tb.insertAdjacentHTML("beforeend", setRowHtml(tb.rows.length+1, ex, "-"));
    wireSetRow(tb.rows[tb.rows.length-1], ex, cardBestWeight(ex));
  }
  laps.forEach((lap,i)=>{
    const inputs=tb.rows[i].querySelectorAll('[data-c]');
    if(di>=0&&inputs[di]) inputs[di].value=Math.round(lap.km*100)/100;
    if(ti>=0&&inputs[ti]) inputs[ti].value=fmtMmSs(lap.sec);
    updatePace(tb.rows[i], ex);
  });
  startTimerIfIdle();
  toast(laps.length+" split"+(laps.length>1?"s":"")+" imported");
}
function parseRange(target){
  const m=String(target).match(/(\d+)\s*[-]\s*(\d+)/);
  return m? {low:+m[1],high:+m[2]} : null;
}

function renderPeople(){
  // Self-heal: if the active slot has no account but the other one does (e.g.
  // right after a skip, or stale data), point activePerson at the real one.
  if(!state.people[state.activePerson] && state.people[1-state.activePerson]) state.activePerson=1-state.activePerson;
  // Drive the app accent (via CSS --brand) and chrome colour off the active person's chosen swatch.
  document.documentElement.setAttribute("data-color", (state.colors&&state.colors[state.activePerson])||"navy");
  updateMeta();
  const el=document.getElementById("ptoggle");
  let html="";
  state.people.forEach((n,i)=>{
    if(n) html+='<button data-p="'+i+'" class="'+(state.activePerson===i?'active':'')+'">'+esc(n)+'</button>';
  });
  const emptySlot=state.people.findIndex(n=>!n);
  if(emptySlot>=0 && state.people.some(n=>n)) html+='<button class="mini" data-addperson="'+emptySlot+'">+ Add</button>';
  el.innerHTML=html;
  el.querySelectorAll("[data-p]").forEach(b=>b.onclick=()=>{
    if(+b.dataset.p===state.activePerson) return;
    captureDraft();
    state.activePerson=+b.dataset.p; save(); renderPeople(); renderView();
    if(activeTab==="log" && formDrafts[draftKey()])
      toast("Restored "+possessive(state.people[state.activePerson])+" unsaved entry");
  });
  el.querySelectorAll("[data-addperson]").forEach(b=>b.onclick=()=>renderCreateAccount(+b.dataset.addperson));
  const w=state.weights[state.activePerson];
  document.getElementById("sub").textContent =
    w ? state.people[state.activePerson]+" · "+w+" kg" : "Tap the gear to set bodyweight";
}
// Full-screen-ish onboarding card: no account exists yet (slotIndex 0), or an
// existing account is offering to add a second (slotIndex 1, skippable).
function renderCreateAccount(slotIndex){
  document.getElementById("tabs").style.display="none";
  document.getElementById("ptoggle").style.display="none";
  document.getElementById("settingsBtn").style.display="none";
  const isSecond = slotIndex===1 && state.people[0];
  let html='<div class="card">'
    + '<div class="sec-title" style="margin:0 0 4px">'+(isSecond?"Add a second account":"Welcome - create your account")+'</div>'
    + '<div class="hint" style="margin-bottom:16px">'+(isSecond
        ?"Optional - this device can be shared by up to two people."
        :"Give your tracker a name and a colour to get started. Nothing is sent anywhere; it's saved on this device.")+'</div>'
    + '<label class="fld" style="margin-bottom:14px">Name<input id="caName" type="text" placeholder="e.g. Alex" autocomplete="off"></label>'
    + '<label class="fld" style="margin-bottom:18px">Colour<div class="swatchpick" id="caColor"></div></label>'
    + '<div class="row" style="justify-content:flex-end">'
    + (isSecond?'<button class="btn btn-ghost" id="caSkip">Skip - just me for now</button>':"")
    + '<button class="btn btn-primary" id="caCreate">Create account</button>'
    + '</div></div>';
  document.getElementById("view").innerHTML=html;
  const colorEl=document.getElementById("caColor");
  const otherColor = state.people[1-slotIndex] ? state.colors[1-slotIndex] : null;
  renderSwatchPicker(colorEl, firstAvailableSwatch(otherColor), otherColor);
  wireSwatchPicker(colorEl);
  const reveal=()=>{
    document.getElementById("tabs").style.display="";
    document.getElementById("ptoggle").style.display="";
    document.getElementById("settingsBtn").style.display="";
  };
  document.getElementById("caCreate").onclick=()=>{
    const nm=(document.getElementById("caName").value||"").trim();
    if(!nm){ toast("Enter a name"); return; }
    state.people[slotIndex]=nm;
    state.colors[slotIndex]=readSwatchPicker(colorEl);
    state.activePerson=slotIndex;
    save(); reveal(); renderPeople(); renderView();
    toast("Welcome, "+nm+"!");
  };
  if(isSecond){
    document.getElementById("caSkip").onclick=()=>{ reveal(); renderPeople(); renderView(); };
  }
}
document.getElementById("tabs").querySelectorAll("button").forEach(b=>{
  b.onclick=()=>switchTab(b.dataset.tab);
});

function latestLog(person, sessionKey){
  return state.logs.filter(l=>l.person===person && l.sessionKey===sessionKey)
    .sort((a,b)=> (a.date<b.date?1:a.date>b.date?-1: (a.id<b.id?1:-1)))[0];
}
function bestWeightSoFar(person, exerciseName){
  var best=-Infinity;
  state.logs.filter(function(l){return l.person===person;}).forEach(function(l){
    var e=(l.entries||[]).find(function(x){return x.name===exerciseName;}); if(!e) return;
    var wu=e.warmup||[];
    e.rows.forEach(function(r,ri){ if(wu.indexOf(ri)>=0) return; var w=setLoad(e, r[0], person, l.date); if(!isNaN(w)&&w>best) best=w; });
  });
  return best;
}
function latestEntryAnywhere(person, exName){
  var bestLog=null, bestEntry=null;
  state.logs.forEach(function(l){
    if(l.person!==person) return;
    var e=(l.entries||[]).find(function(x){return x.name===exName;}); if(!e) return;
    if(!bestLog || l.date>bestLog.date || (l.date===bestLog.date && l.id>bestLog.id)){ bestLog=l; bestEntry=e; }
  });
  return bestLog ? {log:bestLog, entry:bestEntry} : null;
}
// Escaped display of one logged row across its columns. Lifting reads
// "weight x reps"; anything else (cardio/running) joins its filled cells.
function fmtRow(cols, r){
  cols = cols||[];
  const lift = /kg|assist/i.test(cols[0]||"") && /rep/i.test(cols[1]||"");
  const n = Math.max(cols.length, r.length);
  const vals=[]; for(let i=0;i<n;i++){ vals.push(r[i]==null?"":String(r[i]).trim()); }
  if(lift) return esc(vals[0])+(vals[1]!==""?" x "+esc(vals[1]):"");
  const ne=vals.filter(v=>v!=="");
  return ne.length ? ne.map(esc).join(" / ") : "-";
}
function daysAgo(dateStr){
  return Math.round((new Date() - new Date(dateStr+"T12:00:00"))/86400000);
}
// Monday (ISO week start) of the week containing dateStr, as YYYY-MM-DD.
function weekMonday(dateStr){
  var d=new Date(dateStr+"T12:00:00");
  var off=(d.getDay()+6)%7; // 0 = Monday
  d.setDate(d.getDate()-off);
  var m=d.getMonth()+1, day=d.getDate();
  return d.getFullYear()+"-"+(m<10?"0":"")+m+"-"+(day<10?"0":"")+day;
}
function weeklyVolumes(person){
  var map={};
  state.logs.filter(function(l){return l.person===person;}).forEach(function(l){ var wk=weekMonday(l.date); map[wk]=(map[wk]||0)+(l.volume||0); });
  return Object.keys(map).sort().map(function(wk){ return {week:wk, volume:map[wk]}; });
}
function relTime(dateStr){
  var d=daysAgo(dateStr);
  if(d<=0) return "today";
  if(d===1) return "yesterday";
  if(d<7) return d+" days ago";
  var w=Math.round(d/7);
  if(d<56) return w+(w===1?" week":" weeks")+" ago";
  var m=Math.round(d/30.44);
  if(d<700) return m+(m===1?" month":" months")+" ago";
  var y=Math.round(d/365.25);
  return y+(y===1?" year":" years")+" ago";
}

function draftKey(){ return state.people[state.activePerson]+"|"+curSession; }
// The exercise list the Log form works from: the session's programmed exercises
// followed by anything added for today only. Every `data-ei` on the log form
// indexes into THIS, not state.program - so the extras get set rows, drafts,
// warm-up flags, RPE and PR medals with no special-casing anywhere else.
function logExercises(){
  const sess=state.program.sessions[curSession]||{};
  return (sess.exercises||[]).concat(formExtras[draftKey()]||[]);
}
function programExCount(){
  return (((state.program.sessions[curSession]||{}).exercises)||[]).length;
}
// Typing doesn't re-render, so nothing used to reach localStorage between the
// explicit capture points (tab/person/session switch) - a phone that discarded
// the page mid-set lost that set. Debounced so it's one write per pause, not
// one per keystroke.
let draftSaveTimer=null;
function scheduleDraftSave(){
  clearTimeout(draftSaveTimer);
  draftSaveTimer=setTimeout(()=>{ draftSaveTimer=null; captureDraft(); }, 700);
}
function flushDraftSave(){ clearTimeout(draftSaveTimer); draftSaveTimer=null; captureDraft(); }
// Last chance to keep the form: iOS discards backgrounded pages without warning,
// and pagehide/hidden is the only notice we get before it happens.
window.addEventListener("pagehide", flushDraftSave);
document.addEventListener("visibilitychange", ()=>{ if(document.visibilityState==="hidden") flushDraftSave(); });
// Read the live log form into formDrafts under the current person+session,
// or drop the draft if nothing has been entered. Call before any action that
// re-renders the form (person/session/date change, tab switch).
function captureDraft(){
  if(activeTab!=="log") return;
  const form=document.getElementById("exForm");
  if(!form) return;
  const entries=[]; let any=false;
  form.querySelectorAll(".ex").forEach(card=>{
    const ei=+card.dataset.ei;
    const rows=[], done=[], warm=[];
    card.querySelectorAll("tbody tr").forEach(tr=>{
      const vals=[]; let rowHas=false;
      tr.querySelectorAll('[data-c]').forEach(inp=>{ vals.push(inp.value); if(inp.value!=="") rowHas=true; });
      const dn=tr.querySelector('[data-done]').checked;
      const wu=tr.classList.contains("wset");
      rows.push(vals); done.push(dn); warm.push(wu);
      if(rowHas||dn||wu) any=true;
    });
    const rpeSel=card.querySelector('[data-exrpe] button.sel');
    const rpe=rpeSel?rpeSel.dataset.d:null;
    if(rpe!=null) any=true;
    entries[ei]={rows,done,warm,rpe};
    // A changed set count is worth persisting on its own, so sets you add or
    // remove survive a re-render even before anything has been typed.
    // Runs deliberately render one blank split row whatever the program says
    // (renderExForm), so compare against what was rendered, not ex.sets - or an
    // untouched cardio session counts as a draft and gets stored for nothing.
    const exDef=logExercises()[ei];
    const shownRows = exDef ? (isRunning(exDef) ? 1 : Math.max(1, exDef.sets||1)) : 0;
    if(exDef && rows.length!==shownRows) any=true;
  });
  const sel=document.querySelector("#diff button.sel");
  const difficulty=sel?+sel.dataset.d:null;
  const fb=document.getElementById("feedback");
  const feedback=fb?fb.value:"";
  if(difficulty!=null||feedback.trim()!=="") any=true;
  const key=draftKey();
  if(any) formDrafts[key]={entries,difficulty,feedback}; else delete formDrafts[key];
  saveDrafts();
}
// Re-apply a saved draft onto the freshly-rendered form. Returns true if one
// was restored. Runs after the form is wired so added rows get their handlers.
function restoreDraft(){
  const draft=formDrafts[draftKey()];
  if(!draft) return false;
  const exs=logExercises();
  document.querySelectorAll("#exForm .ex").forEach(card=>{
    const ei=+card.dataset.ei;
    const d=draft.entries[ei]; if(!d) return;
    const ex=exs[ei]; if(!ex) return;
    const tb=card.querySelector("tbody");
    const best=cardBestWeight(ex);
    while(tb.rows.length<d.rows.length){
      tb.insertAdjacentHTML("beforeend", setRowHtml(tb.rows.length+1, ex, "-"));
      wireSetRow(tb.rows[tb.rows.length-1], ex, best);
    }
    // ...and drop extras, so sets you removed stay removed across a re-render
    // (leaving/returning to the tab used to add them straight back).
    while(tb.rows.length>d.rows.length && tb.rows.length>1) tb.deleteRow(tb.rows.length-1);
    d.rows.forEach((r,i)=>{
      const tr=tb.rows[i]; if(!tr) return;
      const inputs=tr.querySelectorAll('[data-c]');
      (r||[]).forEach((v,ci)=>{ if(inputs[ci]) inputs[ci].value=v; });
      if(isRunning(ex)) updatePace(tr, ex);
      if(d.warm && d.warm[i]){
        tr.classList.add("wset");
        const sn=tr.querySelector("[data-setno]"); if(sn) sn.textContent="W";
      }
      if(d.done[i]){
        const cb=tr.querySelector('[data-done]');
        cb.checked=true; tr.classList.add("done");
        updateSetMedal(tr, ex, best);
      }
    });
    if(d.rpe!=null){
      const b=card.querySelector('[data-exrpe] button[data-d="'+d.rpe+'"]');
      if(b) b.classList.add("sel");
    }
  });
  if(draft.difficulty!=null){
    const b=document.querySelector('#diff button[data-d="'+draft.difficulty+'"]');
    if(b) b.classList.add("sel");
  }
  if(draft.feedback){ const f=document.getElementById("feedback"); if(f) f.value=draft.feedback; }
  return true;
}

function getTimer(){ return sessionTimers[draftKey()] || {elapsedSec:0, running:false, lastStart:0}; }
function timerElapsed(t){ return Math.floor(t.elapsedSec + (t.running ? (Date.now()-t.lastStart)/1000 : 0)); }
function fmtDuration(sec){
  sec=Math.max(0,Math.floor(sec));
  const h=Math.floor(sec/3600), m=Math.floor((sec%3600)/60), s=sec%60;
  const two=n=>(n<10?"0":"")+n;
  return h>0 ? h+":"+two(m)+":"+two(s) : m+":"+two(s);
}
function startTimer(){
  const key=draftKey();
  const t=sessionTimers[key] || {elapsedSec:0, running:false, lastStart:0};
  if(!t.running){ t.running=true; t.lastStart=Date.now(); sessionTimers[key]=t; }
  saveDrafts();
  ensureTimerTick(); updateTimerUI();
}
function pauseTimer(){
  const t=sessionTimers[draftKey()]; if(!t||!t.running) return;
  t.elapsedSec += (Date.now()-t.lastStart)/1000; t.running=false;
  saveDrafts();
  updateTimerUI();
}
function toggleTimer(){ const t=sessionTimers[draftKey()]; if(t&&t.running) pauseTimer(); else startTimer(); }
function resetTimer(){ delete sessionTimers[draftKey()]; saveDrafts(); updateTimerUI(); }
// Auto-start on the first bit of data entered, but never fight a deliberate
// pause: only starts when no timer has ever been created for this key.
function startTimerIfIdle(){ if(!sessionTimers[draftKey()]) startTimer(); }
function ensureTimerTick(){
  if(timerInterval) return;
  timerInterval=setInterval(()=>{
    const t=sessionTimers[draftKey()];
    if(!document.getElementById("timerDisplay") || !t || !t.running){
      clearInterval(timerInterval); timerInterval=null; return;
    }
    updateTimerUI();
  },1000);
}
function updateTimerUI(){
  const el=document.getElementById("timerDisplay"); if(!el) return;
  const t=getTimer();
  el.textContent=fmtDuration(timerElapsed(t));
  el.classList.toggle("running", t.running);
  const btn=document.getElementById("timerToggle");
  if(btn) btn.textContent = t.running ? "Pause" : (t.elapsedSec>0 ? "Resume" : "Start");
}

// Has anyone ever coached this install? Used to keep coaching-specific copy off
// the screen of someone who has no coach - the features are all opt-in and
// laptop-side, so a plain local install should never be told about plumbing it
// hasn't got.
// Has this install ever had a Garmin activity linked, or zones pulled? Same idea
// as hasCoaching: don't describe kit they haven't got.
function hasGarmin(){
  if(Object.keys(state.hrZones||{}).length) return true;
  return state.logs.some(l=>l && (l.garminActivityId || l.garminWanted || l.garmin));
}
function hasCoaching(){
  const c=state.coaching||{};
  return Object.keys(c).some(k=>{
    const e=c[k]||{};
    return e.overall || e.fiveK || e.nextCardio
      || Object.keys(e.bySession||{}).length || Object.keys(e.byExercise||{}).length;
  });
}
function renderLog(){
  const p = state.people[state.activePerson];
  const opts = orderedKeys().map(k=>{
    const s=state.program.sessions[k];
    return '<option value="'+k+'" '+(k===curSession?'selected':'')+'>'+esc(s.name)+' · '+esc(s.day)+'</option>';
  }).join("");
  const sess = state.program.sessions[curSession];
  const prev = latestLog(p, curSession);
  const coach = (state.coaching && state.coaching[p]) || {};
  const coachFor = name => (coach.byExercise && coach.byExercise[name]) || "";
  const prevNote = prev
    ? "Inputs start blank. "+esc(possessive(p))+" last session ("+relTime(prev.date)+") is shown in the <b>Last</b> column - beat it."
    : "No previous "+esc(p)+" log for this session yet - today sets the baseline.";

  let html = '<div class="card">'
    + '<div class="flex-between" style="margin-bottom:12px">'
    + '<label class="fld grow" style="max-width:340px">Session<select id="sessionSel">'+opts+'</select></label>'
    + '<label class="fld" style="width:160px">Date<input id="logDate" type="date" value="'+curDate+'"></label>'
    + '</div><div class="hint" style="margin-top:-4px">Logging for <b>'+esc(p)+'</b>. '+prevNote+'</div>'
    + '<div class="row" style="margin-top:11px;gap:8px;align-items:center">'
    + '<span class="timer" id="timerDisplay">0:00</span>'
    + '<button class="mini" id="timerToggle">Start</button>'
    + '<button class="mini" id="timerReset">Reset</button>'
    + '<span class="hint" style="margin:0">Workout time - saved with the session.</span>'
    + '</div></div>';

  const sessNote = (coach.bySession && sess && coach.bySession[sess.name]) || "";
  if(sessNote){
    html += '<div class="card coach-card"><div class="sec-title">🧠 Coach'+(coach.updated?' &middot; '+relTime(coach.updated):"")+'</div>'
      + '<div style="white-space:pre-wrap"><b>'+esc(sess.name)+':</b> '+esc(sessNote)+'</div>'
      + '</div>';
  }

  // The coach's cardio assignment, on the session it's about - that's where you
  // read it, standing at the treadmill, rather than having to go back to Home.
  const nc=(coach.nextCardio&&sess&&coach.nextCardio.session===sess.name)?nextCardioCardHtml(p):"";
  html += nc;

  // What this person said is holding this session back. Their words, not the
  // coach's read of the numbers - see limiters() in mcp-coach/server.py.
  const limiter=((state.limiters&&state.limiters[p])||{})[sess?sess.name:""]||"";
  if(limiter){
    html += '<div class="card"><div class="sec-title">&#128681; What\'s holding this back</div>'
      + '<div style="white-space:pre-wrap">'+esc(limiter)+'</div>'
      + '<div class="hint" style="margin-top:5px">'+esc(possessive(p))+' own words. Your coach reads this before the numbers.</div></div>';
  }

  html += lastTimeHtml(sess, prev);

  // Programmed exercises plus anything added for today only.
  const exs = logExercises();

  // Cardio day: the run auto-fills from Garmin, so tell them to just save.
  // Unless nothing here has ever been near a watch, in which case leading with
  // "if you wear your Garmin" is telling someone about kit they haven't got -
  // the manual route is their route, so it goes first and the watch isn't
  // mentioned at all.
  if(exs.some(e=>isRunning(e))){
    html += hasGarmin()
      ? '<div class="cardio-note">⌚ <b>Cardio day.</b> If you wear your Garmin, just <b>log &amp; save</b> - leave the run\'s row <b>empty</b> and its distance, splits, pace &amp; ♥ HR fill themselves in once it syncs. <b>Tick its box or don\'t</b> - that\'s only an on-screen "done" marker, it never types anything in and isn\'t saved, so the row stays free for Garmin either way. Prefer to do it yourself? Type the splits below, or <b>⬆ import</b> a file.</div>'
      : '<div class="cardio-note">🏃 <b>Cardio day.</b> Type your distance and time below and the <b>pace works itself out</b>. One row per split if you want them, or just the total on one row. Got a watch file? <b>⬆ import</b> a TCX/GPX from Garmin or Strava instead.</div>';
  } else if(exs.some(e=>isGarminCardio(e)) && hasGarmin()){
    // Interval-style cardio: the person types their own paces, so Garmin only adds
    // the measurements it alone knows (HR, zones, calories) - it never overwrites.
    // Nothing useful to say here without a watch: you just type your paces in, and
    // the columns already say that.
    html += '<div class="cardio-note">⌚ <b>Cardio day.</b> Fill in your paces as normal - if you wear your Garmin, it adds your <b>♥ HR, heart-rate zones and calories</b> to this session once it syncs, without touching anything you typed.</div>';
  }

  // The session's own warm-up / cool-down notes (Program tab) bracket the
  // exercises, in the order you actually do them.
  if(sess.warmupNote){
    html += '<div class="card"><div class="sec-title">&#128293; Warm-up</div>'
      + '<div style="white-space:pre-wrap">'+esc(sess.warmupNote)+'</div></div>';
  }

  html += '<div id="exForm">';
  exerciseBlocks(exs).forEach(block=>{
    const cardsHtml = block.eis.map(ei=>{
      const ex=exs[ei];
      const last = prev && (prev.entries||[]).find(e=>e.name===ex.name);
      const lastRun = (last && isRunning(ex)) ? runSummaryFromEntry(last, prev&&prev.garmin) : "";
      return renderExForm(ex,ei,last,prev?prev.date:"",recentNote(p,ex,prev),coachFor(ex.name),lastRun);
    }).join("");
    // Grouped exercises get a wrapping .superset card; each inner .ex card is
    // otherwise unchanged, so every existing per-card system (wireExCard,
    // drafts, RPE, warm-ups) keeps working exactly as it does for a standalone
    // exercise - see docs/PROJECT-STATUS.md "Next up" item 6 for why.
    html += block.type==="group" ? '<div class="superset"><div class="superset-label">&#8646; Superset</div>'+cardsHtml+'</div>' : cardsHtml;
  });
  html += '</div>';

  html += '<div class="row" style="margin:-3px 0 13px;align-items:center">'
    + '<button class="mini" id="addTodayEx">&#10133; Add an exercise for today</button>'
    + '<span class="hint" style="margin:0;flex:1">Machine taken, or swapping something? Just this session - your program stays as it is.</span></div>';

  if(sess.cooldownNote){
    html += '<div class="card"><div class="sec-title">&#129482; Cool-down</div>'
      + '<div style="white-space:pre-wrap">'+esc(sess.cooldownNote)+'</div></div>';
  }

  html += '<div class="card"><div class="sec-title">How did the session feel?</div>'
    + '<div class="row" style="margin-bottom:10px"><div class="grow">'
    + '<div class="hint" style="margin-bottom:4px">Difficulty (1 easy &middot; 10 max effort)</div>'
    + '<div class="diff" id="diff">'+[1,2,3,4,5,6,7,8,9,10].map(n=>'<button data-d="'+n+'">'+n+'</button>').join("")+'</div>'
    + '</div></div>'
    + '<label class="fld">Your own notes (optional)<textarea id="feedback" placeholder="e.g. Right knee tight on squats. Felt strong today."></textarea></label>'
    // Only worth saying to someone who actually has a coach. On an install with
    // no coaching and no cloud sync it promised a feature that was never coming,
    // and pointed at a "sync" that isn't set up.
    + (hasCoaching() ? '<div class="hint">🧠 Coaching notes show at the top and on each exercise after a sync.</div>' : '')
    + '</div>'
    + '<div class="row" style="justify-content:flex-end;margin-bottom:30px">'
    + '<button class="btn btn-ghost" id="clearForm">Clear</button>'
    + '<button class="btn btn-primary" id="saveSession">Save session &check;</button></div>';

  document.getElementById("view").innerHTML = html;

  document.getElementById("sessionSel").onchange=e=>{ captureDraft(); curSession=e.target.value; renderView(); };
  document.getElementById("logDate").onchange=e=>{ captureDraft(); curDate=e.target.value; var sk=sessionForDate(curDate); if(sk) curSession=sk; renderView(); };
  document.getElementById("diff").querySelectorAll("button").forEach(b=>b.onclick=()=>{
    document.querySelectorAll("#diff button").forEach(x=>x.classList.remove("sel"));
    b.classList.add("sel");
  });
  document.getElementById("view").querySelectorAll("[data-addset]").forEach(b=>b.onclick=()=>addSetRow(b));
  document.getElementById("view").querySelectorAll("[data-delset]").forEach(b=>b.onclick=()=>{
    const tb=b.closest(".ex").querySelector("tbody");
    if(tb.rows.length>1){ tb.deleteRow(tb.rows.length-1); }
  });
  document.getElementById("exForm").querySelectorAll(".ex").forEach(card=>{
    const ex=exs[+card.dataset.ei];
    if(ex) wireExCard(card, ex);
  });
  document.getElementById("exForm").querySelectorAll("[data-delextra]").forEach(b=>b.onclick=()=>removeTodayExercise(+b.dataset.delextra));
  // Capture first: saving the dialog re-renders the form.
  document.getElementById("addTodayEx").onclick=()=>{ captureDraft(); openExDlg(curSession, null, true); };
  document.getElementById("saveSession").onclick=saveSession;
  document.getElementById("clearForm").onclick=()=>{ delete formDrafts[draftKey()]; saveDrafts(); renderView(); };
  document.getElementById("timerToggle").onclick=toggleTimer;
  document.getElementById("timerReset").onclick=resetTimer;
  const startOnEntry=()=>{ startTimerIfIdle(); scheduleDraftSave(); };
  const form=document.getElementById("exForm");
  form.addEventListener("input", startOnEntry);
  form.addEventListener("change", startOnEntry);
  document.getElementById("feedback").addEventListener("input", scheduleDraftSave);
  restoreDraft();
  document.querySelectorAll("#exForm .ex").forEach(card=>{
    const ex=exs[+card.dataset.ei];
    if(ex) updateWarmup(card, ex);
  });
  updateTimerUI();
  if(getTimer().running) ensureTimerTick();
}

// Which on-screen keyboard a column asks for. This used to be decided per
// exercise - only a lifting exercise got a keypad - so any other numeric column
// popped the full text keyboard mid-set ("lunges comes up with keyboard instead
// of numpad": its second column is Distance (m), not Reps). Decided per column
// name instead. Times (mm:ss) and free text still need real letters/colons.
function colInputMode(col){
  const c=String(col||"");
  if(/time|pace|note|comment/i.test(c)) return "";
  if(/kg|weight|dist|km|level|speed|incline|%/i.test(c)) return "decimal";
  if(/rep|hr|bpm|cal|min|sec|watt|rpm|cadence|count|step|round/i.test(c)) return "numeric";
  return "";
}
function setRowHtml(n,ex,prevCell){
  const paceIdx = isRunning(ex) ? colIndex(ex,/pace/i) : -1;
  let cells="";
  ex.cols.forEach((c,ci)=>{
    const im=colInputMode(c);
    let attr = im ? ' inputmode="'+im+'"' : "";
    if(ci===paceIdx) attr += ' readonly';
    cells += '<td><input data-c="'+ci+'"'+attr+' value="" placeholder="'+esc(c)+'"></td>';
  });
  return '<tr><td class="setno" data-setno data-n="'+n+'" title="Tap to mark as a warm-up set">'+n+'</td>'+cells
    + '<td class="prev">'+prevCell+'</td>'
    + '<td class="done-cell"><input type="checkbox" data-done title="Mark set done"><span class="medal" data-medal hidden>&#129351;</span></td></tr>';
}
// "Most recent for this movement in ANY session" note; empty when the most
// recent occurrence is the log already shown in the Last column.
function recentNote(person, ex, prev){
  if(!isLifting(ex)) return "";
  const rec=latestEntryAnywhere(person, ex.name);
  if(!rec || (prev && rec.log.id===prev.id)) return "";
  // Best set by what it actually loaded, but shown as what was typed - this is a
  // cue for what to key in next time, not a scoreboard.
  let top=null, tw=-Infinity;
  rec.entry.rows.forEach(r=>{ const w=setLoad(rec.entry, r[0], person, rec.log.date); if(!isNaN(w)&&w>tw){tw=w;top=r;} });
  if(!top) return "";
  if(top[0]==="" || top[0]==null) return "";
  return 'Most recent: <b>'+esc(top[0])+' kg'+(top[1]!==""&&top[1]!=null?' × '+esc(top[1]):"")+'</b> · '
    + relTime(rec.log.date)+' ('+esc(rec.log.sessionName)+')';
}
// Warm-up notes may use "NN%" tokens; resolve them to kg from a reference
// weight (the top set entered so far, else last session's top set).
function warmupBase(card){
  let top=-Infinity;
  card.querySelectorAll('tbody tr [data-c="0"]').forEach(inp=>{ const w=parseFloat(inp.value); if(!isNaN(w)&&w>top) top=w; });
  if(top===-Infinity){ const lt=parseFloat(card.dataset.lasttop); if(!isNaN(lt)) top=lt; }
  return top>-Infinity ? top : null;
}
function computeWarmupText(warmup, base){
  // Once a reference weight is known, show the resolved kg in place of the
  // "NN%" token (e.g. "40%x8" -> "40kg x8"); before then, keep the raw %.
  return warmup.replace(/(\d+(?:\.\d+)?)\s*%/g, function(m,pct){
    if(base==null) return m;
    var kg=Math.round((base*parseFloat(pct)/100)/2.5)*2.5;
    return kg+"kg";
  });
}
function updateWarmup(card, ex){
  if(!ex.warmup || ex.warmup.indexOf("%")<0) return;
  const span=card.querySelector("[data-warmup]"); if(!span) return;
  span.textContent=computeWarmupText(ex.warmup, warmupBase(card));
}
function renderExForm(ex,ei,last,prevDate,recent,coach,lastRun){
  const running = isRunning(ex);
  // Runs get a single blank split row — the watch (or the importer) fills the
  // real splits in. Other exercises take their set count from the program only
  // (it used to be max(program, last log), which permanently inflated it).
  const rows = running ? 1 : Math.max(1, ex.sets||1);
  const fmt = r => fmtRow(ex.cols, r);
  let body="";
  for(let i=0;i<rows;i++){
    // Per-set "Last" only makes sense for lifting; a run's km-by-km splits don't
    // line up session to session, so runs show a single "Last run" line instead.
    const r = !running && last && last.rows[i] ? last.rows[i] : null;
    body += setRowHtml(i+1, ex, r?fmt(r):"-");
  }
  let lastTop=-Infinity;
  if(last && isLifting(ex)) last.rows.forEach(r=>{ const w=parseFloat(r[0]); if(!isNaN(w)&&w>lastTop) lastTop=w; });
  const lastTopAttr = lastTop>-Infinity ? ' data-lasttop="'+lastTop+'"' : '';
  const warmupHtml = ex.warmup
    ? '<div class="warmup">Warm-up: <span data-warmup>'+esc(computeWarmupText(ex.warmup, lastTop>-Infinity?lastTop:null))+'</span></div>'
    : "";
  return '<div class="card ex'+(ex.todayOnly?" ex-today":"")+'" data-ei="'+ei+'" data-name="'+esc(ex.name)+'"'+lastTopAttr+'>'
    + '<div class="ex-head"><div class="ex-name">'+esc(ex.name)
      + '<button type="button" class="wrench'+(ex.notes?' has':'')+'" data-exnotes-toggle aria-expanded="false" title="Machine settings">&#128295;</button>'
      + (ex.todayOnly?'<span class="pill today-pill">Today only</span>':'')
      + '</div><div class="ex-meta">'+esc(ex.target)
      + (ex.todayOnly?' <button type="button" class="mini" data-delextra="'+ei+'" title="Remove from today">&#10005;</button>':'')
      + '</div></div>'
    + warmupHtml
    + (running && lastRun ? '<div class="recent">🏃 Last run: <b>'+esc(lastRun)+'</b></div>' : "")
    // Saved machine settings read out in place - no point hiding the seat height
    // behind a tap when you're stood at the machine. The 🔧 still opens the
    // editor (which replaces this line while it's open).
    + '<div class="notes" data-exnotes-view'+(ex.notes?'':' hidden')+'>&#128295; '+esc(ex.notes||"")+'</div>'
    + '<div class="notes-wrap" data-notes-wrap hidden>'
      + '<textarea class="notes" data-exnotes rows="2" placeholder="Seat height, pins, machine settings…">'+esc(ex.notes||"")+'</textarea>'
      + '</div>'
    + (coach?'<div class="coach">🧠 Coach: '+esc(coach)+'</div>':"")
    + (recent?'<div class="recent">🕑 '+recent+'</div>':"")
    + '<div class="sets-wrap"><table class="sets"><thead><tr><th></th>'+ex.cols.map(c=>'<th>'+esc(c)+'</th>').join("")
    + '<th class="prev" title="'+esc(prevDate)+'">Last'+(prevDate?' · '+relTime(prevDate):"")+'</th><th class="done-cell"></th></tr></thead><tbody>'+body+'</tbody></table></div>'
    // RPE isn't a lifting-only idea - a treadmill interval session has an
    // effort level just as much as a set of squats does, and it's the only
    // subjective read we get on a run beyond Garmin's HR. isGarminCardio picks
    // out exactly the cardio worth rating (the intervals, the Zone 2 run) and
    // leaves the Min/Notes warm-up and cool-down rows alone.
    + (isLifting(ex) || isGarminCardio(ex) ? '<div class="row" style="margin-top:6px;align-items:center;gap:6px;flex-wrap:nowrap">'
        + '<span class="hint" style="margin:0;flex:none">RPE</span><div class="diff diff-sm" data-exrpe>'
        + [1,2,3,4,5,6,7,8,9,10].map(n=>'<button type="button" data-d="'+n+'">'+n+'</button>').join("")
        + '</div></div>' : '')
    + '<div class="row" style="margin-top:8px"><button class="mini" data-addset>+ set</button>'
    + '<button class="mini" data-delset>- set</button>'
    + (isRunning(ex)?'<button class="mini" data-runimport style="margin-left:auto">⬆ Import run (TCX/GPX)</button><input type="file" data-runfile accept=".tcx,.gpx,.xml" style="display:none">':'')
    + '</div></div>';
}
// Drop a today-only exercise again (added by mistake, or the machine freed up).
// The draft's entries are indexed by the same `ei` space, so they have to shift
// with it or every card after this one would show the wrong sets back.
function removeTodayExercise(ei){
  captureDraft();
  const key=draftKey();
  const arr=formExtras[key]||[];
  const idx=ei-programExCount();
  if(idx<0 || idx>=arr.length) return;
  const name=arr[idx].name;
  arr.splice(idx,1);
  if(!arr.length) delete formExtras[key];
  const d=formDrafts[key];
  if(d && Array.isArray(d.entries)) d.entries.splice(ei,1);
  saveDrafts(); renderView(); toast("Removed "+name+" from today");
}
function addSetRow(btn){
  const card=btn.closest(".ex"); const ei=+card.dataset.ei;
  const ex=logExercises()[ei];
  const tb=card.querySelector("tbody");
  tb.insertAdjacentHTML("beforeend", setRowHtml(tb.rows.length+1, ex, "-"));
  const tr=tb.rows[tb.rows.length-1];
  wireSetRow(tr, ex, cardBestWeight(ex));
  if(isLifting(ex)){
    const firstWeight=tb.rows[0].querySelector('[data-c="0"]');
    const w=tr.querySelector('[data-c="0"]');
    if(firstWeight && firstWeight.value && w && !w.value) w.value=firstWeight.value;
  }
}

// Best saved weight is only recomputed once per card render/added row, not
// per keystroke — it can't change until the session is saved.
function cardBestWeight(ex){
  return isLifting(ex) ? bestWeightSoFar(state.people[state.activePerson], ex.name) : -Infinity;
}
function updateSetMedal(tr, ex, best){
  const medal=tr.querySelector("[data-medal]");
  if(!medal) return;
  const w=setLoad(ex, tr.querySelector('[data-c="0"]').value, state.people[state.activePerson], curDate);
  // Warm-up sets never earn a PR medal.
  medal.hidden = !(isLifting(ex) && !tr.classList.contains("wset") && !isNaN(w) && best>-Infinity && w>best);
}
function wireSetRow(tr, ex, best){
  const cb=tr.querySelector("[data-done]");
  const weightInput=tr.querySelector('[data-c="0"]');
  const repsInput=tr.querySelector('[data-c="1"]');
  if(!cb) return;
  cb.addEventListener("change", ()=>{
    tr.classList.toggle("done", cb.checked);
    if(cb.checked){
      if(isLifting(ex) && repsInput && !repsInput.value.trim()){
        const range=parseRange(ex.target);
        if(range) repsInput.value=range.high;
      }
      updateSetMedal(tr, ex, best);
    } else {
      tr.querySelector("[data-medal]").hidden=true;
    }
  });
  if(weightInput) weightInput.addEventListener("input", ()=>{ if(cb.checked) updateSetMedal(tr, ex, best); });
  if(isRunning(ex)){
    const upd=()=>updatePace(tr, ex);
    tr.querySelectorAll('[data-c]').forEach(inp=>inp.addEventListener("input", upd));
  }
  const setno=tr.querySelector("[data-setno]");
  if(setno) setno.addEventListener("click", ()=>{
    const wu=tr.classList.toggle("wset");
    setno.textContent = wu ? "W" : setno.dataset.n;
    updateSetMedal(tr, ex, best); // warm-up rows show no medal
  });
}
function wireExCard(card, ex){
  const tbody=card.querySelector("tbody");
  const best=cardBestWeight(ex);
  Array.from(tbody.rows).forEach(tr=>wireSetRow(tr, ex, best));
  const rpePicker=card.querySelector("[data-exrpe]");
  if(rpePicker){
    rpePicker.querySelectorAll("button").forEach(b=>b.onclick=()=>{
      rpePicker.querySelectorAll("button").forEach(x=>x.classList.remove("sel"));
      b.classList.add("sel");
    });
  }
  const firstWeight = tbody.rows[0] && tbody.rows[0].querySelector('[data-c="0"]');
  if(firstWeight && isLifting(ex)){
    // Mirror the first set's weight into rows the user hasn't set themselves.
    // Track the last mirrored value so multi-digit entry keeps updating: typing
    // "6" then "0" fills every row with "60", not stuck at "6" (the old check
    // only filled empty rows, so after the first digit they were never updated).
    let mirrored=firstWeight.value||"";
    firstWeight.addEventListener("input", ()=>{
      const val=firstWeight.value;
      Array.from(tbody.rows).slice(1).forEach(tr=>{
        const w=tr.querySelector('[data-c="0"]');
        if(w && (!w.value || w.value===mirrored)) w.value=val;
      });
      mirrored=val;
    });
  }
  if(ex.warmup && ex.warmup.indexOf("%")>=0){
    updateWarmup(card, ex);
    tbody.addEventListener("input", ()=>updateWarmup(card, ex));
  }
  // Machine settings are editable mid-session: `ex` is the live program object,
  // so changes stick for next time too. Saved on blur to avoid writing on every
  // keystroke; autoSync on change so the other phone picks the settings up.
  const notesEl=card.querySelector("[data-exnotes]");
  const notesWrap=card.querySelector("[data-notes-wrap]");
  const notesBtn=card.querySelector("[data-exnotes-toggle]");
  const notesView=card.querySelector("[data-exnotes-view]");
  // The read-out line and the editor are the same information, so only one of
  // them is on screen at a time.
  const showView=()=>{
    if(!notesView) return;
    notesView.innerHTML="&#128295; "+esc(ex.notes||"");
    if(ex.notes) notesView.removeAttribute("hidden"); else notesView.setAttribute("hidden","");
  };
  if(notesBtn && notesWrap){
    notesBtn.onclick=()=>{
      const opening=notesWrap.hasAttribute("hidden");
      if(opening){
        notesWrap.removeAttribute("hidden");
        if(notesView) notesView.setAttribute("hidden","");
        if(notesEl){ autoGrow(notesEl); notesEl.focus(); }
      } else {
        notesWrap.setAttribute("hidden","");
        showView();
      }
      notesBtn.setAttribute("aria-expanded", opening?"true":"false");
    };
  }
  if(notesEl){
    notesEl.addEventListener("input", ()=>autoGrow(notesEl));
    notesEl.addEventListener("change", ()=>{
      const v=notesEl.value.trim();
      if(v===(ex.notes||"")) return;
      ex.notes=v; saveProgram();
      if(notesBtn) notesBtn.classList.toggle("has", !!v); // wrench stays lit when settings are saved
      toast("Machine settings saved");
    });
  }
  const runBtn=card.querySelector("[data-runimport]");
  if(runBtn){
    const fileInp=card.querySelector("[data-runfile]");
    runBtn.onclick=()=>fileInp.click();
    fileInp.onchange=e=>{
      const f=e.target.files[0]; if(!f) return;
      const rd=new FileReader();
      rd.onload=()=>importRunIntoCard(rd.result, ex, card);
      rd.readAsText(f);
      fileInp.value="";
    };
  }
}

function saveSession(){
  const sess=state.program.sessions[curSession];
  const exs=logExercises();
  const person=state.people[state.activePerson];
  const prev=latestLog(person,curSession);
  const date=document.getElementById("logDate").value || todayStr();
  const sel=document.querySelector("#diff button.sel");
  const difficulty = sel? +sel.dataset.d : null;
  const feedback=document.getElementById("feedback").value.trim();
  const entries=[];
  document.querySelectorAll("#exForm .ex").forEach(card=>{
    const ex=exs[+card.dataset.ei] || {cols:["Weight (kg)","Reps"], name:card.dataset.name};
    const name=ex.name || card.dataset.name;
    const rows=[], warmup=[];
    card.querySelectorAll("tbody tr").forEach(tr=>{
      const vals=[]; let has=false;
      tr.querySelectorAll('[data-c]').forEach(inp=>{ const v=inp.value.trim(); vals.push(v); if(v!=="") has=true; });
      if(has){
        if(tr.classList.contains("wset")) warmup.push(rows.length);
        rows.push(vals);
      }
    });
    const rpeSel=card.querySelector('[data-exrpe] button.sel');
    // A running exercise is still recorded even with nothing typed in - that's
    // the whole point of "just log & save" on a cardio day (see the cardio-day
    // hint in renderLog): the Garmin sync fills the blank row in later, but
    // only if the entry (and garminWanted below) actually exists to fill.
    if(rows.length || isRunning(ex)){ const en={name,cols:ex.cols.slice(),rows}; if(warmup.length) en.warmup=warmup;
      if(rpeSel) en.rpe=rpeSel.dataset.d;
      // Stamp the load type onto the entry so it scores the same for ever, even
      // if the exercise is later re-flagged or dropped from the program.
      if(ex.load){ en.load=ex.load; if(ex.bwPct) en.bwPct=ex.bwPct; }
      if(ex.muscles&&ex.muscles.length) en.muscles=ex.muscles.slice(); entries.push(en); }
  });
  if(!entries.length && !feedback){ toast("Nothing entered yet"); return; }
  var volume=0;
  entries.forEach(function(en){ var wu=en.warmup||[]; en.rows.forEach(function(r,ri){ if(wu.indexOf(ri)>=0) return; var w=setLoad(en, r[0], person, date), reps=parseInt(r[1],10); if(!isNaN(w)&&!isNaN(reps)) volume+=w*reps; }); });
  volume=Math.round(volume);
  var prs=[];
  entries.forEach(function(en){
    if(!isLifting(en)) return; // col-0 is only a weight (kg) for lifting entries
    var wu=en.warmup||[];
    var ws=en.rows.map(function(r,ri){return wu.indexOf(ri)>=0?NaN:setLoad(en, r[0], person, date);}).filter(function(v){return !isNaN(v);});
    if(!ws.length) return;
    var thisMax=Math.max.apply(null,ws);
    var prevBest=bestWeightSoFar(person,en.name);
    if(prevBest>-Infinity && thisMax>prevBest){ en.pr=Math.round(thisMax*10)/10; prs.push({name:en.name,weight:en.pr}); }
  });
  const durationSec = timerElapsed(getTimer());
  const log={ id:Date.now(), date, person, sessionKey:curSession, sessionName:sess.name,
    entries, feedback, difficulty, volume, durationSec };
  // Cardio session: flag it so the Garmin sync (laptop) can link the activity's extra
  // data (HR, zones, cadence, calories, and splits when the run row was left blank).
  // Checks the exercise definitions, not the saved entries, because an interval
  // exercise carries a garminRun flag that the logged entry doesn't. Cleared once
  // linked; see mcp-garmin.
  if(exs.some(e=>isGarminCardio(e))) log.garminWanted=true;
  state.logs.push(log); save();
  // Anything added for today that was actually logged is offered to the program
  // on the save popup - grab it before the form's extras are cleared.
  const loggedNames={}; entries.forEach(function(en){ loggedNames[en.name]=true; });
  const promotable=(formExtras[draftKey()]||[]).filter(function(ex){ return loggedNames[ex.name]; });
  const promoteKey=curSession;
  delete formDrafts[draftKey()];
  delete sessionTimers[draftKey()];
  delete formExtras[draftKey()];
  saveDrafts();
  justSavedId=log.id;
  switchTab("history", true); // draft just cleared above — don't re-capture it
  showSaveSummary(volume, prs, entries, promotable, promoteKey);
  autoSync(); // push this session to the shared store automatically (if sync is set up)
}

function renderHistory(){
  const logs=[...state.logs].sort((a,b)=> (a.date<b.date?1:a.date>b.date?-1:b.id-a.id));
  let html='<div class="card"><div class="flex-between">'
    + '<div class="sec-title" style="margin:0">History - '+logs.length+' session'+(logs.length===1?"":"s")+'</div>'
    + '<select id="histFilter"><option value="all">Everyone</option>'
    + state.people.map(p=>'<option value="'+esc(p)+'">'+esc(p)+'</option>').join("")
    + '</select></div></div>';
  if(!logs.length){
    html+='<div class="card empty">No sessions logged yet.<br>Tap <b>Log it</b> on <b>Home</b> to record your first one.</div>';
    document.getElementById("view").innerHTML=html; return;
  }
  // This-week summary for the active person (volume, sessions, muscle heatmap).
  const p=state.people[state.activePerson];
  const pc = personSwatch(p);
  const thisWk=weekMonday(trainingDateStr());
  const wkLogs=state.logs.filter(l=>l.person===p && weekMonday(l.date)===thisWk);
  const wkVol=wkLogs.reduce((t,l)=>t+(l.volume||0),0);
  html+='<div class="card"><div class="sec-title">📅 This week - '+esc(p)+' <span class="pill" data-sw="'+pc+'">'+wkLogs.length+' session'+(wkLogs.length===1?"":"s")+'</span></div>'
    + '<div class="row" style="align-items:center;gap:16px">'
    + '<div><div style="font-size:22px;font-weight:800">'+wkVol.toLocaleString()+' kg</div><div class="hint" style="margin:0">volume this week</div></div>'
    + '<div id="weekMap" style="flex:1;min-width:180px;max-width:280px"></div>'
    + '</div>'
    + '<div class="hint" style="margin:10px 0 4px">Weekly volume</div><div class="chart-box" style="height:150px"><canvas id="weekChart"></canvas></div></div>';
  html+='<div id="histList"></div>';
  document.getElementById("view").innerHTML=html;
  // Weekly muscle heatmap: clone the (styled) save-dialog map and shade it.
  const src=document.getElementById("muscleSvg");
  if(src && wkLogs.length){
    const clone=src.cloneNode(true); clone.removeAttribute("id"); clone.style.maxWidth="280px";
    paintMuscleMap(clone, muscleSetsForLogs(wkLogs));
    document.getElementById("weekMap").appendChild(clone);
  } else if(document.getElementById("weekMap")){
    document.getElementById("weekMap").innerHTML='<div class="hint" style="margin:0">No sessions yet this week.</div>';
  }
  drawWeekChart(p);
  const filter=document.getElementById("histFilter");
  filter.onchange=()=>drawHist(filter.value);
  drawHist("all");
}
let weekChart=null;
function drawWeekChart(person){
  const canvas=document.getElementById("weekChart"); if(!canvas) return;
  const weeks=weeklyVolumes(person).slice(-10);
  const i=state.people.indexOf(person);
  const dark=document.documentElement.getAttribute("data-theme")==="dark";
  const col=swatchColor(state.colors[i],dark);
  const tickCol=dark?"#9aa3b2":"#697086", gridCol=dark?"rgba(255,255,255,.09)":"rgba(20,30,55,.08)";
  if(weekChart) weekChart.destroy();
  weekChart=new Chart(canvas,{
    type:"bar",
    data:{labels:weeks.map(w=>w.week.slice(5)), datasets:[{label:person+" weekly kg", data:weeks.map(w=>w.volume), backgroundColor:col}]},
    options:{responsive:true, maintainAspectRatio:false,
      scales:{x:{ticks:{color:tickCol},grid:{color:gridCol}}, y:{beginAtZero:true, ticks:{color:tickCol}, grid:{color:gridCol}}},
      plugins:{legend:{display:false}}}
  });
}
// The extra info Garmin adds to a linked cardio session (see mcp-garmin). Themed box.
function garminLine(l){
  const g=l.garmin; if(!g) return "";
  const bits=[];
  if(g.avg_hr!=null) bits.push("avg HR "+g.avg_hr);
  if(g.max_hr!=null) bits.push("max "+g.max_hr);
  if(g.cadence_spm!=null) bits.push("cadence "+g.cadence_spm+" spm");
  if(g.elevation_gain_m!=null) bits.push("+"+g.elevation_gain_m+" m");
  if(g.calories!=null) bits.push(g.calories+" kcal");
  if(g.moving_time) bits.push("moving "+g.moving_time);
  if(g.training_effect!=null) bits.push("TE "+g.training_effect);
  if(g.vo2max!=null) bits.push("VO₂ "+g.vo2max);
  const iv=intervalStructureText(l.garmin);
  return (bits.length||iv)? '<div class="garminbox">⌚ Garmin · '+bits.map(esc).join(" · ")
    + (iv?'<div style="margin-top:4px">'+esc(iv)+'</div>':"")+'</div>' : "";
}
// The reps you actually did, read off the watch's speed trace rather than typed.
// Garmin's laps can't show this - a treadmill auto-laps every 1km, so several
// 1-minute reps and their recoveries land inside a single lap - but the
// per-second trace can, because the belt holds a steady speed through a rep.
// Structure only: treadmill speed is wrist-estimated and reads high, so what you
// typed stays the record for speed. Derived by mcp-garmin (detect_intervals).
function intervalStructureText(g){
  const iv=g&&g.intervals; if(!iv||!iv.reps) return "";
  let s=iv.reps+" × "+fmtMmSs(iv.rep_sec_avg)+" hard";
  if(iv.recovery_sec_avg) s+=", "+fmtMmSs(iv.recovery_sec_avg)+" easy between";
  return "reps on the watch: "+s;
}
function garminStatus(l){
  if(l.garminActivityId) return ' · ⌚ Garmin';
  if(l.garminWanted) return ' · ⌚ awaiting run…';
  return "";
}
// Parse "m:ss" / "h:mm:ss" to seconds; blank/invalid -> null.
function parseClock(s){
  if(s==null) return null; s=String(s).trim(); if(!s) return null;
  const p=s.split(":").map(Number); if(p.some(isNaN)) return null;
  return p.reduce((t,n)=>t*60+n,0);
}
// One-line summary of a session's run for the collapsed History row: total
// distance, time, average pace, and avg HR from the linked Garmin data.
// A real running split has distance. Garmin logs rest/auto laps at 0 km, which
// aren't splits and skew pace/totals — drop those (but keep blank-distance rows
// from manual entry). Used by both the collapsed summary and the splits table.
function isSplitRow(r, di){ const d=parseFloat(r[di]); return isNaN(d) || d>0; }
// Distance · time · avg pace · ♥ HR for one run entry (0-distance laps skipped).
// An interval piece is cardio the watch records but that isn't a distance+time
// run - treadmill reps logged as speeds. The program marks those with garminRun
// (see isGarminCardio), but a *logged* entry never carries that flag, so resolve
// it back to the program definition by name - the same fallback loadTypeOf uses.
function isIntervalEntry(e){
  if(!e || isRunning(e)) return false;
  const def=programExerciseByName(e.name);
  return !!(def && def.garminRun===true);
}
// Fastest single split, as m:ss per km. Computed from each row's own distance
// and time rather than the Pace column, which is only filled in for rows the
// app or the importer got to. Partial last splits are fine - a half km in half
// the time is the same pace - but zero-distance rows would divide by zero.
function bestPaceFromEntry(e){
  if(!e) return "";
  const di=colIndex(e,/dist/i), ti=colIndex(e,/time/i);
  if(di<0||ti<0) return "";
  let best=null;
  (e.rows||[]).forEach(r=>{
    const km=parseFloat(r[di]), sec=parseClock(r[ti]);
    if(isNaN(km)||km<=0||sec==null||sec<=0) return;
    const pace=(sec/60)/km;
    if(best==null||pace<best) best=pace;
  });
  return best==null ? "" : fmtPace(best)+"/km";
}
// Hardest effort in an interval entry: the biggest number in its first column,
// which is the "hard" one (Hard speed (km/h) / Easy speed (km/h)). Reported as a
// pace, because the Zone 2 card beside it on Home reports one - a treadmill
// speed and a run pace are the same thing measured two ways, and comparing them
// shouldn't mean doing 60/x in your head. Only km/h converts (60/x is only right
// for that); the column's own label supplies the unit, and anything else - mph,
// a machine "level", no unit at all - falls back to the raw number as before.
function bestSpeedFromEntry(e){
  if(!e||!e.cols||!e.cols.length) return "";
  let best=null;
  (e.rows||[]).forEach(r=>{
    const v=parseFloat(r&&r[0]);
    if(isNaN(v)||v<=0) return;
    if(best==null||v>best) best=v;
  });
  if(best==null) return "";
  const unit=((String(e.cols[0]).match(/\(([^)]+)\)/)||[])[1]||"").trim();
  if(/^km\s*\/\s*h$/i.test(unit)) return fmtPace(60/best)+"/km";
  return best+(unit?" "+unit:"");
}
function runSummaryFromEntry(e, garmin){
  if(!e) return "";
  const di=colIndex(e,/dist/i), ti=colIndex(e,/time/i);
  let km=0, sec=0;
  (e.rows||[]).forEach(r=>{ const d=parseFloat(r[di]); if(isNaN(d)||d<=0) return;
    km+=d; const t=parseClock(r[ti]); if(t!=null) sec+=t; });
  const bits=[];
  if(km>0) bits.push((Math.round(km*100)/100)+" km");
  if(sec>0) bits.push(fmtMmSs(sec));
  if(km>0&&sec>0) bits.push(fmtPace((sec/60)/km)+"/km");
  const g=garmin||{}; if(g.avg_hr!=null) bits.push("♥ "+g.avg_hr);
  return bits.join(" · ");
}
function runSummary(l){
  const e=(l.entries||[]).find(x=>isRunning(x)); if(!e) return null;
  return runSummaryFromEntry(e, l.garmin) || null;
}
// "Last time you did this one" card, shown at the top of an OPTIONAL session's
// log form. A scheduled session comes round every week, so the per-exercise
// Last column is enough context; an optional one might be three weeks apart,
// and by then "what did I actually do?" isn't a number you remember. Deliberately
// a read-out and not a target - the whole point of an optional session is that
// there's nothing to beat.
function lastTimeHtml(sess, prev){
  if(!sess || String(sess.day||"").toLowerCase()!=="optional") return "";
  if(!prev){
    return '<div class="cardio-note">&#128197; <b>First time for '+esc(sess.name)+'.</b> Nothing to match - '
      + 'just do what you fancy and it\'ll be here for reference next time.</div>';
  }
  const bits=[];
  const rs=runSummary(prev);
  if(rs) bits.push(rs);
  const g=prev.garmin||{};
  if(g.max_hr!=null) bits.push("🧡 "+g.max_hr+" max");
  if(prev.volume) bits.push(prev.volume.toLocaleString()+" kg");
  if(prev.durationSec) bits.push("⏱ "+fmtDuration(prev.durationSec));
  if(prev.difficulty) bits.push("difficulty "+prev.difficulty+"/10");
  return '<div class="cardio-note">&#128197; <b>Last time</b> · '+esc(relTime(prev.date))+' ('+esc(prev.date)+')'
    + (bits.length?'<div style="margin-top:4px">'+bits.map(esc).join(' · ')+'</div>':'')
    + (prev.feedback?'<div class="ex-meta" style="margin-top:4px">📝 '+esc(prev.feedback)+'</div>':'')
    + '</div>';
}
// One entry's detail row. Runs render as a proper splits table (per-lap
// distance/time/pace/HR) with a totals line; everything else stays a compact
// dot-joined list.
function entryDetailHtml(e){
  if(isRunning(e) && (e.rows||[]).length){
    const cols=e.cols||[];
    const di=colIndex(e,/dist/i), ti=colIndex(e,/time/i), pi=colIndex(e,/pace/i), hi=colIndex(e,/hr/i);
    const splitRows=e.rows.filter(r=>isSplitRow(r, di)); // drop 0-distance rest laps
    if(!splitRows.length) return '<tr><td colspan="2"><b>'+esc(e.name)+(e.pr?' 🥇':'')+'</b></td></tr>';
    const head='<tr><th class="spl">#</th>'+cols.map(c=>'<th class="spl">'+esc(c)+'</th>').join("")+'</tr>';
    const body=splitRows.map((r,ri)=>'<tr><td class="spl">'+(ri+1)+'</td>'
      + cols.map((c,ci)=>'<td class="spl">'+esc(r[ci]!=null&&String(r[ci]).trim()!==""?String(r[ci]):"-")+'</td>').join("")+'</tr>').join("");
    let km=0, sec=0, hrSum=0, hrN=0;
    splitRows.forEach(r=>{ const d=parseFloat(r[di]); if(!isNaN(d)) km+=d;
      const t=parseClock(r[ti]); if(t!=null) sec+=t;
      if(hi>=0){ const h=parseFloat(r[hi]); if(!isNaN(h)){ hrSum+=h; hrN++; } } });
    const tot=cols.map((c,ci)=>{
      let v="";
      if(ci===di && km>0) v=Math.round(km*100)/100;
      else if(ci===ti && sec>0) v=fmtMmSs(sec);
      else if(ci===pi && km>0 && sec>0) v=fmtPace((sec/60)/km)+"/km";
      else if(ci===hi && hrN) v=Math.round(hrSum/hrN);
      return '<td class="spl">'+esc(String(v))+'</td>';
    }).join("");
    const totals=(km>0||sec>0)?'<tr class="tot"><td class="spl">Σ</td>'+tot+'</tr>':"";
    return '<tr><td colspan="2"><b>'+esc(e.name)+(e.pr?' 🥇':'')+'</b>'
      + '<div class="splits-wrap"><table class="splits">'+head+body+totals+'</table></div></td></tr>';
  }
  return '<tr><td><b>'+esc(e.name)+(e.pr?' 🥇':'')+'</b>'+(e.rpe!=null?' <span class="hint" style="margin:0">RPE '+esc(e.rpe)+'</span>':'')+'</td><td>'
    + e.rows.map((r,ri)=>{
        let s=fmtRow(e.cols||[], r);
        return (e.warmup&&e.warmup.indexOf(ri)>=0)?'<span class="wu-tag">'+s+' (w)</span>':s;
      }).join(" · ")+'</td></tr>';
}
// Your own notes on a logged session. These used to be write-once - the only
// place to type one was the log form, before saving - so remembering something
// afterwards had nowhere to go. Editable here instead, saved on blur like the
// Program tab's warm-up / cool-down notes. The read-out and the editor swap
// places; the read-out is always rendered (hidden when empty) so there's
// something to reveal after a note is added to a session that had none.
function histNoteHtml(l){
  const fb=l.feedback||"";
  return '<div class="fb" data-fbview="'+l.id+'"'+(fb?"":" hidden")+'>&#128221; '+esc(fb)+'</div>'
    + '<div class="notes-wrap" data-fbwrap="'+l.id+'" hidden>'
      + '<textarea class="notes" data-fbta="'+l.id+'" rows="2" placeholder="e.g. Right knee tight on squats. Felt strong today.">'+esc(fb)+'</textarea></div>'
    + '<div class="row" style="justify-content:flex-end;margin-top:7px">'
      + '<button class="mini" data-fbedit="'+l.id+'">&#128221; '+(fb?"Edit note":"Add a note")+'</button></div>';
}
function wireHistNotes(){
  const logById=id=>state.logs.filter(l=>String(l.id)===String(id))[0];
  const commit=ta=>{
    const log=logById(ta.dataset.fbta); if(!log) return false;
    const v=ta.value.trim();
    if(v===(log.feedback||"")) return false;
    if(v) log.feedback=v; else delete log.feedback;
    save(); return true;
  };
  document.querySelectorAll("[data-fbta]").forEach(ta=>{
    ta.addEventListener("input",()=>autoGrow(ta));
    ta.addEventListener("change",()=>{ if(commit(ta)) toast("Note saved"); });
  });
  document.querySelectorAll("[data-fbedit]").forEach(b=>b.onclick=()=>{
    const id=b.dataset.fbedit;
    const wrap=document.querySelector('[data-fbwrap="'+id+'"]');
    const view=document.querySelector('[data-fbview="'+id+'"]');
    const ta=wrap&&wrap.querySelector("textarea");
    if(!wrap||!ta||!view) return;
    if(wrap.hasAttribute("hidden")){
      wrap.removeAttribute("hidden"); view.setAttribute("hidden","");
      autoGrow(ta); ta.focus();
      b.textContent="✓ Done";
    } else {
      if(commit(ta)) toast("Note saved");
      wrap.setAttribute("hidden","");
      const fb=(logById(id)||{}).feedback||"";
      view.innerHTML="&#128221; "+esc(fb);
      if(fb) view.removeAttribute("hidden"); else view.setAttribute("hidden","");
      b.innerHTML="&#128221; "+(fb?"Edit note":"Add a note");
    }
  });
}
function drawHist(who){
  let logs=[...state.logs].sort((a,b)=> (a.date<b.date?1:a.date>b.date?-1:b.id-a.id));
  if(who!=="all") logs=logs.filter(l=>l.person===who);
  const pc=personSwatch;
  document.getElementById("histList").innerHTML = logs.map(l=>{
    const open = l.id===justSavedId;
    const rows=(l.entries||[]).map(entryDetailHtml).join("");
    const rs=runSummary(l);
    return '<div class="log-item"><div class="log-row"><div class="row-grow">'
      + '<h3>'+esc(l.sessionName)+' <span class="pill" data-sw="'+pc(l.person)+'">'+esc(l.person)+'</span></h3>'
      + '<div class="ex-meta">'+esc(l.date)+(rs?' · '+esc(rs):"")+(l.difficulty?' · difficulty '+l.difficulty+'/10':"")+(l.volume?' · '+l.volume.toLocaleString()+' kg':"")+(l.durationSec?' · ⏱ '+fmtDuration(l.durationSec):"")+garminStatus(l)+'</div></div>'
      + '<div class="row actions"><button class="mini" data-toggle="'+l.id+'">'+(open?"Hide":"View")+'</button>'
      + '<button class="mini" data-del="'+l.id+'" style="color:var(--bad)">Delete</button></div></div>'
      + '<div class="log-detail '+(open?"open":"")+'" id="d'+l.id+'"><table>'
      + (rows||'<tr><td class="ex-meta">No set data</td></tr>')+'</table>'
      + histNoteHtml(l)+garminLine(l)
      + hrZoneBarHtml((l.garmin||{}).hr_zone_secs)+'</div></div>';
  }).join("");
  justSavedId=null;
  wireHistNotes();
  document.querySelectorAll("[data-toggle]").forEach(b=>b.onclick=()=>{
    const d=document.getElementById("d"+b.dataset.toggle);
    d.classList.toggle("open"); b.textContent=d.classList.contains("open")?"Hide":"View";
  });
  document.querySelectorAll("[data-del]").forEach(b=>b.onclick=()=>{
    if(confirm("Delete this session?")){
      state.logs=state.logs.filter(l=>l.id!=b.dataset.del); save(); drawHist(who); toast("Deleted");
    }
  });
}

let chart=null;
// "82 kg" on its own is a puzzle for a pull-up - show the sum behind a
// bodyweight or assisted best. Empty for a normal loaded exercise.
function loadBreakdown(r){
  if(!r || !r.load || r.bw==null) return "";
  const pct=r.pct||100;
  const own=Math.round(r.bw*(pct/100)*10)/10;
  const part=pct<100;
  const you = part ? pct+"% of you = "+own : String(own);
  const typed=isNaN(r.typed)?0:r.typed;
  let txt;
  if(r.load==="assist") txt = typed>0 ? you+" &minus; "+typed+" assist" : (part?you:"your bodyweight, unassisted");
  else txt = typed>0 ? you+" + "+typed+" added" : (part?you:"your bodyweight");
  return '<div class="ex-meta">'+txt+'</div>';
}
// Progress holds two panes: Lifts (records + the exercise chart) and Body
// (goals, bodyweight, its trend). Body used to be its own bottom-bar tab; it
// moved in here so the fifth slot could go to Session, which had no tab at all
// and was only reachable via Home's "Log it". Stacked into one page it would
// have been a records table, a chart, goals, an entry form, a second chart and
// a list - two and a half phone screens before the bodyweight box you opened it
// for - so they're behind a toggle. Also keeps one Chart.js instance live at a
// time. Resets to Lifts on reload, like openSessions in the Program tab.
let progressPane="lifts";
function progressTabsHtml(){
  return '<div class="card pane-card"><div class="ptoggle pane-toggle">'
    + ['lifts','body'].map(k=>'<button type="button" data-pane="'+k+'"'
        + (progressPane===k?' class="active"':'')+'>'+(k==="lifts"?"🏋 Lifts":"⚖ Body")+'</button>').join("")
    + '</div></div>';
}
function wirePaneToggle(){
  document.querySelectorAll("[data-pane]").forEach(b=>b.onclick=()=>{
    if(progressPane===b.dataset.pane) return;
    progressPane=b.dataset.pane;
    renderProgress();
  });
}
function renderProgress(){
  if(progressPane==="body") return renderBody();
  const allEx=[...new Set(state.logs.flatMap(l=>(l.entries||[]).map(e=>e.name)))].sort();
  if(!allEx.length){
    document.getElementById("view").innerHTML=progressTabsHtml()
      +'<div class="card empty">Log a few sessions and your progress charts will appear here.</div>';
    wirePaneToggle();
    return;
  }
  const p=state.people[state.activePerson];
  const pc = personSwatch(p);
  const recs=personRecords(p);
  const recNames=Object.keys(recs).sort();
  let recTable;
  if(recNames.length){
    recTable='<div class="sets-wrap"><table class="rec"><thead><tr><th>Exercise</th><th>Best</th><th>Reps</th><th>e1RM</th><th>When</th></tr></thead><tbody>'
      + recNames.map(function(n){ const r=recs[n]; const e=epley(r.kg, r.reps);
          return '<tr><td>'+esc(n)+'</td><td><b>'+(Math.round(r.kg*10)/10)+' kg</b>'+loadBreakdown(r)+'</td><td>'+(r.reps!=null?r.reps:"–")+'</td><td>'+(isNaN(e)?"–":Math.round(e)+" kg")+'</td><td class="ex-meta">'+relTime(r.date)+'</td></tr>'; }).join("")
      + '</tbody></table></div>';
  } else {
    recTable='<div class="hint">No lifting bests for '+esc(p)+' yet.</div>';
  }
  document.getElementById("view").innerHTML=progressTabsHtml()+'<div class="card">'
    + '<div class="sec-title">🏅 Records - '+esc(p)+' <span class="pill" data-sw="'+pc+'">current bests</span></div>'
    + recTable + '</div>'
    + '<div class="card">'
    + '<div class="row" style="margin-bottom:12px">'
    + '<label class="fld grow" style="max-width:280px">Exercise chart<select id="progEx">'
    + allEx.map(n=>'<option>'+esc(n)+'</option>').join("")+'</select></label>'
    + '<label class="fld" style="width:150px">Metric<select id="progMetric"><option value="weight">Top-set weight</option><option value="e1rm">Est. 1RM</option></select></label></div>'
    + '<div class="hint" style="margin-bottom:10px">Per session, for both people. Warm-up sets are excluded.</div>'
    + '<div class="chart-box"><canvas id="progChart"></canvas></div></div>';
  wirePaneToggle();
  document.getElementById("progEx").onchange=drawChart;
  document.getElementById("progMetric").onchange=drawChart;
  drawChart();
}
function drawChart(){
  const name=document.getElementById("progEx").value;
  const metric=(document.getElementById("progMetric")||{}).value||"weight";
  const dark=document.documentElement.getAttribute("data-theme")==="dark";
  const series=state.people.map((p,i)=>{
    const pts=state.logs.filter(l=>l.person===p)
      .map(l=>{ const e=(l.entries||[]).find(x=>x.name===name); if(!e) return null;
        const wu=e.warmup||[]; const vals=[];
        e.rows.forEach((r,ri)=>{ if(wu.indexOf(ri)>=0) return; const w=setLoad(e, r[0], p, l.date); if(isNaN(w)) return;
          if(metric==="e1rm"){ const v=epley(w,parseInt(r[1],10)); if(!isNaN(v)) vals.push(v); } else vals.push(w); });
        if(!vals.length) return null; return {x:l.date,y:Math.round(Math.max.apply(null,vals)*10)/10}; })
      .filter(Boolean).sort((a,b)=>a.x<b.x?-1:1);
    return {label:p,data:pts,borderColor:swatchColor(state.colors[i],dark),
      backgroundColor:swatchColor(state.colors[i],dark),tension:.25,spanGaps:true};
  });
  if(chart) chart.destroy();
  const tickCol=dark?"#9aa3b2":"#697086";
  const gridCol=dark?"rgba(255,255,255,.09)":"rgba(20,30,55,.08)";
  chart=new Chart(document.getElementById("progChart"),{
    type:"line", data:{datasets:series},
    options:{responsive:true,maintainAspectRatio:false,parsing:false,
      scales:{x:{type:"category",labels:[...new Set(state.logs.map(l=>l.date))].sort(),
          ticks:{color:tickCol},grid:{color:gridCol}},
        y:{beginAtZero:false,title:{display:true,text:metric==="e1rm"?"Est. 1RM (kg)":"Top-set weight",color:tickCol},
          ticks:{color:tickCol},grid:{color:gridCol}}},
      plugins:{legend:{position:"top",labels:{color:tickCol}}}}
  });
}

function bwFor(person){
  return state.bodyweights.filter(b=>b.person===person)
    .slice().sort((a,b)=> a.date<b.date?-1: a.date>b.date?1:0);
}
function latestBw(person){ const a=bwFor(person); return a.length? a[a.length-1] : null; }
// Add or replace a person's bodyweight for a date; keeps weights[] (the
// "current" value shown in the header/settings) in sync with the newest entry.
function addBodyweight(person, date, kg){
  if(isNaN(kg)) return;
  const existing=state.bodyweights.find(b=>b.person===person && b.date===date);
  if(existing) existing.kg=kg; else state.bodyweights.push({person, date, kg});
  const pi=state.people.indexOf(person);
  if(pi>=0){ const lb=latestBw(person); if(lb) state.weights[pi]=String(lb.kg); }
}
// Tolerant CSV parse: split on comma/semicolon/tab, honouring simple quotes.
function parseCsv(text){
  return text.replace(/\r/g,"").split("\n").filter(l=>l.trim()!=="").map(line=>{
    const out=[]; let cur="", q=false;
    for(let i=0;i<line.length;i++){
      const c=line[i];
      if(q){ if(c==='"'){ if(line[i+1]==='"'){cur+='"';i++;} else q=false; } else cur+=c; }
      else if(c==='"') q=true;
      else if(c===","||c===";"||c==="\t"){ out.push(cur); cur=""; }
      else cur+=c;
    }
    out.push(cur);
    return out.map(s=>s.trim());
  });
}
function parseAnyDate(s){
  s=String(s).trim(); if(!s) return null;
  let m=s.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})/); // ISO-ish
  if(m) return m[1]+"-"+("0"+m[2]).slice(-2)+"-"+("0"+m[3]).slice(-2);
  m=s.match(/^(\d{1,2})[-/](\d{1,2})[-/](\d{4})/); // D/M/Y or M/D/Y — assume D/M/Y
  if(m){ let d=+m[1], mo=+m[2]; if(d>12){/*keep*/} else if(mo>12){ const t=d;d=mo;mo=t; }
    return m[3]+"-"+("0"+mo).slice(-2)+"-"+("0"+d).slice(-2); }
  const t=new Date(s); if(!isNaN(t)) return t.toISOString().slice(0,10);
  return null;
}
// Import a bodyweight CSV (e.g. from the 1byone Health app export). Auto-detects
// the date and weight columns from the header; converts lb→kg if the header says so.
function importBodyweightCsv(text, person){
  const rows=parseCsv(text);
  if(!rows.length) return {added:0, msg:"Empty file"};
  const header=rows[0].map(h=>h.toLowerCase());
  let di=header.findIndex(h=>/date|time|day/.test(h));
  let wi=header.findIndex(h=>/weight|mass|\bkg\b|\blb\b|lbs|pounds/.test(h));
  let start=1;
  if(di<0 || wi<0){ // no recognisable header — assume col0=date, col1=weight, no header
    di=0; wi=1; start=0;
  }
  const isLb=wi>=0 && /lb|pound/.test(header[wi]||"");
  let added=0;
  for(let r=start;r<rows.length;r++){
    const cells=rows[r]; if(!cells || cells.length<=Math.max(di,wi)) continue;
    const date=parseAnyDate(cells[di]);
    let kg=parseFloat(String(cells[wi]).replace(/[^\d.]/g,""));
    if(!date || isNaN(kg)) continue;
    if(isLb) kg=Math.round(kg*0.453592*10)/10;
    addBodyweight(person, date, kg); added++;
  }
  return {added, msg: added? added+" entries imported" : "No date+weight rows found"};
}

let bwChart=null;
function renderBody(){
  const p=state.people[state.activePerson];
  const hist=bwFor(p).slice().reverse(); // newest first for the list
  const latest=latestBw(p);
  const pc = personSwatch(p);
  const goal=(state.goals&&state.goals[state.activePerson])||"";
  // Body is the second pane of the Progress tab, so it carries the same toggle.
  // Reached directly (Home's ⚖ arrow), it sets progressPane itself first.
  let html=progressTabsHtml()
    + '<div class="card"><div class="sec-title">🎯 '+esc(possessive(p))+' goals</div>'
    + (goal ? '<div style="white-space:pre-wrap">'+esc(goal)+'</div>'
            : '<div class="hint" style="margin:0">No goals set yet - add them via the gear menu.</div>')
    + '</div>';
  html+='<div class="card">'
    + '<div class="flex-between" style="margin-bottom:10px"><div>'
    + '<h3>'+esc(p)+' <span class="pill" data-sw="'+pc+'">bodyweight</span></h3>'
    + '<div class="ex-meta">'+(latest? latest.kg+' kg · '+relTime(latest.date) : 'No entries yet')+'</div></div></div>'
    + '<div class="row" style="align-items:flex-end;gap:8px">'
    + '<label class="fld"><span>Weight (kg)</span><input id="bwKg" type="number" inputmode="decimal" step="0.1" placeholder="e.g. 76" style="width:120px"></label>'
    + '<label class="fld"><span>Date</span><input id="bwDate" type="date" value="'+trainingDateStr()+'" style="width:150px"></label>'
    + '<button class="btn btn-primary" id="bwAdd">Add</button>'
    + '<button class="mini" id="bwImport" style="margin-left:auto">⬆ Import from scale (CSV)</button>'
    + '<input id="bwFile" type="file" accept=".csv,text/csv,text/plain" style="display:none">'
    + '</div>'
    + '<div class="hint" style="margin-top:6px">Import a CSV exported from your scale app (e.g. 1byone Health). Date + weight columns are detected automatically.</div>'
    + '</div>';
  if(hist.length){
    html+='<div class="card"><div class="sec-title">Trend</div><div class="chart-box"><canvas id="bwChart"></canvas></div></div>';
    html+='<div class="card"><div class="sec-title">History - '+hist.length+' entr'+(hist.length===1?"y":"ies")+'</div><div id="bwList"></div></div>';
  } else {
    html+='<div class="card empty">No bodyweight logged for '+esc(p)+' yet.<br>Add one above, or import from your scale app.</div>';
  }
  document.getElementById("view").innerHTML=html;
  wirePaneToggle();

  document.getElementById("bwAdd").onclick=()=>{
    const kg=parseFloat(document.getElementById("bwKg").value);
    const date=document.getElementById("bwDate").value||todayStr();
    if(isNaN(kg)){ toast("Enter a weight"); return; }
    addBodyweight(p, date, kg); save(); renderPeople(); renderBody(); toast("Saved");
  };
  document.getElementById("bwImport").onclick=()=>document.getElementById("bwFile").click();
  document.getElementById("bwFile").onchange=e=>{
    const f=e.target.files[0]; if(!f) return;
    const rd=new FileReader();
    rd.onload=()=>{ const res=importBodyweightCsv(rd.result, p); if(res.added){ save(); renderPeople(); } renderBody(); toast(res.msg); };
    rd.readAsText(f);
  };
  if(hist.length){
    const list=document.getElementById("bwList");
    list.innerHTML=hist.map(b=>'<div class="log-row" style="padding:4px 0;border-bottom:1px solid var(--line)">'
      + '<div><b>'+b.kg+' kg</b> <span class="ex-meta">'+esc(b.date)+' · '+relTime(b.date)+'</span></div>'
      + '<button class="mini" data-bwdel="'+esc(b.person)+'|'+esc(b.date)+'" style="color:var(--bad)">Delete</button></div>').join("");
    list.querySelectorAll("[data-bwdel]").forEach(btn=>btn.onclick=()=>{
      const a=btn.dataset.bwdel.split("|");
      state.bodyweights=state.bodyweights.filter(b=>!(b.person===a[0] && b.date===a[1]));
      const pi=state.people.indexOf(p); if(pi>=0){ const lb=latestBw(p); state.weights[pi]=lb?String(lb.kg):""; }
      save(); renderPeople(); renderBody(); toast("Deleted");
    });
    drawBwChart(p);
  }
}
function drawBwChart(person){
  const pts=bwFor(person).map(b=>({x:b.date, y:b.kg}));
  const i=state.people.indexOf(person);
  if(bwChart) bwChart.destroy();
  const dark=document.documentElement.getAttribute("data-theme")==="dark";
  const col=swatchColor(state.colors[i],dark);
  const tickCol=dark?"#9aa3b2":"#697086", gridCol=dark?"rgba(255,255,255,.09)":"rgba(20,30,55,.08)";
  bwChart=new Chart(document.getElementById("bwChart"),{
    type:"line", data:{datasets:[{label:person+" (kg)", data:pts, borderColor:col, backgroundColor:col, tension:.25, spanGaps:true}]},
    options:{responsive:true, maintainAspectRatio:false, parsing:false,
      scales:{x:{type:"category", labels:[...new Set(bwFor(person).map(b=>b.date))].sort(), ticks:{color:tickCol}, grid:{color:gridCol}},
        y:{beginAtZero:false, title:{display:true, text:"kg", color:tickCol}, ticks:{color:tickCol}, grid:{color:gridCol}}},
      plugins:{legend:{position:"top", labels:{color:tickCol}}}}
  });
}

// "sessionKey:index" refs currently ticked for grouping - module-level so it
// survives the re-renders triggered by ticking each checkbox; cleared once a
// group is actually made, or implicitly stale (harmless) if you leave the tab.
let selectedExRefs=new Set();
// Which Program sessions are expanded. Starts empty - everything collapsed - so
// the tab opens as a short index of the week. In memory rather than saved, so
// it survives the tab's own re-renders and a trip to another tab, and resets to
// all-collapsed next time the app is opened.
let openSessions=new Set();
function exRowHtml(k, ei, ex){
  const ref=k+':'+ei;
  return '<div class="ex"><div class="ex-head"><div class="row row-grow" style="gap:6px;align-items:baseline;flex-wrap:nowrap">'
    + '<input type="checkbox" data-selex="'+ref+'" style="width:auto;flex:none" title="Select for grouping"'+(selectedExRefs.has(ref)?' checked':'')+'>'
    + '<div style="min-width:0"><div class="ex-name">'+esc(ex.name)+'</div>'
    + '<div class="ex-meta">'+esc(ex.target)+(ex.warmup?' · warm-up: '+esc(ex.warmup):"")+(ex.notes?' · 🔧 setup':"")+'</div></div></div>'
    + '<div class="row actions"><button class="mini" data-editex="'+ref+'">Edit</button>'
    + '<button class="mini ico" data-upex="'+ref+'" title="Move up" aria-label="Move up">&uarr;</button>'
    + '<button class="mini ico" data-downex="'+ref+'" title="Move down" aria-label="Move down">&darr;</button>'
    + '<button class="mini ico" data-delex="'+ref+'" style="color:var(--bad)" title="Remove" aria-label="Remove">&times;</button>'
    + '</div></div></div>';
}
// Per-session warm-up/mobility and cool-down notes, edited in the Program tab
// and read on the Log tab (see renderLog). Free text on purpose - it's "3 min
// cross-trainer then shoulder mobility", not something to model as exercises.
// Collapsed unless the session already has one, matching the 🔧 settings rule:
// what exists is on screen, what doesn't stays out of the way.
// .notes textareas are `overflow:hidden`, so anything past the visible rows was
// invisible while typing it. Grow to fit instead. No-ops while hidden
// (scrollHeight is 0) - call it again when the textarea is revealed.
function autoGrow(ta){
  if(!ta || !ta.scrollHeight) return;
  ta.style.height="auto";
  // scrollHeight is content+padding; under border-box the borders need adding
  // back or the last line sits a couple of pixels under the edge.
  ta.style.height=(ta.scrollHeight + (ta.offsetHeight-ta.clientHeight))+"px";
}
function sessNotesHtml(k, s){
  const wu=s.warmupNote||"", cd=s.cooldownNote||"";
  const has=!!(wu||cd);
  return '<div class="sessnotes" data-sessnotes-wrap="'+esc(k)+'"'+(has?"":" hidden")+'>'
    + '<label class="fld" style="margin-bottom:8px">&#128293; Warm-up / mobility'
      + '<textarea class="notes" data-sessnote="warmupNote" data-sesskey="'+esc(k)+'" rows="2" placeholder="e.g. 3 min cross-trainer, then shoulder mobility">'+esc(wu)+'</textarea></label>'
    + '<label class="fld">&#129482; Cool-down'
      + '<textarea class="notes" data-sessnote="cooldownNote" data-sesskey="'+esc(k)+'" rows="2" placeholder="e.g. 5 min easy bike, hamstring + hip flexor stretches">'+esc(cd)+'</textarea></label>'
    + '</div>';
}
function renderEdit(){
  let html='<div class="card"><div class="hint">Tap a session to open it - rename exercises, change targets, add warm-up notes, note a session warm-up / cool-down, add or remove movements. Changes apply to future logging; past history is untouched. Tick 2+ exercises in the same session to group them as a superset/circuit.</div>'
    + '<div class="row actions" style="margin-top:10px"><button class="mini" id="addSessionBtn">&#10133; Add session</button>'
    + '<button class="mini" id="importSessionBtn">&#128229; Import shared session</button></div></div>';
  if(!orderedKeys().length){
    html+='<div class="card empty">No sessions yet.<br>Tap <b>+ Add session</b> above to create your first workout day.</div>';
  }
  orderedKeys().forEach(k=>{
    const s=state.program.sessions[k];
    const selCount=s.exercises.filter((ex,ei)=>selectedExRefs.has(k+':'+ei)).length;
    // Collapsed by default so the tab is a short scannable index of the week;
    // openSessions remembers what you opened across re-renders (editing an
    // exercise re-renders the whole tab and would otherwise shut the session
    // you're working in) and resets on reload.
    const open=openSessions.has(k);
    const n=s.exercises.length;
    html+='<div class="card sess'+(open?' open':'')+'">'
      + '<button type="button" class="sess-head" data-sesstoggle="'+esc(k)+'" aria-expanded="'+(open?"true":"false")+'">'
        + '<span class="sess-caret">&#9656;</span>'
        + '<span class="sess-title"><span class="sess-name">'+esc(s.name)+'</span>'
          + '<span class="ex-meta">'+esc(s.day)+' &middot; '+n+' exercise'+(n===1?"":"s")+'</span></span>'
      + '</button>';
    if(open){
      // One right-aligned row of session actions. The warm-up/cool-down toggle
      // used to sit on its own left-aligned row underneath, which put a
      // left/right zigzag between the session actions above it and the
      // per-exercise actions below.
      html+='<div class="row actions" style="margin:2px 0 10px">'
        + (selCount>=2?'<button class="mini" data-group="'+k+'">&#8646; Group as superset ('+selCount+')</button>':'')
        + '<button class="mini" data-sessnotes="'+esc(k)+'" aria-expanded="'+((s.warmupNote||s.cooldownNote)?"true":"false")+'">&#128293; Warm-up / &#129482; cool-down</button>'
        + '<button class="mini" data-shareex="'+k+'">&#128279; Share</button>'
        + '<button class="mini" data-addex="'+k+'">&#10133; Exercise</button></div>'
        + sessNotesHtml(k, s);
      exerciseBlocks(s.exercises).forEach(block=>{
        const rows=block.eis.map(ei=>exRowHtml(k,ei,s.exercises[ei])).join("");
        html += block.type==="group"
          ? '<div class="superset"><div class="superset-label">&#8646; Superset<button class="mini" data-ungroup="'+k+':'+block.groupId+'">Ungroup</button></div>'+rows+'</div>'
          : rows;
      });
    }
    html+='</div>';
  });
  document.getElementById("view").innerHTML=html;
  document.querySelectorAll("[data-sesstoggle]").forEach(b=>b.onclick=()=>{
    const k=b.dataset.sesstoggle;
    if(openSessions.has(k)) openSessions.delete(k); else openSessions.add(k);
    renderEdit();
  });
  document.querySelectorAll("[data-addex]").forEach(b=>b.onclick=()=>openExDlg(b.dataset.addex,null));
  document.querySelectorAll("[data-editex]").forEach(b=>b.onclick=()=>{ const a=b.dataset.editex.split(":"); openExDlg(a[0],+a[1]); });
  document.querySelectorAll("[data-delex]").forEach(b=>b.onclick=()=>{
    const a=b.dataset.delex.split(":");
    if(confirm("Remove this exercise from the program?")){
      state.program.sessions[a[0]].exercises.splice(+a[1],1);
      cleanupSoloGroups(a[0]);
      saveProgram(); renderEdit(); toast("Removed");
    }
  });
  document.querySelectorAll("[data-upex]").forEach(b=>b.onclick=()=>move(b.dataset.upex,-1));
  document.querySelectorAll("[data-downex]").forEach(b=>b.onclick=()=>move(b.dataset.downex,1));
  document.querySelectorAll("[data-shareex]").forEach(b=>b.onclick=()=>shareSession(b.dataset.shareex));
  document.querySelectorAll("[data-selex]").forEach(cb=>cb.onchange=()=>{
    if(cb.checked) selectedExRefs.add(cb.dataset.selex); else selectedExRefs.delete(cb.dataset.selex);
    renderEdit();
  });
  document.querySelectorAll("[data-sessnotes]").forEach(b=>b.onclick=()=>{
    const wrap=document.querySelector('[data-sessnotes-wrap="'+b.dataset.sessnotes+'"]');
    if(!wrap) return;
    const opening=wrap.hasAttribute("hidden");
    if(opening){
      wrap.removeAttribute("hidden");
      wrap.querySelectorAll("textarea").forEach(autoGrow);
    } else wrap.setAttribute("hidden","");
    b.setAttribute("aria-expanded", opening?"true":"false");
  });
  // Saved on blur rather than per keystroke, same as the exercise 🔧 settings.
  document.querySelectorAll("[data-sessnote]").forEach(ta=>{
    autoGrow(ta);
    ta.addEventListener("input", ()=>autoGrow(ta));
  });
  document.querySelectorAll("[data-sessnote]").forEach(ta=>ta.addEventListener("change",()=>{
    const sess=state.program.sessions[ta.dataset.sesskey]; if(!sess) return;
    const field=ta.dataset.sessnote, v=ta.value.trim();
    if(v===(sess[field]||"")) return;
    if(v) sess[field]=v; else delete sess[field];
    saveProgram();
    toast(field==="warmupNote" ? "Warm-up note saved" : "Cool-down note saved");
  }));
  document.querySelectorAll("[data-group]").forEach(b=>b.onclick=()=>groupSelected(b.dataset.group));
  document.querySelectorAll("[data-ungroup]").forEach(b=>b.onclick=()=>{
    const a=b.dataset.ungroup.split(":");
    ungroupExercises(a[0], a.slice(1).join(":"));
  });
  document.getElementById("importSessionBtn").onclick=()=>importSessionDlg.showModal();
  document.getElementById("addSessionBtn").onclick=()=>{
    document.getElementById("sessName").value="";
    document.getElementById("sessDay").value="Monday";
    sessionDlg.showModal();
  };
}
// A "group" of one exercise isn't a group - clear a groupId once only one
// member of it is left (e.g. after deleting the exercise that was its pair).
function cleanupSoloGroups(sessionKey){
  const arr=state.program.sessions[sessionKey].exercises;
  const counts={};
  arr.forEach(ex=>{ if(ex.groupId) counts[ex.groupId]=(counts[ex.groupId]||0)+1; });
  arr.forEach(ex=>{ if(ex.groupId && counts[ex.groupId]<2) delete ex.groupId; });
}
function groupSelected(sessionKey){
  const refs=Array.from(selectedExRefs)
    .filter(r=>r.startsWith(sessionKey+":"))
    .map(r=>+r.split(":")[1]).sort((a,b)=>a-b);
  if(refs.length<2) return;
  const arr=state.program.sessions[sessionKey].exercises;
  const gid="grp-"+Date.now();
  const selectedSet=new Set(refs);
  const members=refs.map(i=>arr[i]);
  members.forEach(ex=>{ ex.groupId=gid; });
  const before=arr.slice(0, refs[0]);
  const after=arr.filter((ex,i)=> i>refs[0] && !selectedSet.has(i));
  state.program.sessions[sessionKey].exercises=before.concat(members, after);
  selectedExRefs.clear();
  saveProgram(); renderEdit(); toast("Grouped as superset");
}
function ungroupExercises(sessionKey, groupId){
  state.program.sessions[sessionKey].exercises.forEach(ex=>{ if(ex.groupId===groupId) delete ex.groupId; });
  saveProgram(); renderEdit(); toast("Ungrouped");
}
// Moves the contiguous block containing exercise `ref` (its whole superset
// group if it's grouped, otherwise just itself) up/down past the adjacent
// block, keeping grouped members adjacent - see exerciseBlocks().
function move(ref,dir){
  const a=ref.split(":"); const sessionKey=a[0];
  const arr=state.program.sessions[sessionKey].exercises;
  const i=+a[1];
  const gid=arr[i].groupId;
  let lo=i, hi=i;
  if(gid){
    while(lo>0 && arr[lo-1].groupId===gid) lo--;
    while(hi<arr.length-1 && arr[hi+1].groupId===gid) hi++;
  }
  let oLo, oHi;
  if(dir<0){
    if(lo===0) return;
    oHi=lo-1; oLo=oHi;
    const ogid=arr[oHi].groupId;
    if(ogid){ while(oLo>0 && arr[oLo-1].groupId===ogid) oLo--; }
  } else {
    if(hi===arr.length-1) return;
    oLo=hi+1; oHi=oLo;
    const ogid=arr[oLo].groupId;
    if(ogid){ while(oHi<arr.length-1 && arr[oHi+1].groupId===ogid) oHi++; }
  }
  const thisBlock=arr.slice(lo,hi+1), otherBlock=arr.slice(oLo,oHi+1);
  const start=Math.min(lo,oLo);
  const newOrder = dir<0 ? thisBlock.concat(otherBlock) : otherBlock.concat(thisBlock);
  arr.splice(start, thisBlock.length+otherBlock.length, ...newOrder);
  saveProgram(); renderEdit();
}

// Common exercise names, so a brand-new account (no program, no logs yet) has
// a real list to pick from instead of a dropdown that starts completely empty
// and only grows once you've already typed something in yourself.
const COMMON_EXERCISES = [
  "Bench press","Incline bench press","Dumbbell bench press","Incline dumbbell press",
  "Chest fly","Cable crossover","Push-up","Dips",
  "Deadlift","Romanian deadlift","Pull-up","Chin-up","Lat pulldown","Barbell row",
  "Dumbbell row","Seated cable row","Face pull",
  "Squat","Front squat","Leg press","Leg extension","Leg curl","Lunge","Calf raise",
  "Hip thrust","Hip abduction","Hip adduction",
  "Overhead press","Dumbbell shoulder press","Lateral raise","Rear delt fly","Upright row",
  "Bicep curl","Hammer curl","Tricep pushdown","Tricep extension","Skull crusher",
  "Close-grip bench press",
  "Plank","Crunch","Hanging leg raise","Russian twist","Sit-up",
  "Running","Cycling","Rowing machine","Treadmill intervals","Elliptical"
];
let exDlgCtx=null;
const exDlg=document.getElementById("exDlg");
// Unique exercise names to offer as pick-from-list suggestions: common ones
// plus anything seen in the program or logged history (so the Add/Edit dialog
// avoids the spelling variants that fragment history for the same movement).
function exerciseLibrary(){
  const set={};
  COMMON_EXERCISES.forEach(n=>{ set[n]=true; });
  Object.keys(state.program.sessions).forEach(k=>{
    state.program.sessions[k].exercises.forEach(e=>{ if(e.name) set[e.name]=true; });
  });
  state.logs.forEach(l=>(l.entries||[]).forEach(e=>{ if(e.name) set[e.name]=true; }));
  return Object.keys(set).sort((a,b)=>a.toLowerCase()<b.toLowerCase()?-1:1);
}
// todayOnly: the same dialog, but the result goes into today's log form instead
// of the program (see the exSave handler).
function openExDlg(sessionKey,ei,todayOnly){
  exDlgCtx={sessionKey,ei,todayOnly:!!todayOnly};
  const editing = ei!=null;
  const ex = editing? state.program.sessions[sessionKey].exercises[ei]
    : {name:"",warmup:"",target:"3x8-12",cols:["Weight (kg)","Reps"],sets:3};
  document.getElementById("exNameList").innerHTML =
    exerciseLibrary().map(n=>'<option value="'+esc(n)+'"></option>').join("");
  document.getElementById("exDlgTitle").textContent =
    todayOnly ? "Add an exercise for today" : (editing?"Edit exercise":"Add exercise");
  const todayHint=document.getElementById("exTodayHint");
  if(todayHint) todayHint.hidden=!todayOnly;
  document.getElementById("exSave").textContent = todayOnly ? "Add for today" : "Save exercise";
  document.getElementById("exName").value=ex.name;
  document.getElementById("exWarmup").value=ex.warmup||"";
  document.getElementById("exNotes").value=ex.notes||"";
  document.getElementById("exTarget").value=ex.target||"";
  document.getElementById("exSets").value=ex.sets||3;
  document.getElementById("exCol0").value=ex.cols[0];
  document.getElementById("exCol1").value=ex.cols[1];
  document.getElementById("exCol2").value=ex.cols[2]||"";
  document.getElementById("exGarmin").checked = ex.garminRun===true;
  document.getElementById("exLoad").value = ex.load || "";
  document.getElementById("exBwPct").value = ex.bwPct || 100;
  syncLoadFields();
  exMusclesTouched = false;
  renderMuscleTags(document.getElementById("exMuscles"),
    (ex.muscles&&ex.muscles.length) ? ex.muscles : classifyMuscles(ex.name));
  exDlg.showModal();
}
// Tracks whether the user has manually touched the muscle pills for the
// exercise currently open in the dialog, so re-guessing on name changes
// doesn't clobber a deliberate choice.
let exMusclesTouched = false;
document.getElementById("exMuscles").onclick=e=>{
  const b=e.target.closest("button"); if(!b) return;
  exMusclesTouched = true;
  b.classList.toggle("sel");
};
document.getElementById("exName").oninput=()=>{
  if(exMusclesTouched) return;
  renderMuscleTags(document.getElementById("exMuscles"),
    classifyMuscles(document.getElementById("exName").value));
};
// The % row only makes sense for a bodyweight movement (an assisted one is
// always all of you, minus the help), and the first column gets named for what
// the number means - "Added/Assist (kg)" was the ambiguity that started this.
function syncLoadFields(){
  document.getElementById("exBwPctRow").hidden = document.getElementById("exLoad").value!=="bw";
}
// Only on a deliberate change, never on open - re-titling someone's column just
// because they looked at the exercise would be rude.
document.getElementById("exLoad").onchange=()=>{
  syncLoadFields();
  const load=document.getElementById("exLoad").value;
  const col0=document.getElementById("exCol0");
  const generic=/^(weight \(kg\)|added\/assist \(kg\)|added \(kg\)|assist \(kg\)|)$/i.test(col0.value.trim());
  if(!generic) return; // a label someone wrote themselves is left alone
  col0.value = load==="bw" ? "Added (kg)" : load==="assist" ? "Assist (kg)" : "Weight (kg)";
};
document.getElementById("exCancel").onclick=()=>exDlg.close();
document.getElementById("exPresetLift").onclick=()=>{
  document.getElementById("exCol0").value="Weight (kg)";
  document.getElementById("exCol1").value="Reps";
  document.getElementById("exCol2").value="";
};
document.getElementById("exPresetRun").onclick=()=>{
  document.getElementById("exCol0").value="Distance (km)";
  document.getElementById("exCol1").value="Time (mm:ss)";
  document.getElementById("exCol2").value="Pace";
};
document.getElementById("exSave").onclick=()=>{
  const name=document.getElementById("exName").value.trim();
  if(!name){ toast("Name required"); return; }
  const cols=[document.getElementById("exCol0").value.trim()||"Weight (kg)",
              document.getElementById("exCol1").value.trim()||"Reps"];
  const c2=document.getElementById("exCol2").value.trim();
  if(c2) cols.push(c2);
  const ex={ name, warmup:document.getElementById("exWarmup").value.trim(),
    notes:document.getElementById("exNotes").value.trim(),
    target:document.getElementById("exTarget").value.trim()||"-",
    sets:Math.max(1,Math.min(12,+document.getElementById("exSets").value||3)),
    cols, muscles:readMuscleTags(document.getElementById("exMuscles")) };
  if(document.getElementById("exGarmin").checked) ex.garminRun=true;
  const load=document.getElementById("exLoad").value;
  if(load){
    ex.load=load;
    if(load==="bw"){
      const pct=Math.max(1, Math.min(100, +document.getElementById("exBwPct").value||100));
      if(pct!==100) ex.bwPct=pct;
    }
  }
  // Today only: straight into the log form's extras, never into the program.
  if(exDlgCtx.todayOnly){
    ex.todayOnly=true;
    const key=draftKey();
    if(!formExtras[key]) formExtras[key]=[];
    formExtras[key].push(ex);
    saveDrafts(); exDlg.close(); renderView();
    toast("Added "+ex.name+" for today");
    return;
  }
  const arr=state.program.sessions[exDlgCtx.sessionKey].exercises;
  if(exDlgCtx.ei!=null){
    // Editing rebuilds the exercise object from scratch - carry its superset
    // membership over, or the edited exercise silently drops out of the group
    // (leaving its old groupmates rendered as a solo "superset" of one).
    const old=arr[exDlgCtx.ei];
    if(old && old.groupId) ex.groupId=old.groupId;
    arr[exDlgCtx.ei]=ex;
  } else arr.push(ex);
  cleanupSoloGroups(exDlgCtx.sessionKey);
  saveProgram(); exDlg.close(); renderEdit(); toast("Saved");
};

const setDlg=document.getElementById("settingsDlg");
document.getElementById("settingsBtn").onclick=()=>{
  // Settings are person-specific: edit the selected person; switch person to edit the other.
  const i=state.activePerson;
  document.getElementById("setWho").textContent="· "+(state.people[i]||"");
  document.getElementById("pName").value=state.people[i]||"";
  const otherColor = state.people[1-i] ? state.colors[1-i] : null;
  renderSwatchPicker(document.getElementById("pColor"), (state.colors&&state.colors[i])||"navy", otherColor);
  wireSwatchPicker(document.getElementById("pColor"));
  document.getElementById("pWeight").value=(state.weights&&state.weights[i])||"";
  document.getElementById("pGoals").value=(state.goals&&state.goals[i])||"";
  document.getElementById("pWeightLab").childNodes[0].nodeValue=possessive(state.people[i])+" bodyweight (kg)";
  document.getElementById("pGoalsLab").childNodes[0].nodeValue=possessive(state.people[i])+" goals";
  const sc=loadSync();
  document.getElementById("ghRepo").value=sc.repo||"";
  document.getElementById("ghPath").value=sc.path||"";
  document.getElementById("ghToken").value=sc.token||"";
  setSyncStatus(sc.repo&&sc.token ? "Configured for "+sc.repo+(sc.sha?" · last synced OK":"") : "Not configured.");
  document.getElementById("sugText").value="";
  renderSuggestions();
  renderNotSetupList();
  showAppVersion();
  setDlg.showModal();
  // Only once the dialog is actually on screen - autoGrow reads scrollHeight,
  // which is 0 while it's still hidden.
  autoGrow(document.getElementById("pGoals"));
};
// Goals are a list, not a sentence ("squat 100kg, sub-25 5k, stay injury-free"),
// but the box was a fixed two rows with the overflow hidden, so anything past
// the second line scrolled out of sight as you typed it. Grow to fit, same as
// the warm-up/cool-down and machine-settings notes. The inline min-height stays
// as the floor so an empty box doesn't collapse to one line.
document.getElementById("pGoals").addEventListener("input", function(){ autoGrow(this); });
// What this device/account doesn't have set up yet, vs. what Daniel & Cerys
// already have running. None of it is code-gated per account - it's all
// laptop-side setup (MCP servers, tokens) any account can get the same way.
function renderNotSetupList(){
  const el=document.getElementById("notSetupList"); if(!el) return;
  const sync=loadSync();
  const syncOk=!!(sync.repo && sync.token);
  el.innerHTML =
      '<p style="margin:0 0 8px">'+(syncOk
        ?'<b>Cloud sync</b> - configured on this device.'
        :'<b>Cloud sync</b> - not set up on this device. Needs a private GitHub repo + access token (above).')+'</p>'
    + '<p style="margin:0 0 8px"><b>Garmin auto-import</b> - not set up. Needs its own MCP server, a Garmin login, and a scheduled sync job on a laptop running Claude Code (see mcp-garmin/README.md).</p>'
    + '<p style="margin:0 0 8px"><b>AI coaching</b> - not set up. Needs the coaching MCP server, plus someone running a coaching chat for you (see docs/coaching-prompt.md).</p>'
    + '<div class="hint" style="margin:0">This device supports up to <b>2 accounts</b>. A third person needs their own separate device/install.</div>';
}
function renderSuggestions(){
  const list=document.getElementById("sugList"); if(!list) return;
  const open=(state.suggestions||[]).filter(s=>s&&s.status!=="done").slice().reverse();
  list.innerHTML = open.length
    ? '<div class="hint" style="margin:0 0 4px">'+open.length+' pending - synced for the dev/coach chat to action</div>'
      + open.map(s=>'<div class="log-row" style="padding:3px 0;border-bottom:1px solid var(--line);gap:8px">'
        + '<div style="font-size:13px"><b class="pill" data-sw="'+personSwatch(s.person)+'">'+esc(s.person||"?")+'</b> '+esc(s.text)+'</div>'
        + '<button class="mini" data-sugdel="'+s.id+'" title="Mark as done" style="color:var(--good)">&#10003;</button></div>').join("")
    : '<div class="hint" style="margin:0">No suggestions yet.</div>';
  list.querySelectorAll("[data-sugdel]").forEach(b=>b.onclick=()=>{
    // Mark done rather than deleting. A deleted row was resurrected by the very
    // next sync — mergeInData unions in any remote suggestion missing locally —
    // so dismissals never stuck. A local "done" is the tombstone: it hides the
    // row, blocks the re-add, and is re-asserted on every push, so it stays
    // cleared even if another device pushed an older "open" copy.
    const s=(state.suggestions||[]).find(x=>String(x.id)===b.dataset.sugdel);
    if(s){ s.status="done"; s.doneAt=new Date().toISOString(); }
    save(); renderSuggestions(); autoSync();
  });
}
document.getElementById("sugSend").onclick=()=>{
  const t=document.getElementById("sugText").value.trim();
  if(!t){ toast("Type a suggestion first"); return; }
  if(!Array.isArray(state.suggestions)) state.suggestions=[];
  state.suggestions.push({id:Date.now(), person:state.people[state.activePerson], date:todayStr(), text:t, status:"open"});
  save(); document.getElementById("sugText").value=""; renderSuggestions(); autoSync(); toast("Suggestion added");
};
// Auto-save the selected person's name / bodyweight / goals whenever the
// dialog closes (X, Done, Esc or backdrop) — no explicit Save button.
// Set right before a programmatic setDlg.close() that shouldn't trigger the
// normal auto-save-on-close (e.g. deleteAccount(), which already made its own
// change and would otherwise have the stale form fields overwrite it).
let skipSettingsSave=false;
function saveSettingsPerson(){
  if(skipSettingsSave){ skipSettingsSave=false; return; }
  // Preserve any in-progress log entry: closing settings re-renders the view, and
  // without capturing first the half-filled form was wiped (“going into settings
  // then back to log clears the log”).
  captureDraft();
  const i=state.activePerson;
  if(!Array.isArray(state.weights)) state.weights=["",""];
  if(!Array.isArray(state.goals)) state.goals=["",""];
  if(!Array.isArray(state.colors)) state.colors=["",""];
  const nm=(document.getElementById("pName").value||"").trim();
  if(nm && nm!==state.people[i]){
    // Renaming an existing account orphans its history (data is keyed by
    // name) - warn, same as the Delete-account confirm. A first-time name
    // (state.people[i] currently empty) needs no warning - nothing to orphan.
    const wasNamed=!!state.people[i];
    if(!wasNamed || confirm("Rename "+state.people[i]+" to \""+nm+"\"? Future logs save under the new name - history logged under \""+state.people[i]+"\" stays saved but won't show as this account's anymore unless you rename back to it exactly."))
      state.people[i]=nm;
  }
  const prevWeight=(state.weights[i]||"").trim();
  state.colors[i]=readSwatchPicker(document.getElementById("pColor"));
  state.weights[i]=(document.getElementById("pWeight").value||"").trim();
  state.goals[i]=(document.getElementById("pGoals").value||"").trim();
  // Only record a bodyweight when the number was actually edited. This used to run on
  // every settings close, so merely opening Settings on a new day stamped that day with
  // the unchanged weight and the trend chart gained a flat point daily. Weigh-ins should
  // come from a deliberate entry - here, the Body tab, or a scale import.
  const kg=parseFloat(state.weights[i]);
  if(!isNaN(kg) && state.weights[i]!==prevWeight) addBodyweight(state.people[i], todayStr(), kg);
  save(); renderPeople(); renderView();
}
setDlg.addEventListener("close", saveSettingsPerson);
document.getElementById("settingsClose").onclick=()=>setDlg.close();
document.getElementById("settingsClose2").onclick=()=>setDlg.close();
document.getElementById("guideBtn").onclick=()=>{ setDlg.close(); switchTab("help"); };
document.getElementById("ghSaveCfg").onclick=()=>{
  const cfg=loadSync();
  cfg.repo=document.getElementById("ghRepo").value.trim();
  cfg.path=document.getElementById("ghPath").value.trim()||"data.json";
  cfg.token=document.getElementById("ghToken").value.trim();
  saveSyncCfg(cfg);
  setSyncStatus(cfg.repo&&cfg.token ? "Saved. Ready to sync "+cfg.repo : "Saved (repo + token needed to sync).");
  toast("Sync settings saved");
};
document.getElementById("ghSyncBtn").onclick=()=>{
  // Persist whatever's in the fields first, then sync.
  document.getElementById("ghSaveCfg").click();
  syncNow();
};
// Clearing the program is the one destructive action that reaches off this
// device. saveProgram() stamps a fresh updatedAt and pushes immediately, and the
// other phone's next sync sees the newer stamp and adopts the empty program
// (see mergeInData) - so one mis-tap here empties BOTH phones, and the store's
// copy is gone too, leaving nothing to restore from. Hence: a backup file first,
// and then the word typed out in full.
document.getElementById("resetProgram").onclick=()=>{
  if(!confirm("Clear the whole program?\n\n"
    + "• Every session and exercise is removed - you start from an empty Program tab.\n"
    + "• This syncs: it empties the program on BOTH phones, not just this one.\n"
    + "• There is no undo.\n"
    + "• Your logged history, bodyweights and coaching notes are NOT touched.\n\n"
    + "A backup file is downloaded first.")) return;
  if(!exportData()){ toast("Backup failed - program not cleared"); return; }
  if((prompt("Backup saved. To confirm, type RESET below.")||"").trim().toUpperCase()!=="RESET"){
    toast("Cancelled - program unchanged"); return;
  }
  state.program={order:[], sessions:{}};
  curSession=state.program.order[0];
  // renderView() sends you to Program when there are no sessions, which is the
  // only tab that works from here (and where + Add session lives).
  saveProgram(); setDlg.close(); renderView(); toast("Program cleared");
};
document.getElementById("deleteAccount").onclick=()=>{
  const i=state.activePerson, nm=state.people[i];
  if(!confirm("Remove "+possessive(nm)+" account from this device? Their logged history, bodyweight and coaching notes stay saved under \""+nm+"\" - re-adding an account with the exact same name later reconnects them - but they'll need to create an account again to log anything.")) return;
  state.people[i]=""; state.colors[i]=""; state.weights[i]=""; state.goals[i]="";
  save(); skipSettingsSave=true; setDlg.close();
  renderPeople(); renderView();
  toast(nm+"'s account removed");
};

const importDlg=document.getElementById("importDlg");
function exportPayload(){
  return {version:1, exportedAt:new Date().toISOString(),
    people:state.people, weights:state.weights, goals:state.goals, coaching:state.coaching,
    coachingLog:state.coachingLog, suggestions:state.suggestions, meals:state.meals,
    bodyweights:state.bodyweights, hrZones:state.hrZones, racePredictions:state.racePredictions,
    limiters:state.limiters, program:state.program, logs:state.logs};
}
// Merge an exported/synced payload into local state. Logs upsert by id and
// bodyweights by person+date (both idempotent). Config (program/people/
// weights/goals) is only replaced when adopting; otherwise empty goals are
// filled from the incoming copy so each person's goal propagates.
// fromSync: only a cloud sync adopts a newer shared program automatically. A
// manual file import must not - it has its own "adopt" tick box, and quietly
// overriding it would replace the program of whoever opened someone else's
// export just to merge a few sessions in.
function mergeInData(data, adoptConfig, fromSync){
  let added=0, updated=0;
  if(Array.isArray(data.logs)){
    var byId={}; state.logs.forEach((l,i)=>{ byId[l.id]=i; });
    data.logs.forEach(function(l){ if(!l) return; if(byId[l.id]!=null){ state.logs[byId[l.id]]=l; updated++; } else { byId[l.id]=state.logs.length; state.logs.push(l); added++; } });
  }
  if(Array.isArray(data.bodyweights)) data.bodyweights.forEach(function(b){ if(b&&b.person&&b.date&&!isNaN(parseFloat(b.kg))) addBodyweight(b.person, b.date, parseFloat(b.kg)); });
  // Coaching is authored centrally (by the MCP coach), so incoming notes win per person.
  if(data.coaching && typeof data.coaching==="object"){ if(!state.coaching) state.coaching={}; Object.keys(data.coaching).forEach(function(p){ state.coaching[p]=data.coaching[p]; }); }
  // Same per-person overwrite as coaching: Garmin is the source of truth for zones.
  if(data.hrZones && typeof data.hrZones==="object"){ if(!state.hrZones) state.hrZones={}; Object.keys(data.hrZones).forEach(function(p){ state.hrZones[p]=data.hrZones[p]; }); }
  if(data.racePredictions && typeof data.racePredictions==="object"){ if(!state.racePredictions) state.racePredictions={}; Object.keys(data.racePredictions).forEach(function(p){ state.racePredictions[p]=data.racePredictions[p]; }); }
  // Limiters: authored centrally like coaching, so incoming wins per person.
  if(data.limiters && typeof data.limiters==="object"){ if(!state.limiters) state.limiters={}; Object.keys(data.limiters).forEach(function(p){ state.limiters[p]=data.limiters[p]; }); }
  // Coaching history: union by id (every past coach write, so improvement can be tracked).
  if(Array.isArray(data.coachingLog)){ if(!Array.isArray(state.coachingLog)) state.coachingLog=[]; var cid={}; state.coachingLog.forEach(function(e){ cid[e.id]=true; }); data.coachingLog.forEach(function(e){ if(e&&e.id!=null&&!cid[e.id]){ state.coachingLog.push(e); cid[e.id]=true; } }); }
  // Improvement suggestions: union by id, and a "done" status wins from either
  // side — so resolving one in the coach/dev chat clears it on every device on
  // the next sync. (A plain union kept the local "open" copy and ignored the
  // incoming "done", so resolved suggestions stayed pending in the app.)
  if(Array.isArray(data.suggestions)){
    if(!Array.isArray(state.suggestions)) state.suggestions=[];
    var byS={}; state.suggestions.forEach(function(s){ if(s&&s.id!=null) byS[s.id]=s; });
    data.suggestions.forEach(function(s){
      if(!s||s.id==null) return;
      var cur=byS[s.id];
      if(!cur){ state.suggestions.push(s); byS[s.id]=s; }
      else if(s.status==="done" && cur.status!=="done"){ cur.status="done"; updated++; }
    });
  }
  // Meals: upsert by id, same as logs. Written by the Home Hub app (barcode /
  // camera capture) into the shared store; this app displays them. Unknown
  // fields are kept as-is so the hub can add some without a change here.
  // See docs/home-hub-link.md for the agreed shape.
  if(Array.isArray(data.meals)){
    if(!Array.isArray(state.meals)) state.meals=[];
    var byM={}; state.meals.forEach(function(m,i){ if(m&&m.id!=null) byM[m.id]=i; });
    data.meals.forEach(function(m){
      if(!m||m.id==null) return;
      if(byM[m.id]!=null){ state.meals[byM[m.id]]=m; updated++; }
      else { byM[m.id]=state.meals.length; state.meals.push(m); added++; }
    });
  }
  // Program: shared between both people, so take the store's copy when it is
  // newer than this device's (saveProgram stamps every edit). A phone that has
  // never stamped its own takes the incoming one; if neither side carries a
  // stamp nothing changes, which is exactly how this behaved before.
  if(fromSync && !adoptConfig && data.program && data.program.sessions){
    const mine=(state.program&&state.program.updatedAt)||"";
    const theirs=data.program.updatedAt||"";
    // Never swap the plan out from under a workout in progress: the log form
    // indexes exercises by position, so a different list would rearrange sets
    // already typed. It adopts on the next sync once the session is saved.
    const busy = activeTab==="log" && !!formDrafts[draftKey()];
    if(theirs && theirs>mine && !busy){
      state.program=clone(data.program);
      updated++;
    }
  }
  if(adoptConfig){
    if(data.program&&data.program.sessions) state.program=clone(data.program);
    if(Array.isArray(data.people)&&data.people.length) state.people=data.people.slice(0,2);
    if(Array.isArray(data.weights)) state.weights=data.weights.slice(0,2);
    if(Array.isArray(data.goals)) state.goals=data.goals.slice(0,2);
    curSession=sessionForDate(curDate)||state.program.order[0];
  } else if(Array.isArray(data.goals)){
    data.goals.forEach(function(g,i){ if(g && !((state.goals[i]||"").trim())) state.goals[i]=g; });
  }
  return {added, updated};
}
// One-pass current bests (max top-set weight) per lifting exercise for a person.
function personPRs(person){
  const best={};
  state.logs.filter(l=>l.person===person).forEach(function(l){
    (l.entries||[]).forEach(function(e){
      if(!isLifting(e)) return;
      const wu=e.warmup||[];
      let top=-Infinity; e.rows.forEach(function(r,ri){ if(wu.indexOf(ri)>=0) return; const w=setLoad(e, r[0], person, l.date); if(!isNaN(w)&&w>top) top=w; });
      if(top>-Infinity && (!(e.name in best) || top>best[e.name].kg)) best[e.name]={kg:top, date:l.date};
    });
  });
  return best;
}
// Epley estimated 1RM.
function epley(w, reps){ return (isNaN(w)||isNaN(reps)||reps<1) ? NaN : w*(1+reps/30); }
// Per-exercise current bests for a person: heaviest working set, the reps on
// it, its estimated 1RM, and when. Warm-up sets excluded.
function personRecords(person){
  const best={};
  state.logs.filter(l=>l.person===person).forEach(function(l){
    (l.entries||[]).forEach(function(e){
      if(!isLifting(e)) return;
      const wu=e.warmup||[];
      e.rows.forEach(function(r,ri){
        if(wu.indexOf(ri)>=0) return;
        const w=setLoad(e, r[0], person, l.date), reps=parseInt(r[1],10);
        if(isNaN(w)) return;
        // `typed`/`bw` are kept so the Records table can show where a
        // bodyweight or assisted figure came from.
        if(!(e.name in best) || w>best[e.name].kg)
          best[e.name]={kg:w, reps:isNaN(reps)?null:reps, date:l.date,
            load:loadTypeOf(e), typed:parseFloat(r[0]), bw:bodyweightOn(person,l.date), pct:loadPctOf(e)};
      });
    });
  });
  return best;
}
function rowPlain(cols, r){
  cols=cols||[];
  const lift=/kg|assist/i.test(cols[0]||"") && /rep/i.test(cols[1]||"");
  const n=Math.max(cols.length, r.length), vals=[];
  for(let i=0;i<n;i++) vals.push(r[i]==null?"":String(r[i]).trim());
  if(lift) return vals[0]+(vals[1]!==""?" x "+vals[1]:"");
  const ne=vals.filter(v=>v!==""); return ne.length?ne.join(" / "):"-";
}
// Markdown coaching brief for one person: goals + bodyweight + PRs + recent
// sessions, with a coach preamble. Paste into Claude, or drop into Obsidian.
function coachBrief(person){
  const i=state.people.indexOf(person);
  const goal=((state.goals&&state.goals[i])||"").trim();
  const bw=bwFor(person), latest=bw.length?bw[bw.length-1]:null;
  const logs=state.logs.filter(l=>l.person===person)
    .sort((a,b)=> a.date<b.date?1:a.date>b.date?-1:(b.id-a.id));
  const prs=personPRs(person);
  let md="# Coaching brief - "+person+"\n\n";
  md+="> You are "+possessive(person)+" strength & conditioning coach. Review the training below "
    + "against the goals and give specific, actionable feedback and the next session's focus.\n\n";
  md+="## Goals\n"+(goal||"_none set_")+"\n\n";
  md+="## Bodyweight\n"+(latest?("Latest **"+latest.kg+" kg** ("+relTime(latest.date)+")"
    + (bw.length>1?"; "+bw.length+" entries logged":"")):"_none logged_")+"\n\n";
  const prNames=Object.keys(prs).sort();
  md+="## Current bests\n"+(prNames.length? prNames.map(n=>"- **"+n+"** - "+prs[n].kg+" kg ("+relTime(prs[n].date)+")").join("\n") : "_none yet_")+"\n\n";
  md+="## Recent sessions (latest "+Math.min(8,logs.length)+")\n";
  if(!logs.length) md+="_none logged_\n";
  logs.slice(0,8).forEach(function(l){
    const meta=[l.date]; if(l.difficulty) meta.push("difficulty "+l.difficulty+"/10");
    if(l.volume) meta.push(l.volume.toLocaleString()+" kg"); if(l.durationSec) meta.push(fmtDuration(l.durationSec));
    md+="\n### "+l.sessionName+" - "+meta.join(" · ")+"\n";
    (l.entries||[]).forEach(function(e){ var wu=e.warmup||[];
      md+="- "+e.name+(e.pr?" 🥇":"")+": "+(e.rows||[]).map(function(r,ri){ var s=rowPlain(e.cols||[],r); return wu.indexOf(ri)>=0?s+" (warm-up)":s; }).join(", ")+"\n"; });
    if(l.feedback) md+="- _Note:_ "+l.feedback+"\n";
  });
  return md;
}
function exportCoachBrief(){
  const person=state.people[state.activePerson];
  const md=coachBrief(person);
  const fname="coach-brief-"+person.replace(/\s+/g,"-")+"-"+todayStr()+".md";
  try{
    const blob=new Blob([md],{type:"text/markdown"});
    const url=URL.createObjectURL(blob);
    const a=document.createElement("a"); a.href=url; a.download=fname;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(()=>URL.revokeObjectURL(url),2000);
  }catch(e){}
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(md).then(()=>toast("Coach brief copied + saved"), ()=>toast("Coach brief saved"));
  } else toast("Coach brief saved");
}
function exportData(){
  const text=JSON.stringify(exportPayload(),null,2);
  const fname="training-data-"+todayStr()+".json";
  try{
    const blob=new Blob([text],{type:"application/json"});
    const url=URL.createObjectURL(blob);
    const a=document.createElement("a"); a.href=url; a.download=fname;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(()=>URL.revokeObjectURL(url),2000);
    state.lastExportAt=new Date().toISOString(); save();
    toast("Exported "+fname);
    return true;
  }catch(e){
    setDlg.close();
    document.getElementById("importText").value=text;
    importDlg.showModal();
    toast("Download blocked - copy this text to transfer");
    // Reported so a caller using the export as a safety net (resetProgram) can
    // stop rather than press on with no backup actually written to disk.
    return false;
  }
}
document.getElementById("importCancel").onclick=()=>importDlg.close();
document.getElementById("importFile").onchange=e=>{
  const f=e.target.files[0]; if(!f) return;
  const r=new FileReader();
  r.onload=()=>{ document.getElementById("importText").value=r.result; };
  r.readAsText(f);
};
document.getElementById("importConfirm").onclick=()=>{
  let data; try{ data=JSON.parse(document.getElementById("importText").value); }
  catch(e){ toast("Couldn't read that data"); return; }
  if(!data || !Array.isArray(data.logs)){ toast("No logs found in import"); return; }
  const res=mergeInData(data, document.getElementById("importAdopt").checked);
  save(); importDlg.close(); setDlg.close(); renderPeople(); renderView();
  toast(res.added+" added, "+res.updated+" updated");
};
document.getElementById("exportBtn").onclick=()=>exportData();
document.getElementById("importBtn").onclick=()=>{ setDlg.close(); importDlg.showModal(); };
document.getElementById("coachBriefBtn").onclick=()=>exportCoachBrief();

// ---- Share a session (routine only - no personal numbers) ----
// Travels as plain text through the phone's native share sheet, since there's
// no backend connecting separate installs. Recipient pastes it back in via
// Import shared session, which decodes and adds it as a new program session.
function slugify(s){ return String(s).toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/(^-+|-+$)/g,"") || "session"; }
function sessionShareCode(sessionKey){
  const s=state.program.sessions[sessionKey];
  // Warm-up/cool-down notes are part of the plan, not personal numbers, so they
  // travel with a shared session.
  const payload={type:"tt-session", v:1, name:s.name, day:s.day||"", exercises:clone(s.exercises)};
  if(s.warmupNote) payload.warmupNote=s.warmupNote;
  if(s.cooldownNote) payload.cooldownNote=s.cooldownNote;
  return b64encode(JSON.stringify(payload));
}
function shareSession(sessionKey){
  const s=state.program.sessions[sessionKey];
  const text="🏋️ "+s.name+" workout - paste this into Training Tracker → Program → Import shared session:\n\n"+sessionShareCode(sessionKey);
  if(navigator.share){
    navigator.share({text}).catch(()=>{}); // user cancelling the share sheet isn't an error
  } else if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(text).then(()=>toast("Share code copied - paste it to them"), ()=>toast("Couldn't copy"));
  } else toast("Sharing isn't supported in this browser");
}
const importSessionDlg=document.getElementById("importSessionDlg");
document.getElementById("importSessionCancel").onclick=()=>importSessionDlg.close();
document.getElementById("importSessionConfirm").onclick=()=>{
  // The pasted text may be the whole shared message (friendly intro line +
  // code), not just the code itself - the code is always the last token.
  const raw=document.getElementById("importSessionText").value.trim();
  const tokens=raw.split(/\s+/).filter(Boolean);
  const candidate=tokens.length?tokens[tokens.length-1]:raw;
  let payload;
  try{ payload=JSON.parse(b64decode(candidate)); }
  catch(e){ toast("Couldn't read that code"); return; }
  if(!payload || payload.type!=="tt-session" || !Array.isArray(payload.exercises)){ toast("Not a valid shared session"); return; }
  let key=slugify(payload.name), n=2;
  while(state.program.sessions[key]){ key=slugify(payload.name)+"-"+n; n++; }
  state.program.sessions[key]={name:payload.name||"Shared session", day:payload.day||"", exercises:payload.exercises};
  if(payload.warmupNote) state.program.sessions[key].warmupNote=String(payload.warmupNote);
  if(payload.cooldownNote) state.program.sessions[key].cooldownNote=String(payload.cooldownNote);
  state.program.order.push(key);
  saveProgram(); document.getElementById("importSessionText").value=""; importSessionDlg.close(); renderEdit();
  toast("Added "+(payload.name||"session"));
};
const sessionDlg=document.getElementById("sessionDlg");
document.getElementById("sessCancel").onclick=()=>sessionDlg.close();
document.getElementById("sessSave").onclick=()=>{
  const name=(document.getElementById("sessName").value||"").trim();
  if(!name){ toast("Name required"); return; }
  const day=document.getElementById("sessDay").value;
  let key=slugify(name), n=2;
  while(state.program.sessions[key]){ key=slugify(name)+"-"+n; n++; }
  state.program.sessions[key]={name, day, exercises:[]};
  state.program.order.push(key);
  saveProgram(); sessionDlg.close(); renderEdit();
  toast("Added "+name);
};

// ---- Cloud sync (GitHub Contents API) ----
const SYNC_KEY="flLiveTracker_sync_v1";
function loadSync(){ try{ return JSON.parse(localStorage.getItem(SYNC_KEY))||{}; }catch(e){ return {}; } }
function saveSyncCfg(s){ localStorage.setItem(SYNC_KEY, JSON.stringify(s)); }
function ghHeaders(token){ return {"Authorization":"Bearer "+token, "Accept":"application/vnd.github+json", "X-GitHub-Api-Version":"2022-11-28"}; }
function b64encode(str){ return btoa(unescape(encodeURIComponent(str))); }
function b64decode(str){ return decodeURIComponent(escape(atob(String(str).replace(/\s/g,"")))); }
function ghUrl(cfg){ return "https://api.github.com/repos/"+cfg.repo+"/contents/"+cfg.path; }
function ghGetFile(cfg){
  return fetch(ghUrl(cfg), {headers:ghHeaders(cfg.token)}).then(function(r){
    if(r.status===404) return {exists:false};
    if(!r.ok) throw new Error("read "+r.status);
    return r.json().then(function(j){ return {exists:true, sha:j.sha, json:JSON.parse(b64decode(j.content))}; });
  });
}
function ghPutFile(cfg, payloadStr, sha){
  const body={message:"Sync training data "+new Date().toISOString(), content:b64encode(payloadStr)};
  if(sha) body.sha=sha;
  return fetch(ghUrl(cfg), {method:"PUT", headers:ghHeaders(cfg.token), body:JSON.stringify(body)}).then(function(r){
    if(!r.ok) return r.text().then(function(t){ throw new Error("write "+r.status); });
    return r.json();
  });
}
function setSyncStatus(msg){ const el=document.getElementById("ghStatus"); if(el) el.textContent=msg; }
// Pull remote -> merge (logs+bodyweights union) -> push merged local back.
// quiet=true for automatic syncs (on save / on open): no toasts, best-effort.
function syncNow(quiet){
  const cfg=loadSync();
  if(!cfg.repo || !cfg.token){ if(!quiet) toast("Add your GitHub repo + token first"); return Promise.resolve(); }
  cfg.path=cfg.path||"data.json";
  setSyncStatus("Syncing…");
  return ghGetFile(cfg).then(function(remote){
    let merged={added:0,updated:0};
    if(remote.exists && remote.json){ merged=mergeInData(remote.json, false, true); save(); } // keep pulled data even if the push fails
    // Push our state over the remote rather than replacing the file outright, so
    // top-level keys this version doesn't know about survive. Without this, a phone
    // running an older build silently deletes any field added since (hrZones, and
    // whatever the Home Hub writes later) just by syncing.
    const payload=Object.assign({}, (remote.exists&&remote.json)||{}, exportPayload());
    return ghPutFile(cfg, JSON.stringify(payload,null,2), remote.exists?remote.sha:null)
      .then(function(res){
        cfg.sha=res&&res.content&&res.content.sha; saveSyncCfg(cfg);
        // A sync can land mid-workout (adding a suggestion, saving machine
        // settings and the on-open pull all trigger one), and the re-render
        // below rebuilds the log form - capture what's typed first or it's gone.
        captureDraft();
        save(); renderPeople(); renderView();
        setSyncStatus("Synced "+new Date().toLocaleTimeString()+" · +"+merged.added+" new, "+merged.updated+" updated");
        if(!quiet) toast("Synced"); else if(merged.added||merged.updated) toast("Synced · "+(merged.added+merged.updated)+" update"+(merged.added+merged.updated===1?"":"s")+" pulled");
      });
  }).catch(function(e){
    const m=String(e.message||e);
    setSyncStatus("Sync failed ("+(m.indexOf("401")>=0||m.indexOf("403")>=0?"check token/repo access":m)+")");
    if(!quiet) toast("Sync failed"); // stay quiet on auto-sync (e.g. offline) — it retries next time
  });
}
// Best-effort background sync — only if configured. Used after save and on open.
function autoSync(){ const c=loadSync(); if(c.repo && c.token) syncNow(true); }

function renderHelp(){
  function card(title, body){ return '<div class="card"><div class="sec-title">'+title+'</div>'+body+'</div>'; }
  function p(t){ return '<p style="margin:0 0 9px">'+t+'</p>'; }
  var h='';
  h+='<div class="card"><h3 style="margin-bottom:6px">How to use this tracker</h3>'
    +'<div class="hint" style="margin-bottom:0">A training + health log for up to two people sharing a device. Log each workout and it tells you what to aim for next time. Works offline, saves only on this device - nothing sent anywhere.</div></div>';

  h+=card('Home',
      p('The app opens on <b>Home</b> - your at-a-glance hub for the selected person: <b>today\'s session</b> (with a <b>Log it</b> shortcut), any <b>🧠 Coach</b> note, quick tiles (sessions &amp; volume this week, latest bodyweight with its trend, total sessions), your <b>last session</b>, your <b>🏃 last Zone 2 run</b> and <b>⚡ last intervals</b> (a card each, since one "last run" only ever showed whichever came most recently - each shows its best pace - the intervals card converts your fastest treadmill speed to a pace so the two read the same way - ❤ average and max HR, and the time-in-zone bar), your <b>❤️ heart rate zones</b>, a <b>bodyweight trend</b> mini-chart, and your <b>goals</b>. The arrows jump to the full <b>History</b>, <b>Body</b> etc.')
     +p('<b>The five tabs</b> are <b>Home</b>, <b>Session</b> (today\'s workout, to log), <b>History</b>, <b>Progress</b> (with <b>🏋 Lifts</b> and <b>⚖ Body</b> side by side at the top) and <b>Program</b>.')
     +p('<b>❤️ Heart rate zones</b> shows your max, resting and threshold HR plus the bpm range of each training zone (Z1 warm up through Z5 maximum), straight from your Garmin settings. Runs that Garmin has linked also get a <b>zone bar</b> under them on Home and in History - which zones you actually spent the run in, and how long in each.')
     +p('<b>🏁 Estimated 5k</b> is what you\'d likely run a 5k in right now. Your <b>coach</b> works it out from your logged runs, using Garmin\'s own race prediction as one input rather than gospel - that prediction comes from a VO₂max model and reads optimistic when you\'ve only done easy runs. The card says what the estimate is based on and how confident it is; before the coach has looked, it shows Garmin\'s raw number marked <b>unreviewed</b>. Expect <b>low confidence</b> until you do a hard effort or a time trial - that\'s the single best thing to make it accurate.')
     +p('<b>Updating your zones:</b> they only refresh when someone runs the zone sync on the laptop, because zones barely ever change so it isn\'t worth doing automatically. After changing them on Garmin, run <code>python mcp-garmin/server.py --hrzones training-garmin</code> (or <code>--hrzones training-garmin-cerys</code>). That refreshes the ranges <i>and</i> tidies up past runs - filling in a missing zone bar, and restoring the run itself into the exercise list on any older cardio session that only shows the <b>⌚ Garmin</b> summary line. It\'s safe to re-run any time - it does nothing when nothing has changed.'));

  h+=card('1 &middot; Pick who you are',
      p('A brand-new install starts blank - no accounts, no program. <b>Create your account</b> with a name and a colour swatch to get going; nothing else is needed. A second person can join the same device later via <b>+ Add</b> next to the name toggle (or skip it and stay solo).')
     +p('Use the <b>name toggle</b> top-right to switch. Each account has its own colour, chosen at creation (or changed later in Settings) - the whole app\'s accent follows whoever\'s selected. The other account\'s colour is greyed out in the picker so you can\'t both end up looking the same. Everything you log and every suggestion belongs to that person. You can switch person <b>mid-entry without losing</b> what you\'ve typed - handy for logging both of you from one phone; a toast confirms when your part is restored.')
     +p('The <b>⚙️ gear</b> (top-right) opens <b>Settings</b> - switch <b>dark / light</b> theme, open this <b>Guide</b>, change your <b>name, colour</b> and <b>bodyweight</b>, and manage export / import / cloud sync. The selected person\'s latest weight shows under the title. Renaming an existing account <b>asks first</b>, since it orphans past history under the old name. <b>Delete this account</b> frees the slot up for someone else - your logged history stays saved under your old name rather than being erased, same as renaming.'));

  h+=card('2 &middot; Log a workout',
      p('Tap the <b>Session</b> tab (or <b>Log it →</b> on Home), then choose the session and date. The date auto-picks the right session for that weekday - and a late-night session (before ~5am) counts as the <b>previous</b> training day. Because Session is its own tab, you can nip to History mid-workout to check last week\'s numbers and come straight back - what you\'ve typed is still there.')
     +p('Type <b>weight</b> and <b>reps</b> per set - phones pop a <b>number pad</b> for any column that takes a number, including ones like <i>Distance (m)</i> or <i>Min</i>, while columns that need real typing (a <i>Time</i> or <i>Pace</i> such as 7:20, or <i>Notes</i>) keep the full keyboard. Enter the first set\'s weight and the rest auto-fill to match. Tick a set\'s <b>checkbox</b> when done: it fills empty reps to the top of the target range, and shows a gold <b>🥇 medal</b> right away if that weight beats your best. Use <b>+ set</b> / <b>- set</b> to change set count.')
     +p('The <b>Last</b> column shows what that person did last time (as "3 days ago" - hover for the date). A <b>🕑 Most recent</b> chip appears when you did that movement more recently in another session. Warm-ups written as a percentage (e.g. "40%x8") show the actual kg for <b>you</b> - worked out from your own last top set for that exercise (and from today\'s weight once you type one), so Daniel and Cerys each get their own warm-up numbers.')
     +p('<b>Machine settings</b> (seat height, pins) are <b>shown on the exercise</b> whenever there are any - no tapping needed when you\'re stood at the machine. Tap the <b>🔧</b> next to the name to write or change them; you can do it <b>mid-session</b> and they\'re saved to the program for next time. The wrench stays highlighted when settings are stored.')
     +p('<b>Tap a set number</b> to mark that set as a <b>warm-up</b> (it shows <b>W</b>). Warm-up sets are excluded from your volume total, PRs and the muscle map - so they don\'t inflate your numbers.')
     +p('<b>Lifting and running</b> exercises get an optional <b>RPE</b> rating (1-10, same scale as the session difficulty rating below), just under the set table - one per exercise, rating how hard it felt overall. That covers your treadmill intervals and easy runs as well as your lifts, so you can record that a session felt easy even when the pace looked fast. Blank is fine if you don\'t use it; it shows in History next to the exercise name.')
     +p('Exercises grouped as a <b>superset/circuit</b> (set up in Edit Program) show together in a bordered block - log each one exactly as normal, there\'s no special entry mode, it\'s just a visual grouping so you can see what pairs with what.')
     +p('<b>&#10133; Add an exercise for today</b> (under the last exercise) covers the gym being busy, a niggle, or just fancying something else - it logs exactly like a normal exercise but shows a dashed <b>Today only</b> card, and your <b>program is untouched</b>. Tap the <b>&#10005;</b> on the card to drop it again. When you save, the popup offers to <b>add it to the program</b> if you want to keep it.')
     +p('<b>Your entry is kept safe.</b> What you\'ve typed is stored on the device as you go, so nothing is lost by leaving the app, switching person, a sync landing mid-set, or your phone dropping the page and reloading it - come back and the sets (and the running timer) are still there. It\'s cleared once you save the session, tap <b>Clear</b>, or leave it more than about 12 hours.'));

  h+=card('3 &middot; Time it, rate it, save',
      p('The <b>timer</b> at the top starts when you begin entering (or tap Start), and is saved with the session; Pause/Reset as needed.')
     +p('Tap a <b>difficulty</b> 1-10 and add any <b>notes</b>. Hit <b>Save session</b>: you get total volume (with a fun comparison), any <b>PRs</b>, and a <b>muscle map</b> of what you worked. Guidance for next time comes from your <b>🧠 Coach</b> notes rather than an auto-generated plan.'));

  h+=card('4 &middot; Cardio &amp; running',
      p('On a <b>cardio day</b> the easiest thing is to just <b>log &amp; save</b> - a banner reminds you. If you wear your <b>Garmin</b>, the run\'s distance, per-km <b>splits</b>, pace and ♥ HR fill in automatically once it syncs; the run starts as a single blank row and shows a <b>🏃 Last run</b> summary to beat. Prefer to enter it yourself? Type the splits (pace is computed for you) or import a file.')
     +p('<b>Interval / speed sessions</b> work slightly differently: you type your own <b>hard and easy paces</b>, and Garmin adds only what it alone measures - <b>♥ HR, heart-rate zones and calories</b> - without overwriting anything you entered. That works because the exercise is ticked <b>⌚ Garmin records this</b> in Edit Program (real distance+time runs are detected automatically; tick it for cardio logged as paces instead). These hard efforts are also the most valuable data for your <b>🏁 Estimated 5k</b>.')
     +p('<b>Should you tick the run\'s box?</b> Entirely up to you - it\'s only a visual "done" marker, it\'s never saved, and on a run it fills nothing in (the auto-fill only applies to lifting), so the saved result is identical either way. What actually matters is leaving the run\'s row <b>empty</b>: anything typed there counts as your own data and Garmin won\'t overwrite it, so the splits won\'t come through.')
     +p('On a running exercise, <b>⬆ Import run (TCX/GPX)</b> pulls a run exported from Garmin or Strava straight into the splits - export the file on your laptop, then import.')
     +p('<b>Garmin auto-link (⌚):</b> when you save a cardio session it\'s tagged <i>⌚ awaiting run…</i>; the Garmin sync on the laptop then finds that day\'s run and adds the extra info - <b>heart rate, cadence, elevation, calories, moving time, training effect</b>, and per-km splits if you left them blank - shown as a <b>⌚ Garmin</b> line in History. It never overwrites what you typed. (Set up in <code>mcp-garmin</code>; needs the laptop.)')
     +p('On an <b>interval</b> session it also works out the <b>reps you actually did</b> - "6 × 0:58 hard, 2:02 easy between" - by reading the speed trace off your watch. Garmin\'s own laps can\'t show this (a treadmill laps every 1 km, so several reps and their recoveries end up inside one lap), and it\'s <b>structure only</b>: the speeds <b>you</b> typed stay the record for speed, because treadmill pace is estimated from your wrist and reads high. It means your coach can see whether the session you were set is the session you did - including when you had to cut one short.'));

  h+=card('5 &middot; History, Progress &amp; Records',
      p('<b>History</b> opens with a <b>This week</b> summary for the selected person - total volume, session count, a muscle heatmap of what you\'ve hit, and a weekly-volume bar chart - then lists every saved session (newest first); filter by person, tap <b>View</b> for full detail, or delete. <b>Runs</b> show their <b>distance, time, pace and ♥ heart rate</b> right on the row, and open to a <b>splits table</b> (each lap\'s pace and HR, with a totals line) plus the <b>⌚ Garmin</b> extras (cadence, elevation, calories, training effect, VO₂).')
     +p('<b>&#128221; Your own notes can be added or changed after the event.</b> Open a session with <b>View</b> and tap <b>Add a note</b> (or <b>Edit note</b> if there\'s one already) - so remembering something on the drive home, or the day after, isn\'t too late. It saves as soon as you tap away, and it\'s the same note the coach reads.')
     +p('<b>Progress</b> has two halves, switched at the top. <b>🏋 Lifts</b> shows the selected person\'s <b>current bests</b> (weight, reps and estimated 1RM per exercise), then charts your top set for any exercise over time with both people on one graph. <b>⚖ Body</b> is your goals, bodyweight and its trend - see section 6.'));

  h+=card('6 &middot; Body, goals &amp; bodyweight',
      p('<b>Body lives inside Progress</b>, on the <b>⚖ Body</b> half of the toggle at the top of that tab (<b>🏋 Lifts</b> is the other). It tracks each person\'s bodyweight over time with a trend chart. Add a weight by hand, or <b>⬆ Import from scale (CSV)</b> a file exported from your scale app (e.g. 1byone Health) - it finds the date and weight columns automatically.')
     +p('Set your <b>goals</b> in the gear menu; they show at the top of the Body pane and travel with your data, so a coach (or Claude) can see what you\'re working toward.')
     +p('For AI coaching, the gear menu\'s <b>Coach brief (Markdown)</b> button bundles the selected person\'s goals, PRs, bodyweight and recent sessions into a summary you can paste into Claude (or drop into Obsidian).')
     +p('When a coach sends you notes, they show as teal <b>🧠 Coach</b> cards on <b>Home</b> and at the top of the <b>Log</b> tab: a note for <b>today’s session</b>, an optional <b>general</b> note, and a <b>🧠 Coach</b> cue with a next step on each exercise. Every past note is kept under <b>🧠 Coaching history</b> on Home, so you (and the coach) can see how the advice has changed and whether it worked. Tap <b>Sync now</b> to pull the latest coaching.')
     +p('<b>&#9889; Next cardio</b> is the one coach card that does more than tell you something. When two cardio sessions share a day, your coach can <b>assign</b> which one is next and what to do in it - and the app then <b>opens that one</b> for you, instead of guessing. It\'s <b>per person</b>, so you and your partner can get different numbers for the same session. Once you\'ve logged a cardio session the card goes quiet and marks itself <b>done</b>, and the app goes back to <b>alternating on its own</b> - whichever of the two you did least recently - until your coach writes a new one. You can always pick the other session from the list anyway; it\'s a default, not a lock.')
     +p('<b>&#128681; What\'s holding this back</b> shows on a session when you\'ve told your coach what\'s limiting it - "haven\'t found my top working speed yet", "Zone 2 is a walk for me, not a run". It\'s in <b>your</b> words, kept apart from the coach\'s own read of your numbers, and it\'s the first thing the coach checks - because two people can produce the same heart-rate trace for completely opposite reasons.'));

  h+=card('7 &middot; Edit the program',
      p('Sessions are listed <b>closed</b>, one line each with the day and how many exercises are in it, so the whole week fits on a screen and you can find the one you want. <b>Tap a session</b> to open it; open as many as you like. They stay open while you\'re using the app - including if you nip to another tab - and start closed again next time you open it.')
     +p('<b>Edit Program</b> lets you add / edit / reorder / remove exercises. Pick a name from the <b>suggestions list</b> to avoid duplicate spellings (start typing to search - it\'s pre-loaded with common exercises even on a brand-new account, plus anything you\'ve already used - or just type a new one). Set a <b>target</b>, a <b>warm-up</b> (a <b>%</b> is best - it scales to each person\'s own last top set; a fixed weight is the same for both of you), and <b>setup notes</b> (seat height, pins - editable straight from the log form too). Use the <b>Lifting</b> / <b>Running</b> presets for the column labels, or add a 3rd column.')
     +p('<b>&#10133; Add session</b> creates a brand-new workout day (name + weekday) - a blank account starts with no sessions at all, so this is the first thing to do there.')
     +p('Set a session\'s day to <b>Optional - any day</b> and it stops being part of the week: the calendar never opens it for you, Home never calls it today\'s session, and it sits at the bottom of the session list waiting to be picked. That\'s for the extra you do <i>if you fancy it</i> - a weekend run, a spare mobility session - without it turning into something you\'ve skipped. Because an optional session can be weeks apart, its log opens with a <b>&#128197; Last time</b> card - when you last did it, what you did, and the note you left - so you\'re not trying to remember.')
     +p('<b>&#128293; Warm-up / &#129482; cool-down</b> on a session holds free-text notes for what you do either side of the exercises - "3 min cross-trainer, then shoulder mobility", or which stretches you finish on. They show as their own cards at the top and bottom of that session\'s log, in the order you actually do them, and travel with a shared session. Leave either blank and nothing appears.')
     +p('<b>What are you lifting?</b> tells the app what the number in the first column actually means, for pull-ups, dips, press-ups and assisted machines. <b>Your bodyweight, plus any added weight</b> scores you as your own weight plus whatever you type (0 or blank = just you); <b>minus the machine\'s help</b> subtracts the assistance instead, so <b>less help counts as a better set</b> - which is the way round it should always have been. It only changes the <b>maths</b> (volume, PRs, estimated 1RM, 🥇 medals) - you type the same number as always, and the column gets renamed <i>Added</i> or <i>Assist</i> so it\'s unambiguous. The <b>% of bodyweight</b> box is how much of you the movement really lifts (pull-up or dip 100, press-up about 65), so a set of press-ups doesn\'t swamp your volume.')
     +p('Your <b>bodyweight on the day of that session</b> is used, so old sessions keep the numbers you earned at the time. Weigh in on the Body tab to keep it honest - with no weigh-ins at all it falls back to the figure in Settings. Turning the setting on re-scores that exercise\'s <b>records and PRs</b> straight away (they\'re worked out live); the volume total already saved against past sessions is left as it was logged. Went from assisted to unassisted to weighted on the same movement? Use <b>bodyweight + added</b> and type the assistance as a negative number, or keep them as two exercises.')
     +p('<b>Works</b> tags which muscles an exercise counts toward on the heatmap - guessed from the name automatically, but tap to add/remove any that got missed (handy for oddly-named exercises).')
     +p('<b>&#128279; Share</b> on a session sends its exercise list (no personal numbers) through your phone\'s share sheet - useful if someone else you know is using their own copy of the app. They paste the code back in via <b>&#128229; Import shared session</b> at the top of this tab to add it as a new session on their program.')
     +p('Tick the checkbox on 2+ exercises in the same session, then <b>&#8646; Group as superset</b>, to mark them as a superset/circuit - they\'re moved next to each other and shown in a bordered block on both this tab and the Log tab. <b>Ungroup</b> on the block splits them back into normal standalone exercises. Moving a grouped exercise up/down moves the whole block together; each exercise inside still logs completely normally.')
     +p('Program edits only affect future logging; past history is untouched. <b>Clear program</b> (gear menu) empties the Program tab so you can start again from scratch - there is no built-in default plan to go back to. It <b>downloads a backup file first</b> and then asks you to type RESET, because it can\'t be undone and, if you use cloud sync, it empties the program on <b>both phones</b>. Your logged history, bodyweights and coaching notes are never touched by it.'));

  h+=card('8 &middot; Your data, backups &amp; sync',
      p('Everything saves <b>on this device</b>. Gear menu &rarr; <b>Export</b> saves a file with everything; <b>Import / merge</b> on another device adds it in, merged by unique ID so nothing duplicates.')
     +p('<b>Cloud sync (GitHub)</b> is optional and free: set a private repo + access token in the gear menu once. After that it syncs <b>automatically</b> - when you open the app and after every save - so both of you stay up to date and your coach sees new sessions without you doing anything. (<b>Sync now</b> is still there for a manual pull.) It doubles as an off-device <b>backup</b>; the token is stored only on this device and never included in exports.')
     +p('<b>The program syncs too.</b> Everyone sharing a store trains the same plan, so an edit in <b>Program</b> - a new exercise, a warm-up note, a reorder - goes up straight away and lands on the other phone next time it syncs. The most recent edit wins, so nothing you change gets replaced by an older copy, and it never swaps the plan over <b>mid-workout</b>: if you\'ve got sets typed in, it waits until you\'ve saved. Devices without cloud sync set up keep their own program entirely.')
     +p('It\'s an installable app: open in your phone browser and <b>Add to Home Screen</b>, then always open it from that icon. It works <b>offline</b>.')
     +p('Gear menu &rarr; <b>What\'s not set up yet</b> lists anything that needs laptop-side setup (cloud sync, Garmin auto-import, AI coaching) and what it takes - none of it is tied to a particular account, so any account can get the same thing the same way.'));

  h+=card('Quick tips',
      p('&bull; Beat the <b>Last</b> numbers - even one extra rep counts.')
     +p('&bull; Tick sets as you go to catch PRs live and auto-fill reps.')
     +p('&bull; No cloud sync? Export regularly as a backup, and to keep both of you in sync. With sync on, that\'s already handled - every save pushes a full copy off-device.')
     +p('&bull; Spotted a bug or have an idea? Jot it in the gear menu under <b>💡 Improve the app</b> - it syncs to the dev backlog so it isn\'t forgotten.'));

  document.getElementById("view").innerHTML=h;
}

const VOL_REFS=[
  {n:"house cats",w:4.5,e:"🐱"},
  {n:"bulldogs",w:25,e:"🐶"},
  {n:"baby elephants",w:110,e:"🐘"},
  {n:"grizzly bears",w:360,e:"🐻"},
  {n:"grand pianos",w:480,e:"🎹"},
  {n:"horses",w:550,e:"🐴"},
  {n:"dairy cows",w:750,e:"🐄"},
  {n:"compact cars",w:1300,e:"🚗"},
  {n:"hippos",w:1500,e:"🦛"},
  {n:"rhinos",w:2300,e:"🦏"},
  {n:"African elephants",w:6000,e:"🐘"},
  {n:"T. rexes",w:8000,e:"🦖"},
  {n:"London buses",w:12000,e:"🚌"},
  {n:"whale sharks",w:19000,e:"🐋"}
];
function volCompare(total){
  var refs=VOL_REFS.slice().sort(function(a,b){return a.w-b.w;});
  var pick=refs[0];
  for(var i=0;i<refs.length;i++){ if(total/refs[i].w>=1.2) pick=refs[i]; }
  var count=total/pick.w;
  var cstr = count>=10? String(Math.round(count)) : String(Math.round(count*10)/10);
  return {text:"about "+cstr+" "+pick.n, emoji:pick.e};
}
function lerp(a,b,t){return Math.round(a+(b-a)*t);}
function muscleColor(c,max){
  if(!c||!max) return ""; // unworked: clear inline fill, fall back to CSS --musc-base
  // Neutral intensity heat ramp (warm amber -> hot red as the set count rises).
  // Person-independent on purpose: the map reads as "how hard" not "who", so it
  // doesn't clash with the per-person accents. Endpoints suit light + dark cards.
  var t=c/max, lo=[255,206,110], hi=[222,60,45];
  return "rgb("+lerp(lo[0],hi[0],t)+","+lerp(lo[1],hi[1],t)+","+lerp(lo[2],hi[2],t)+")";
}
const MUSCLE_LABELS = {quads:"Quads",glutes:"Glutes",hamstrings:"Hamstrings",adductors:"Adductors",
  calves:"Calves",chest:"Chest",delts:"Delts",triceps:"Triceps",lats:"Lats",traps:"Traps",
  biceps:"Biceps",forearms:"Forearms",abs:"Abs",lowerback:"Lower back"};
// Renders the exercise-dialog muscle-tag pills with `selected` pre-toggled.
function renderMuscleTags(container, selected){
  container.innerHTML = Object.keys(MUSCLE_LABELS).map(function(k){
    return '<button type="button" data-m="'+k+'" class="'+(selected.indexOf(k)>=0?"sel":"")+'">'+MUSCLE_LABELS[k]+'</button>';
  }).join("");
}
function readMuscleTags(container){
  return Array.prototype.slice.call(container.querySelectorAll("button.sel")).map(function(b){ return b.dataset.m; });
}
function classifyMuscles(name){
  var n=String(name).toLowerCase(), m=[];
  function add(){for(var i=0;i<arguments.length;i++){if(m.indexOf(arguments[i])<0)m.push(arguments[i]);}}
  if(/squat|leg press|lunge/.test(n)) add("quads","glutes");
  if(/leg extension/.test(n)) add("quads");
  if(/(lying|seated|leg)\s*curl/.test(n) || /hamstring/.test(n)) add("hamstrings");
  if(/deadlift|romanian|rdl|good ?morning/.test(n)) add("hamstrings","glutes");
  if(/abduction|glute|hip thrust/.test(n)) add("glutes");
  if(/adduction|adductor/.test(n)) add("adductors");
  if(/calf|calves/.test(n)) add("calves");
  if(/bench|incline|crossover|fly|pec|push.?up/.test(n) || (/chest/.test(n) && !/row/.test(n))) add("chest");
  if(/press/.test(n) && !/overhead|shoulder|leg|ohp|military|chest/.test(n)) add("chest");
  if(/overhead press|shoulder press|ohp|military/.test(n)) add("delts");
  if(/lateral raise|side raise|rear delt|face pull|reverse fly/.test(n)) add("delts");
  if(/tricep|pushdown|skull|overhead ext/.test(n)) add("triceps");
  if(/pulldown|pull.?up|chin.?up/.test(n)) add("lats");
  if(/row/.test(n)) add("traps");
  if(/curl/.test(n) && !/leg|lying|seated/.test(n)) add("biceps");
  if(/hammer|forearm|wrist/.test(n)) add("forearms");
  if(/crunch|plank|sit.?up|leg raise|hanging/.test(n)) add("abs");
  if(/back extension|hyperextension|lower back/.test(n)) add("lowerback");
  return m;
}
// Muscle set-counts (warm-ups excluded) from a list of entries, and from logs.
function muscleSetsFromEntries(entries){
  var m={};
  (entries||[]).forEach(function(en){
    var ms=(en.muscles&&en.muscles.length) ? en.muscles : classifyMuscles(en.name||"");
    var sets=((en.rows&&en.rows.length)||0)-((en.warmup&&en.warmup.length)||0);
    ms.forEach(function(mk){ m[mk]=(m[mk]||0)+sets; });
  });
  return m;
}
function muscleSetsForLogs(logs){
  var m={};
  logs.forEach(function(l){ var mm=muscleSetsFromEntries(l.entries); for(var k in mm){ m[k]=(m[k]||0)+mm[k]; } });
  return m;
}
// Shade an SVG muscle map (by data-muscle) from a set-count map; returns the max.
function paintMuscleMap(svgEl, museSets){
  var maxc=0; for(var k in museSets){ if(museSets[k]>maxc) maxc=museSets[k]; }
  svgEl.querySelectorAll(".musc").forEach(function(el){
    var mk=el.getAttribute("data-muscle"); var cval=museSets[mk]||0;
    el.style.fill = muscleColor(cval,maxc);
    var ti=el.querySelector("title");
    if(ti){ var base=ti.textContent.replace(/:.*$/,""); ti.textContent=base+": "+cval+" set"+(cval===1?"":"s"); }
  });
  return maxc;
}
// One-tap "that swap was a keeper" - copies a today-only exercise into the
// program for next time. Strips the todayOnly marker so it becomes a normal
// programmed exercise.
function promoteTodayExercise(sessionKey, ex, btn){
  const sess=state.program.sessions[sessionKey];
  if(!sess){ toast("That session no longer exists"); return; }
  const def=clone(ex); delete def.todayOnly;
  sess.exercises.push(def);
  saveProgram();
  btn.disabled=true; btn.textContent="Added ✓";
  toast("Added "+def.name+" to "+sess.name);
}
function showSaveSummary(volume, prs, entries, promotable, promoteKey){
  var prHtml = prs.length
    ? prs.map(function(pr){return '<div style="background:#fff7e0;border:1px solid #f0dca0;border-radius:8px;padding:6px 10px;margin:6px 0;font-size:13.5px;font-weight:700;color:#8a6d1a">🥇 New PR &middot; '+esc(pr.name)+' &middot; '+pr.weight+' kg</div>';}).join("")
    : '';
  if(volume>0){
    var c=volCompare(volume);
    document.getElementById("saveEmoji").textContent=c.emoji;
    document.getElementById("saveVol").textContent=volume.toLocaleString()+" kg moved";
    document.getElementById("saveCompare").textContent="That's "+c.text+"!";
  } else {
    document.getElementById("saveEmoji").textContent="🏃";
    document.getElementById("saveVol").textContent="Session saved";
    document.getElementById("saveCompare").textContent="Great conditioning work!";
  }
  var muscleSets=muscleSetsFromEntries(entries);
  var wrap=document.getElementById("muscleWrap");
  if(paintMuscleMap(document.getElementById("muscleSvg"), muscleSets)>0) wrap.style.display="";
  else wrap.style.display="none";
  document.getElementById("savePRs").innerHTML=prHtml;
  const promoteEl=document.getElementById("savePromote");
  const extras=promotable||[];
  const sess=state.program.sessions[promoteKey];
  if(promoteEl){
    promoteEl.innerHTML = (extras.length && sess)
      ? '<div class="hint" style="margin:10px 0 6px">Added just for today. Keep '
        + (extras.length===1?'it':'them')+' in <b>'+esc(sess.name)+'</b> from now on?</div>'
        + extras.map(function(ex,i){
            return '<div class="row" style="justify-content:space-between;align-items:center;gap:8px;margin-bottom:5px">'
              + '<span style="font-size:13px">'+esc(ex.name)+'</span>'
              + '<button class="mini" data-promote="'+i+'">&#10133; Add to program</button></div>';
          }).join("")
      : '';
    promoteEl.querySelectorAll("[data-promote]").forEach(function(b){
      b.onclick=function(){ promoteTodayExercise(promoteKey, extras[+b.dataset.promote], b); };
    });
  }
  document.getElementById("saveDlg").showModal();
}
document.getElementById("saveDlgOk").onclick=function(){ document.getElementById("saveDlg").close(); };

// Home dashboard — the hub landing: greeting + today's session, coach card,
// this-week stat tiles, last session, last Zone 2 run, last intervals,
// bodyweight trend, goals.
// Reuses existing helpers; links out to the detailed tabs.
// The five Garmin HR training zones. Reference info (what each zone's bpm band is),
// not time spent in them - written by mcp-garmin's `--hrzones` into state.hrZones,
// keyed by person name. Renders nothing at all until that's been run for someone.
const HR_ZONE_NAMES=["Warm up","Easy","Aerobic","Threshold","Maximum"];
function hrZonesCardHtml(person){
  const z=(state.hrZones&&state.hrZones[person])||null;
  if(!z || !Array.isArray(z.floors) || z.floors.length<5) return "";
  const stat=(lab,v)=> v==null?"":lab+' <b>'+esc(String(v))+'</b>';
  const stats=[stat("Max",z.maxHr), stat("Resting",z.restingHr), stat("Threshold",z.thresholdHr)].filter(Boolean);
  const rows=z.floors.map(function(lo,i){
    // Each zone runs up to just under the next zone's floor; the top one runs to max HR.
    const nextLo=z.floors[i+1];
    const hi = nextLo!=null ? nextLo-1 : ((z.maxHr!=null && z.maxHr>lo) ? z.maxHr : null);
    return '<div class="hrz-row"><span class="hrz-dot" data-z="'+(i+1)+'"></span>'
      + '<span class="hrz-name">Z'+(i+1)+' <span class="hrz-sub">'+esc(HR_ZONE_NAMES[i])+'</span></span>'
      + '<span class="hrz-range">'+esc(hi!=null ? lo+"-"+hi : lo+"+")+' bpm</span></div>';
  }).join("");
  return '<div class="card"><div class="sec-title" style="margin:0 0 6px">❤️ Heart rate zones</div>'
    + (stats.length?'<div class="ex-meta" style="margin-bottom:8px">'+stats.join(' · ')+' bpm</div>':'')
    + rows
    + '<div class="hint" style="margin-top:6px">From Garmin'
    + (z.updated?' · updated '+esc(relTime(String(z.updated).slice(0,10))):'')+'</div></div>';
}
// Stacked bar of where a run's time actually sat across the HR zones (seconds per
// zone, Z1..Z5, from Garmin - see mcp-garmin fetch_hr_zone_times). Complements the
// zone-range card above: that says what the bands are, this says which you were in.
function hrZoneBarHtml(secs){
  if(!Array.isArray(secs)) return "";
  const total=secs.reduce(function(t,s){ return t+(s||0); },0);
  if(total<=0) return "";
  const bar=secs.map(function(s,i){
    return (s>0) ? '<span class="hrzbar-seg" data-z="'+(i+1)+'" style="width:'+(s/total*100).toFixed(2)+'%"'
      + ' title="Z'+(i+1)+' '+esc(HR_ZONE_NAMES[i])+' · '+esc(fmtDuration(s))+'"></span>' : '';
  }).join("");
  let top=0;
  secs.forEach(function(s,i){ if((s||0)>(secs[top]||0)) top=i; });
  return '<div class="hrzbar">'+bar+'</div>'
    + '<div class="ex-meta" style="margin-top:5px">Mostly <b>Z'+(top+1)+' '+esc(HR_ZONE_NAMES[top])+'</b> · '
    + esc(fmtDuration(secs[top]))+' of '+esc(fmtDuration(total))
    + ' ('+Math.round(secs[top]/total*100)+'%)</div>';
}
// Estimated 5k. Normally the coach's considered figure (written via write_coaching's
// five_k), which weighs Garmin's race prediction against the runs actually logged.
// Until the coach has looked, Garmin's own prediction shows instead - clearly marked
// unreviewed, because that model runs optimistic without hard efforts to learn from.
function fiveKCardHtml(person){
  const est=((state.coaching&&state.coaching[person])||{}).fiveK;
  const pred=(state.racePredictions&&state.racePredictions[person])||null;
  let time, pace, basis, conf, when;
  if(est && est.time){
    time=est.time;
    pace=est.pace||"";
    basis=est.basis||"";
    conf=(est.confidence||"").toLowerCase();
    when=est.updated ? "Coach · "+relTime(String(est.updated).slice(0,10)) : "From your coach";
  } else if(pred && pred["5k"]){
    time=fmtDuration(pred["5k"]);
    pace=fmtDuration(pred["5k"]/5);
    basis="Garmin's own prediction - your coach hasn't reviewed this against your logged runs yet.";
    conf="unreviewed";
    when=pred.updated ? "Garmin · "+relTime(String(pred.updated).slice(0,10)) : "From Garmin";
  } else return "";
  return '<div class="card"><div class="flex-between" style="align-items:baseline">'
    + '<div class="sec-title" style="margin:0">🏁 Estimated 5k</div>'
    + (conf?'<span class="conf" data-c="'+esc(conf)+'">'+esc(conf)+(conf==="unreviewed"?"":" confidence")+'</span>':'')
    + '</div>'
    + '<div class="fivek">'+esc(time)+(pace?'<span class="sub"> · '+esc(pace)+' /km</span>':'')+'</div>'
    + (basis?'<div class="ex-meta" style="margin-top:2px">'+esc(basis)+'</div>':'')
    + '<div class="hint" style="margin-top:5px">'+esc(when)+'</div></div>';
}
// The coach's next-cardio assignment. Unlike the other coach notes this one
// isn't only advice - while it's live it decides which cardio session the app
// opens on a day two of them share (see sessionForDate). Once a cardio session
// has been logged it stays on screen but goes quiet, so you can still see what
// was asked for without a fortnight-old prescription still driving the app.
function nextCardioCardHtml(person){
  const nc=((state.coaching&&state.coaching[person])||{}).nextCardio;
  if(!nc || !nc.session) return "";
  const live=!!liveNextCardio();
  const when=nc.updated ? "Coach · "+relTime(String(nc.updated).slice(0,10)) : "From your coach";
  return '<div class="card coach-card'+(live?'':' spent')+'">'
    + '<div class="flex-between" style="align-items:baseline">'
      + '<div class="sec-title" style="margin:0">&#9889; Next cardio</div>'
      + '<span class="conf" data-c="'+(live?'assigned':'done')+'">'+(live?'assigned':'done')+'</span>'
    + '</div>'
    + '<h3 style="margin:8px 0 2px">'+esc(nc.session)+'</h3>'
    + (nc.focus?'<div style="white-space:pre-wrap">'+esc(nc.focus)+'</div>':'')
    + (nc.why?'<div class="ex-meta" style="margin-top:4px">'+esc(nc.why)+'</div>':'')
    + '<div class="hint" style="margin-top:5px">'+esc(when)
      + (live?' · this is the one the app will open for you'
             :' · done - the app is back to alternating until your coach looks again')+'</div>'
    + '</div>';
}
let homeChart=null;
function renderHome(){
  const p=state.people[state.activePerson];
  const pc = personSwatch(p);
  const thisWk=weekMonday(trainingDateStr());
  const pLogs=[...state.logs].filter(l=>l.person===p).sort((a,b)=> (a.date<b.date?1:a.date>b.date?-1:b.id-a.id));
  const wkLogs=pLogs.filter(l=>weekMonday(l.date)===thisWk);
  const wkVol=wkLogs.reduce((t,l)=>t+(l.volume||0),0);
  const last=pLogs[0];
  const lastRun=pLogs.find(l=>(l.entries||[]).some(e=>isRunning(e)));
  const lastIntervals=pLogs.find(l=>(l.entries||[]).some(e=>isIntervalEntry(e)));
  const bw=bwFor(p);
  const latest=bw.length? bw[bw.length-1] : null;
  let bwDelta="";
  if(bw.length>=2){ const d=Math.round((bw[bw.length-1].kg-bw[bw.length-2].kg)*10)/10; bwDelta = d>0?'▲ '+d:d<0?'▼ '+Math.abs(d):'-'; }
  const coach=(state.coaching&&state.coaching[p])||{};
  const goal=(state.goals&&state.goals[state.activePerson])||"";
  const sess=state.program.sessions[curSession];
  // This card follows curSession (so Log it → takes you where you were), but it
  // used to call that "today's session" unconditionally - pick anything else on
  // the Log tab and Home would insist that was today. Only claim it's today's
  // when the calendar agrees. Matters most for an Optional session, which the
  // calendar deliberately never picks, and on Sat/Sun, where nothing is
  // scheduled and curSession is just a fallback.
  const todayKey=sessionForDate(trainingDateStr());
  const isToday=!!todayKey && curSession===todayKey;
  let niceDate; try{ niceDate=new Date().toLocaleDateString(undefined,{weekday:"long",day:"numeric",month:"long"}); }catch(e){ niceDate=todayStr(); }

  let html='<div class="card">'
    + '<div class="sec-title" style="margin:0">👋 '+esc(possessive(p))+' hub</div>'
    + '<div class="home-greet">'+esc(niceDate)+'</div>'
    + '<div class="flex-between" style="align-items:center;gap:10px;flex-wrap:wrap;margin-top:10px">'
    + '<div>'+(isToday?'Today’s session':'Selected session')+': <b>'+esc(sess?sess.name:"-")+'</b>'+(sess?' <span class="hint" style="margin:0">· '+esc(sess.day)+'</span>':"")+'</div>'
    + '<button class="btn btn-primary" id="homeLogBtn">Log it →</button>'
    + '</div></div>';

  html += nextCardioCardHtml(p);

  const coachSessNote=(coach.bySession && sess && coach.bySession[sess.name])||"";
  if(coachSessNote){
    html+='<div class="card coach-card"><div class="sec-title">🧠 Coach · '+esc(sess.name)+(coach.updated?' &middot; '+relTime(coach.updated):"")+'</div>'
      + '<div style="white-space:pre-wrap">'+esc(coachSessNote)+'</div></div>';
  }
  if(coach.overall){
    html+='<div class="card coach-card"><div class="sec-title">🧠 Coach'+(coach.updated?' &middot; '+relTime(coach.updated):"")+'</div>'
      + '<div style="white-space:pre-wrap">'+esc(coach.overall)+'</div></div>';
  }

  html+='<div class="tiles">'
    + '<div class="tile"><div class="big">'+wkLogs.length+'</div><div class="lbl">sessions this week</div></div>'
    + '<div class="tile"><div class="big">'+wkVol.toLocaleString()+'</div><div class="lbl">kg volume this week</div></div>'
    + '<div class="tile"><div class="big">'+(latest? latest.kg+'<span class="sub"> kg</span>':'-')+'</div><div class="lbl">bodyweight'+(bwDelta?' · '+bwDelta:'')+'</div></div>'
    + '<div class="tile"><div class="big">'+pLogs.length+'</div><div class="lbl">sessions logged</div></div>'
    + '</div>';

  if(last){
    const pr=(last.entries||[]).some(e=>e.pr);
    html+='<div class="card"><div class="flex-between"><div class="sec-title" style="margin:0">Last session</div>'
      + '<button class="mini" data-home-go="history">History →</button></div>'
      + '<h3 style="margin:8px 0 2px">'+esc(last.sessionName)+(pr?' 🥇':'')+' <span class="pill" data-sw="'+pc+'">'+relTime(last.date)+'</span></h3>'
      + '<div class="ex-meta">'+esc(last.date)+(last.difficulty?' · difficulty '+last.difficulty+'/10':"")+(last.volume?' · '+last.volume.toLocaleString()+' kg':"")+(last.durationSec?' · ⏱ '+fmtDuration(last.durationSec):"")+garminStatus(last)+'</div>'
      + '</div>';
  } else {
    html+='<div class="card empty">No sessions logged yet.<br>Tap <b>Log it</b> on <b>Home</b> to record your first one.</div>';
  }

  // The two cardio sessions are different jobs and read completely differently,
  // so they get a card each. One combined "last run" only ever showed whichever
  // came last - and worse, it could never show the intervals at all, because it
  // keyed on isRunning() (distance + time) and treadmill reps are logged as
  // speeds. Daniel's interval sessions, HR data and all, were invisible here.
  const cardioCard=(log, entry, title, lead)=>{
    const g=log.garmin||{};
    const bits=[];
    if(lead) bits.push(lead);
    // Garmin's moving time, not the session timer: this card is about the run,
    // and everything beside it (HR, the zone bar) already is. The timer covers
    // the whole gym session, so on a cardio+core day it read 1:12:33 next to an
    // 18:31 zone bar. Falls back to the timer when there's no watch data.
    if(g.moving_time) bits.push('⏱ '+g.moving_time);
    else if(log.durationSec) bits.push('⏱ '+fmtDuration(log.durationSec));
    // Red heart for the average, orange for the peak - the same direction the
    // zone palette runs (--hrz2 green through --hrz4 orange to --hrz5 red), so
    // the hotter number reads as the hotter colour rather than needing the label.
    if(g.avg_hr!=null) bits.push('❤ '+g.avg_hr+' avg');
    if(g.max_hr!=null) bits.push('🧡 '+g.max_hr+' max');
    return '<div class="card"><div class="flex-between"><div class="sec-title" style="margin:0">'+title+'</div>'
      + '<button class="mini" data-home-go="history">History →</button></div>'
      + '<h3 style="margin:8px 0 2px">'+esc(log.sessionName)+' <span class="pill" data-sw="'+pc+'">'+relTime(log.date)+'</span></h3>'
      + '<div class="ex-meta">'+(bits.length?bits.map(esc).join(' · '):'-')+garminStatus(log)+'</div>'
      + (intervalStructureText(g)?'<div class="ex-meta" style="margin-top:3px">⚙ '+esc(intervalStructureText(g))+'</div>':'')
      + hrZoneBarHtml(g.hr_zone_secs)+'</div>';
  };

  if(lastRun){
    const runEntry=(lastRun.entries||[]).find(e=>isRunning(e));
    const km=(runEntry.rows||[]).reduce((t,r)=>t+(parseFloat(r[0])||0),0);
    const best=bestPaceFromEntry(runEntry);
    const lead=[km?(Math.round(km*100)/100)+' km':'', best?'best '+best:''].filter(Boolean).join(' · ');
    html+=cardioCard(lastRun, runEntry, '🏃 Last Zone 2 run', lead);
  }
  if(lastIntervals){
    const ivEntry=(lastIntervals.entries||[]).find(e=>isIntervalEntry(e));
    const best=bestSpeedFromEntry(ivEntry);
    html+=cardioCard(lastIntervals, ivEntry, '⚡ Last intervals', best?'best '+best:'');
  }

  html += fiveKCardHtml(p);
  html += hrZonesCardHtml(p);

  if(bw.length>=2){
    html+='<div class="card"><div class="flex-between"><div class="sec-title" style="margin:0">⚖️ Bodyweight trend</div>'
      + '<button class="mini" data-home-go="body">Body →</button></div>'
      + '<div class="chart-box" style="height:150px"><canvas id="homeBwChart"></canvas></div></div>';
  }

  html+='<div class="card"><div class="sec-title">🎯 '+esc(possessive(p))+' goals</div>'
    + (goal ? '<div style="white-space:pre-wrap">'+esc(goal)+'</div>'
            : '<div class="hint" style="margin:0">No goals set yet - add them via the gear menu'+(hasCoaching()?' so coaching can target them':'')+'.</div>')
    + '</div>';

  // Coaching history — every past coach write, so improvement can be tracked over time.
  const chist=(state.coachingLog||[]).filter(e=>e&&e.person===p).sort((a,b)=> (a.id<b.id?1:a.id>b.id?-1:0));
  if(chist.length){
    html+='<details class="card coach-hist"><summary class="sec-title">🧠 Coaching history · '+chist.length+'</summary>'
      + chist.slice(0,15).map(e=>{
          const parts=[];
          if(e.overall) parts.push('<div><b>Overall:</b> '+esc(e.overall)+'</div>');
          if(e.bySession) Object.keys(e.bySession).forEach(k=> parts.push('<div><b>'+esc(k)+':</b> '+esc(e.bySession[k])+'</div>'));
          if(e.byExercise) Object.keys(e.byExercise).forEach(k=> parts.push('<div>'+esc(k)+' - '+esc(e.byExercise[k])+'</div>'));
          return '<div class="hist-entry"><div class="ex-meta">'+esc(e.date||"")+'</div>'+(parts.join('')||'<div class="hint" style="margin:0">(no note)</div>')+'</div>';
        }).join('')
      + '</details>';
  }

  document.getElementById("view").innerHTML=html;

  const go=tab=>switchTab(tab);
  const lb=document.getElementById("homeLogBtn"); if(lb) lb.onclick=()=>go("log");
  document.querySelectorAll("[data-home-go]").forEach(b=>b.onclick=()=>go(b.dataset.homeGo));

  if(bw.length>=2){
    const i=state.people.indexOf(p);
    const dark=document.documentElement.getAttribute("data-theme")==="dark";
    const col=swatchColor(state.colors[i],dark);
    const tickCol=dark?"#9aa3b2":"#697086", gridCol=dark?"rgba(255,255,255,.09)":"rgba(20,30,55,.08)";
    if(homeChart) homeChart.destroy();
    homeChart=new Chart(document.getElementById("homeBwChart"),{
      type:"line",
      data:{labels:bw.map(b=>b.date), datasets:[{data:bw.map(b=>b.kg), borderColor:col, backgroundColor:col, tension:.25, pointRadius:2, spanGaps:true}]},
      options:{responsive:true, maintainAspectRatio:false,
        scales:{x:{ticks:{color:tickCol,maxTicksLimit:6}, grid:{color:gridCol}}, y:{beginAtZero:false, ticks:{color:tickCol}, grid:{color:gridCol}}},
        plugins:{legend:{display:false}}}
    });
  }
}

function renderView(){
  if(!state.people[0] && !state.people[1]){ renderCreateAccount(0); return; }
  // No sessions yet: force Program, since Home/Log/History/Progress all assume
  // a real curSession. Self-corrects the moment a first session is added.
  // No sessions yet: nothing to log, chart or review, so Program is the only
  // useful place. syncTabButtons keeps the bar honest about the redirect -
  // otherwise tapping Session on a blank install lit Session and showed Program.
  if(!state.program.order.length){ activeTab="edit"; syncTabButtons(); }
  if(!state.program.sessions[curSession]) curSession=state.program.order[0];
  if(activeTab==="home") renderHome();
  else if(activeTab==="log") renderLog();
  else if(activeTab==="history") renderHistory();
  else if(activeTab==="progress") renderProgress();
  // "body" is no longer a tab of its own - it's the Body pane of Progress. Kept
  // as a route so an old persisted tab value, or Home's ⚖ arrow, still lands
  // somewhere sensible instead of a blank view.
  else if(activeTab==="body"){ activeTab="progress"; progressPane="body"; renderProgress(); syncTabButtons(); }
  else if(activeTab==="edit") renderEdit();
  else if(activeTab==="help") renderHelp();
}

// Light up whichever bottom-bar button matches the active tab. Separate from
// switchTab because renderView can redirect (body -> progress) after the button
// has already been set, and the Guide has no button at all.
function syncTabButtons(){
  document.querySelectorAll("#tabs button").forEach(function(x){ x.classList.toggle("active", x.dataset.tab===activeTab); });
}
// Switch section. Works even for views without a bottom-bar tab (the Guide,
// reached from Settings). skipCapture is used right after saving, when the
// draft has just been cleared on purpose.
function switchTab(tab, skipCapture){
  if(!skipCapture) captureDraft();
  activeTab=tab;
  syncTabButtons();
  renderView();
}

// Preset account colours - hex values mirror the CSS vars in css/styles.css
// (--me/--partner/--sw-*) so charts + the theme-color meta tag (which Chart.js
// and <meta> need as raw hex, not var()) stay in step with the app's --brand.
const SWATCHES = {
  navy:{light:"#1e3a8a",dark:"#7d9bf5"}, purple:{light:"#7a1fe0",dark:"#b57cff"},
  teal:{light:"#0d7d72",dark:"#4fd8c9"}, rose:{light:"#be185d",dark:"#f472b6"},
  amber:{light:"#a15c00",dark:"#f2b84b"}, green:{light:"#15803d",dark:"#5fd88a"}
};
function swatchColor(key,dark){ const s=SWATCHES[key]||SWATCHES.navy; return dark?s.dark:s.light; }
// Renders/reads a single-select colour-swatch picker (.swatchpick, styled in
// css/styles.css). Shared by the Settings dialog and account creation.
// `takenKey` (the other account's colour, if any) is greyed out and unclickable
// so two accounts on one device can't end up visually indistinguishable.
function renderSwatchPicker(container, selected, takenKey){
  container.innerHTML = Object.keys(SWATCHES).map(function(k){
    const taken = takenKey && k===takenKey;
    return '<button type="button" data-c="'+k+'" class="'+(k===selected?"sel":"")+'"'
      + (taken?' disabled':'') + ' title="'+k.charAt(0).toUpperCase()+k.slice(1)+(taken?" (already used)":"")+'"></button>';
  }).join("");
}
function readSwatchPicker(container){ const b=container.querySelector("button.sel"); return b?b.dataset.c:"navy"; }
// Swatch key for a person by name, used to colour their "pill" badges throughout.
function personSwatch(name){ const i=state.people.indexOf(name); return (i>=0 && state.colors[i]) || "navy"; }
// First swatch key not equal to `excludeKey` - a sensible default pre-selection
// that never collides with the other account's colour.
function firstAvailableSwatch(excludeKey){
  const keys=Object.keys(SWATCHES);
  return keys.find(k=>k!==excludeKey) || keys[0];
}
function wireSwatchPicker(container){
  container.onclick=e=>{
    const b=e.target.closest("button"); if(!b || b.disabled) return;
    container.querySelectorAll("button").forEach(x=>x.classList.remove("sel"));
    b.classList.add("sel");
  };
}
// Address-bar / PWA chrome colour: active person's accent in light, app bg in dark.
function updateMeta(){
  const meta=document.querySelector('meta[name="theme-color"]');
  if(!meta) return;
  const dark=document.documentElement.getAttribute("data-theme")==="dark";
  meta.setAttribute("content", dark ? "#12151c" : swatchColor(state.colors[state.activePerson],false));
}
function applyTheme(t){
  document.documentElement.setAttribute("data-theme", t);
  updateMeta();
  const btn=document.getElementById("themeToggleBtn");
  if(btn){ btn.textContent = t==="dark" ? "☀️ Light mode" : "🌙 Dark mode"; }
}
function initTheme(){
  let t=state.theme;
  if(t!=="light" && t!=="dark"){
    t=(window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) ? "dark" : "light";
  }
  applyTheme(t);
}
function toggleTheme(){
  if(activeTab==="log") captureDraft(); // preserve unsaved entry across the re-render
  const next = document.documentElement.getAttribute("data-theme")==="dark" ? "light" : "dark";
  state.theme=next; save(); applyTheme(next);
  renderView(); // re-render so the themed chart + surfaces refresh
}
document.getElementById("themeToggleBtn").onclick=toggleTheme;

curSession = sessionForDate(curDate) || curSession;
initTheme();
renderPeople();
renderView();
autoSync(); // on open: pull the latest (partner's logs, coach notes) automatically

// Ask the browser to protect this site's storage from automatic eviction under
// storage pressure — relevant for anyone not using cloud sync, since local data
// is the only copy. Best-effort; no UI, nothing to do if unsupported/denied.
if(navigator.storage && navigator.storage.persist) navigator.storage.persist().catch(()=>{});

// Nudge toward a manual backup if it's been a long time (or never) since the
// last Export and there's actually something to lose. Delayed so it doesn't
// collide with the sync-status toast from autoSync() above.
// Skipped entirely when cloud sync is set up: every save already pushes a full
// copy to the GitHub store, so the data IS backed up off-device and the nudge
// was telling you to fix a problem you don't have.
setTimeout(function(){
  if(!state.logs || !state.logs.length) return;
  var sc=loadSync();
  if(sc.repo && sc.token) return;
  var last = state.lastExportAt ? new Date(state.lastExportAt).getTime() : 0;
  var daysSince = (Date.now()-last)/86400000;
  if(daysSince>30) toast("Haven't exported in a while - back up via gear → Export");
}, 4000);

if("serviceWorker" in navigator){
  // Auto-apply new versions. sw.js calls skipWaiting()+clients.claim(), so a
  // freshly deployed version activates instead of waiting for every tab to
  // close; controllerchange then reloads the page so the phone actually runs
  // the new code (an installed PWA otherwise keeps stale JS in memory for
  // ages — which is why fixes seemed not to land). Guarded so the initial
  // claim on a first visit doesn't trigger a reload loop.
  let hadController = !!navigator.serviceWorker.controller, reloadingForUpdate=false;
  navigator.serviceWorker.addEventListener("controllerchange", ()=>{
    if(!hadController){ hadController=true; return; }
    if(reloadingForUpdate) return; reloadingForUpdate=true; window.location.reload();
  });
  window.addEventListener("load", ()=>{
    navigator.serviceWorker.register("sw.js").then(reg=>{ if(reg) reg.update(); });
  });
}

// Show the running app version (the shell cache name, e.g. "tt-v47") in Settings.
function showAppVersion(){
  const el=document.getElementById("appVersion"); if(!el) return;
  if(!window.caches){ el.textContent="-"; return; }
  caches.keys().then(keys=>{
    const v=keys.filter(k=>/^tt-v/.test(k)).sort((a,b)=>
      (parseInt(a.replace(/\D/g,""),10)||0)-(parseInt(b.replace(/\D/g,""),10)||0));
    el.textContent = v.length ? v[v.length-1] : "-";
  }).catch(()=>{ el.textContent="-"; });
}
// Force the newest deployed version: drop the service worker + every cache, then
// reload from the network. This is the reliable escape hatch for an installed
// PWA that keeps serving stale files.
function forceUpdate(){
  const btn=document.getElementById("updateNow"); if(btn){ btn.disabled=true; btn.textContent="Updating…"; }
  const reload=()=>window.location.reload();
  const jobs=[];
  if(navigator.serviceWorker && navigator.serviceWorker.getRegistrations)
    jobs.push(navigator.serviceWorker.getRegistrations().then(rs=>Promise.all(rs.map(r=>r.unregister()))));
  if(window.caches)
    jobs.push(caches.keys().then(ks=>Promise.all(ks.map(k=>caches.delete(k)))));
  Promise.all(jobs).then(reload).catch(reload);
}
const updBtn=document.getElementById("updateNow");
if(updBtn) updBtn.onclick=forceUpdate;
