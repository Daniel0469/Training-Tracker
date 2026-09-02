# -*- coding: utf-8 -*-
"""Add flexibility-test support to js/app.js.

Three things: a type predicate (isFlexTest) so a centimetre measurement is never
mistaken for a load, a guard so those measurements stay out of session volume,
and a Flexibility pane in Progress that reads the tests as a ladder.

    python scratchpad/patch_flex.py
"""
import io, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, "..", "js", "app.js")
src = io.open(APP, encoding="utf-8").read()
orig = src


def sub(anchor, new, label):
    global src
    n = src.count(anchor)
    if n != 1:
        sys.exit("!! anchor %r matched %d times (%s)" % (anchor[:60], n, label))
    src = src.replace(anchor, new)
    print("  *", label)


# 1. The predicate. Lives with isLifting/isRunning because it is the same kind of
#    thing: the columns are what say which sort of exercise this is.
sub(
    "// Which exercises offer an RPE rating. Effort is worth rating on anything you",
    u'''// A flexibility test measures a distance in centimetres - the gap from your
// fingertips to the floor, how far your foot sits from the wall - rather than a
// load. It is never a lifting entry, so it stays off the records table, out of
// session volume and off the Lifts chart, where a gap plotted on an axis
// labelled "Top-set weight" would be worse than no chart at all.
function isFlexTest(ex){ return /^cm$/i.test(String((ex.cols||[])[0]||"").trim()) && !isLifting(ex); }
// Most tests are a gap you want to close. Ankle range is the exception: the
// further your foot sits from the wall, the more dorsiflexion you have.
function flexBetterHigher(ex){ return !!ex && ex.betterWhen==="higher"; }

// Which exercises offer an RPE rating. Effort is worth rating on anything you''',
    "isFlexTest / flexBetterHigher",
)

# 2. Keep centimetres out of session volume. Deliberately narrow: other
#    non-lifting entries (the lunges, Weight x Distance) have always counted
#    towards volume, and changing that is a separate decision for Daniel.
sub(
    "  entries.forEach(function(en){ var wu=en.warmup||[]; en.rows.forEach(function(r,ri){"
    " if(wu.indexOf(ri)>=0) return; var w=setLoad(en, r[0], person, date), reps=parseInt(r[1],10);"
    " if(!isNaN(w)&&!isNaN(reps)) volume+=w*reps; }); });",
    u"  // Both columns of a flexibility test hold numbers, so without this gate a\n"
    u"  // 12cm gap logged beside an 8cm one would add 96kg of phantom volume.\n"
    u"  entries.forEach(function(en){ if(isFlexTest(en)) return; var wu=en.warmup||[]; en.rows.forEach(function(r,ri){"
    u" if(wu.indexOf(ri)>=0) return; var w=setLoad(en, r[0], person, date), reps=parseInt(r[1],10);"
    u" if(!isNaN(w)&&!isNaN(reps)) volume+=w*reps; }); });",
    "volume guard",
)

# 3. Flexibility tests get their own pane, so they leave the Lifts picker alone.
sub(
    "  const allEx=[...new Set(state.logs.flatMap(l=>(l.entries||[]).map(e=>e.name)))].sort();",
    u"  // Centimetres, not kilograms: these chart in the Flexibility pane instead.\n"
    u"  const allEx=[...new Set(state.logs.flatMap(l=>(l.entries||[]).filter(e=>!isFlexTest(e))"
    u".map(e=>e.name)))].sort();",
    "Lifts picker excludes flex tests",
)

sub(
    u'const PANE_LABELS={lifts:"\U0001f3cb Lifts", run:"\U0001f3c3 Run", time:"⏱ Time", body:"⚖ Body"};',
    u'const PANE_LABELS={lifts:"\U0001f3cb Lifts", run:"\U0001f3c3 Run", flex:"\U0001f938 Flexibility",'
    u' time:"⏱ Time", body:"⚖ Body"};',
    "PANE_LABELS.flex",
)

sub(
    '  if(hasRunData()) keys.push("run");\n  if(hasDurationData()) keys.push("time");',
    u'  if(hasRunData()) keys.push("run");\n  if(hasFlexData()) keys.push("flex");\n'
    u'  if(hasDurationData()) keys.push("time");',
    "flex pane gated on data",
)

sub(
    '  if(progressPane==="time") return renderTime();',
    u'  if(progressPane==="flex") return renderFlex();\n  if(progressPane==="time") return renderTime();',
    "flex pane dispatch",
)

sub("let chart=null;", u"let chart=null;\nlet flexChart=null;", "flexChart handle")

sub(
    'let timeSession="";           // "" = every session',
    u'let timeSession="";           // "" = every session\n'
    u'let flexTest="";              // which flexibility test the ladder chart is showing',
    "flexTest selection",
)

# 4. The pane itself, sitting next to the Time pane it is modelled on.
FLEX = u'''// ---- Flexibility ------------------------------------------------------------
// Tests are logged in centimetres and read as a ladder: every rung you have
// measured, where it sits now, and which way it has moved since the first time.
// The method this follows says the lowest rung is the only thing worth training,
// so the job of the table is to make the low one findable - not to celebrate the
// high ones.
function hasFlexData(){
  return state.logs.some(l=>l && (l.entries||[]).some(e=>isFlexTest(e)));
}
// One rung per test name, oldest measurement first. A per-side test puts both
// sides in one entry as two rows; the ladder reports the WORSE side, because
// that is the side actually limiting the skill.
function flexHistory(person){
  const byName={};
  state.logs.filter(l=>l.person===person).slice().sort((a,b)=>a.date<b.date?-1:1)
    .forEach(l=>(l.entries||[]).forEach(e=>{
      if(!isFlexTest(e)) return;
      const vals=(e.rows||[]).map(r=>parseFloat(r[0])).filter(v=>!isNaN(v));
      if(!vals.length) return;
      const higher=flexBetterHigher(e);
      const v=higher?Math.min.apply(null,vals):Math.max.apply(null,vals);
      const rung=byName[e.name]||(byName[e.name]={name:e.name,higher:higher,pts:[]});
      rung.pts.push({date:l.date,v:v});
    }));
  return Object.keys(byName).sort().map(n=>byName[n]);
}
function renderFlex(){
  const p=state.people[state.activePerson];
  const hist=flexHistory(p);
  const names=hist.map(h=>h.name);
  // A test can go away under you when the active person changes, the same way
  // timeSession can - see renderTime.
  if(flexTest && names.indexOf(flexTest)<0) flexTest="";
  if(!flexTest && names.length) flexTest=names[0];
  let html=progressTabsHtml();
  if(!hist.length){
    html+='<div class="card empty">No flexibility tests logged for '+esc(p)+' yet.<br>'
      + 'Run the <b>Mobility assessment</b> session and your ladder appears here.</div>';
    document.getElementById("view").innerHTML=html;
    wirePaneToggle();
    return;
  }
  html+='<div class="card"><div class="sec-title">&#129692; Flexibility ladder - '+esc(p)+'</div>'
    + '<div class="hint" style="margin-bottom:10px">Your lowest rung is what limits the skill - '
    + 'that is the one to train, not whichever stretch you feel the most. A test done on both '
    + 'sides reports the worse side.</div>'
    + '<div class="sets-wrap"><table class="rec"><thead><tr><th>Test</th><th>Now</th>'
    + '<th>Change</th><th>Measured</th></tr></thead><tbody>'
    + hist.map(function(h){
        const first=h.pts[0], last=h.pts[h.pts.length-1];
        const d=Math.round((last.v-first.v)*10)/10;
        const better=h.higher? d>0 : d<0;
        let change;
        if(h.pts.length<2) change='<span class="ex-meta">baseline</span>';
        else if(d===0) change='<span class="ex-meta">no change</span>';
        else change='<span style="color:var('+(better?"--good":"--bad")+')">'
          + (d>0?"&#9650;":"&#9660;")+Math.abs(d)+' cm</span>';
        return '<tr><td>'+esc(h.name)
          + (h.higher?' <span class="ex-meta">(higher is better)</span>':"")
          + '</td><td><b>'+(Math.round(last.v*10)/10)+' cm</b></td><td>'+change
          + '</td><td class="ex-meta">'+relTime(last.date)+'</td></tr>';
      }).join("")
    + '</tbody></table></div></div>';
  html+='<div class="card">'
    + '<div class="row" style="margin-bottom:12px">'
    + '<label class="fld grow" style="max-width:280px">Test<select id="flexTest">'
    + names.map(n=>'<option'+(n===flexTest?' selected':'')+'>'+esc(n)+'</option>').join("")
    + '</select></label></div>'
    + '<div class="hint" style="margin-bottom:10px">Both people, every time you have measured it.</div>'
    + '<div class="chart-box"><canvas id="flexChart"></canvas></div></div>';
  document.getElementById("view").innerHTML=html;
  wirePaneToggle();
  document.getElementById("flexTest").onchange=e=>{ flexTest=e.target.value; renderFlex(); };
  drawFlexChart();
}
function drawFlexChart(){
  const dark=document.documentElement.getAttribute("data-theme")==="dark";
  const series=state.people.map(function(p,i){
    const h=flexHistory(p).filter(x=>x.name===flexTest)[0];
    return {label:p, data:(h?h.pts:[]).map(pt=>({x:pt.date,y:Math.round(pt.v*10)/10})),
      borderColor:swatchColor(state.colors[i],dark),backgroundColor:swatchColor(state.colors[i],dark),
      tension:.25,spanGaps:true};
  });
  if(flexChart) flexChart.destroy();
  const tickCol=dark?"#9aa3b2":"#697086";
  const gridCol=dark?"rgba(255,255,255,.09)":"rgba(20,30,55,.08)";
  flexChart=new Chart(document.getElementById("flexChart"),{
    type:"line", data:{datasets:series},
    options:{responsive:true,maintainAspectRatio:false,parsing:false,
      scales:{x:{type:"category",labels:[...new Set(state.logs.map(l=>l.date))].sort(),
          ticks:{color:tickCol},grid:{color:gridCol}},
        y:{beginAtZero:false,title:{display:true,text:"cm",color:tickCol},
          ticks:{color:tickCol},grid:{color:gridCol}}},
      plugins:{legend:{position:"top",labels:{color:tickCol}}}}
  });
}
function renderTime(){'''

sub("function renderTime(){", FLEX, "renderFlex / drawFlexChart / flexHistory")

if src == orig:
    sys.exit("!! nothing changed")
io.open(APP, "w", encoding="utf-8", newline="").write(src)
print("\nwrote js/app.js  (%+d chars)" % (len(src) - len(orig)))
