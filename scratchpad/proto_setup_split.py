"""Prototype splitting setupNote into garminNote + setupNote, against a COPY.

Reads the newest prototype state, splits each run session's single setup note into
its two real halves - the Garmin structured workout (which is now its own field and
its own folded panel) and the treadmill fallback - and writes a new local state file.
The shared store is never opened.

The split point is the "IF IT IS TOO COLD, WET OR DARK" line that already separated
them in prose. Two of the notes then close with an "OUTDOORS IS THE DEFAULT"
paragraph, which is about the outdoor session and would otherwise be stranded inside
the belt fallback, so it moves back to the watch half where it belongs.
"""
import io, json, copy

SRC = 'scratchpad/proto-run-week1.json'
OUT = 'scratchpad/proto-setup-split.json'
MARK = 'IF IT IS TOO COLD, WET OR DARK'
STRAY = 'OUTDOORS IS THE DEFAULT'

data = json.load(io.open(SRC, encoding='utf-8'))
before = copy.deepcopy(data)
sessions = (data.get('program') or {}).get('sessions') or {}

for key, s in sessions.items():
    note = s.get('setupNote') or ''
    if MARK not in note:
        continue
    i = note.index(MARK)
    garmin, belt = note[:i].rstrip(), note[i:].strip()

    # The outdoor paragraph is about the watch session, not the belt one.
    if STRAY in belt:
        j = belt.index(STRAY)
        stray, belt = belt[j:].strip(), belt[:j].rstrip()
        garmin = garmin + '\n\n' + stray

    s['garminNote'] = garmin
    s['setupNote'] = belt
    print('=== %s (%s)' % (s.get('name'), key))
    print('    garminNote %4d chars, starts: %s' % (len(garmin), garmin.split('\n')[0][:64]))
    print('    setupNote  %4d chars, starts: %s' % (len(belt), belt.split('\n')[0][:64]))
    if STRAY in garmin:
        print('    (moved the OUTDOORS IS THE DEFAULT paragraph back to the watch half)')
    # Nothing may be lost in the split.
    a = ''.join(note.split())
    b = ''.join((garmin + belt).split())
    print('    content preserved:', 'YES' if sorted(a) == sorted(b) else 'NO - CHECK')

json.dump(data, io.open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('\nwrote', OUT)
