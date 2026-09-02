# -*- coding: utf-8 -*-
"""Two fixes on top of patch_flex.py.

1. saveSession never copied betterWhen onto the log entry, so every test read as
   lower-is-better and the ankle and active-raise improvements charted as losses.
   Copied alongside load/bwPct/muscles, for the same stated reason: history has
   to stay readable if the exercise is later changed or dropped.
2. The ladder sorted alphabetically, which split the pike tests away from each
   other. Program order groups them, and log entries are already saved in it.

    python scratchpad/patch_flex2.py
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
        sys.exit("!! anchor %r matched %d times (%s)" % (anchor[:70], n, label))
    src = src.replace(anchor, new)
    print("  *", label)


sub(
    "      if(ex.load){ en.load=ex.load; if(ex.bwPct) en.bwPct=ex.bwPct; }",
    u"      if(ex.load){ en.load=ex.load; if(ex.bwPct) en.bwPct=ex.bwPct; }\n"
    u"      // Which way is better travel on a flexibility test. Same reasoning as\n"
    u"      // load above: without it on the entry, an old measurement reads as a\n"
    u"      // gap-to-close the moment the exercise changes or leaves the program.\n"
    u"      if(ex.betterWhen) en.betterWhen=ex.betterWhen;",
    "saveSession copies betterWhen",
)

sub(
    "  return Object.keys(byName).sort().map(n=>byName[n]);",
    u"  // Insertion order, not alphabetical: entries are saved in program order, so\n"
    u"  // this keeps the tests for one skill next to each other in the ladder.\n"
    u"  return order.map(n=>byName[n]);",
    "ladder keeps program order",
)

sub(
    "  const byName={};\n"
    "  state.logs.filter(l=>l.person===person).slice().sort((a,b)=>a.date<b.date?-1:1)",
    u"  const byName={}, order=[];\n"
    u"  state.logs.filter(l=>l.person===person).slice().sort((a,b)=>a.date<b.date?-1:1)",
    "ladder order accumulator",
)

sub(
    "      const rung=byName[e.name]||(byName[e.name]={name:e.name,higher:higher,pts:[]});",
    u"      if(!byName[e.name]){ byName[e.name]={name:e.name,higher:higher,pts:[]}; order.push(e.name); }\n"
    u"      const rung=byName[e.name];\n"
    u"      rung.higher=higher; // the newest log wins if the flag was added later",
    "ladder registers new rungs",
)

if src == orig:
    sys.exit("!! nothing changed")
io.open(APP, "w", encoding="utf-8", newline="").write(src)
print("\nwrote js/app.js  (%+d chars)" % (len(src) - len(orig)))
