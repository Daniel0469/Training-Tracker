# -*- coding: utf-8 -*-
"""Show that a program proposal is waiting, without having to expand anything.

Nine proposals landed on the Mobility assessment and Daniel could not see any of
them until he opened the session - the cards only render inside an expanded one.
Two marks fix that at the two points you would actually look:

  * a count on each collapsed session row, so the Program tab reads as an index
    of what needs attention rather than a list you have to open one by one;
  * a dot on the Program tab itself, so a proposal is visible from anywhere in
    the app rather than only once you have already gone looking.

    python scratchpad/patch_pending_mark.py
"""
import io, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, "..", "js", "app.js")
CSS = os.path.join(HERE, "..", "css", "styles.css")


def patch(path, edits):
    src = io.open(path, encoding="utf-8").read()
    orig = src
    for anchor, new, label in edits:
        n = src.count(anchor)
        if n != 1:
            sys.exit("!! %s: anchor matched %d times (%s)" % (os.path.basename(path), n, label))
        src = src.replace(anchor, new)
        print("  *", label)
    if src == orig:
        sys.exit("!! nothing changed in " + path)
    io.open(path, "w", encoding="utf-8", newline="").write(src)


patch(APP, [
    # 1. Every pending change on a session, whatever kind. changesAddingTo only
    #    covers adds, which would undercount a session holding an edit or a
    #    removal - exactly the ones worth not missing.
    (
        "function sessionKeyByName(name){",
        u"function changesForSession(sessionName){\n"
        u"  return pendingChanges().filter(c=> c.session===sessionName);\n"
        u"}\n"
        u"function sessionKeyByName(name){",
        "changesForSession helper",
    ),
    # 2. The count on the collapsed row.
    (
        "        + '<span class=\"sess-title\"><span class=\"sess-name\">'+esc(s.name)+'</span>'",
        u"        + '<span class=\"sess-title\"><span class=\"sess-name\">'+esc(s.name)\n"
        u"          // Visible while the session is SHUT: the proposal cards themselves only\n"
        u"          // render once it is open, which is how nine of them went unnoticed.\n"
        u"          + (pendingHere?' <span class=\"sess-flag\">'+pendingHere+' waiting</span>':\"\")\n"
        u"          + '</span>'",
        "count on the collapsed session row",
    ),
    (
        "    const n=s.exercises.length;",
        u"    const n=s.exercises.length;\n"
        u"    const pendingHere=changesForSession(s.name).length;",
        "count computed per session",
    ),
    # 3. The dot on the Program tab, so it is visible from anywhere.
    (
        '  document.querySelectorAll("#tabs button").forEach(function(x){ x.classList.toggle("active", x.dataset.tab===activeTab); });',
        u'  document.querySelectorAll("#tabs button").forEach(function(x){ x.classList.toggle("active", x.dataset.tab===activeTab); });\n'
        u'  // A proposal changes what you are told to do next session, so it should be\n'
        u'  // visible without going looking for it. The dot rides the Program tab because\n'
        u'  // that is where the change is accepted.\n'
        u'  const progTab=document.querySelector(\'#tabs button[data-tab="edit"]\');\n'
        u'  if(progTab) progTab.classList.toggle("has-pending", pendingChanges().length>0);',
        "dot on the Program tab",
    ),
    # 4. Applying or declining a proposal re-renders this tab rather than switching
    #    to it, so without this the dot would linger after the last one was cleared.
    (
        "  document.getElementById(\"view\").innerHTML=html;\n"
        "  document.querySelectorAll(\"[data-sesstoggle]\").forEach(b=>b.onclick=()=>{",
        u"  document.getElementById(\"view\").innerHTML=html;\n"
        u"  syncTabButtons(); // the count just changed if we got here from apply/decline\n"
        u"  document.querySelectorAll(\"[data-sesstoggle]\").forEach(b=>b.onclick=()=>{",
        "dot refreshes after apply/decline",
    ),
    # 5. Guide.
    (
        u"A proposal to <b>remove</b> an exercise is marked in red - your past logs of it are kept either way, removing it only stops it being prescribed.')",
        u"A proposal to <b>remove</b> an exercise is marked in red - your past logs of it are kept either way, removing it only stops it being prescribed.')"
        u"\n     +p('<b>You don\\'t have to go looking.</b> While anything is waiting, the <b>Program</b> tab carries a dot, and each session that has proposals on it shows a <b>waiting</b> count on its row while it is still closed - so you can see which session to open rather than opening all of them. Both clear themselves as soon as the last proposal on them is applied or declined.')",
        "Guide paragraph",
    ),
])

patch(CSS, [
    (
        "  .pill{font-size:11px;font-weight:700;padding:2px 8px;border-radius:20px}",
        u"  .pill{font-size:11px;font-weight:700;padding:2px 8px;border-radius:20px}\n"
        u"  /* \"3 waiting\" on a collapsed session row. Brand-soft on brand so it reads in\n"
        u"     both themes without hardcoding a colour. */\n"
        u"  .sess-flag{display:inline-block;vertical-align:middle;margin-left:7px;font-size:11px;\n"
        u"    font-weight:700;padding:2px 8px;border-radius:20px;\n"
        u"    background:var(--brand-soft);color:var(--brand);white-space:nowrap}",
        "sess-flag style",
    ),
    (
        "  .tabs button.active{background:var(--brand-soft);color:var(--brand)}",
        u"  .tabs button.active{background:var(--brand-soft);color:var(--brand)}\n"
        u"  /* Dot on the Program tab while a proposal is waiting. Positioned rather than\n"
        u"     appended so it never reflows the label or widens the bar. */\n"
        u"  .tabs button.has-pending{position:relative}\n"
        u"  .tabs button.has-pending::after{content:\"\";position:absolute;top:10px;right:10px;\n"
        u"    width:8px;height:8px;border-radius:50%;background:var(--brand)}",
        "Program tab dot style",
    ),
])

# The service worker is cache-first, so without this bump nobody gets either mark.
SW = os.path.join(HERE, "..", "sw.js")
sw = io.open(SW, encoding="utf-8").read()
if "tt-v118" not in sw:
    sys.exit("!! expected tt-v118 in sw.js")
io.open(SW, "w", encoding="utf-8", newline="").write(sw.replace("tt-v118", "tt-v119", 1))
print("  * CACHE_NAME -> tt-v119")
