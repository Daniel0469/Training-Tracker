"""Design v3 PWA icons: the dumbbell line mark (the same path as the Session tab
icon, ICONS.dumbbell in js/app.js) drawn with Pillow at 4x and downsampled.

    python scratchpad/make_icons.py preview   # option sheet -> scratchpad/icon-v3-options.png
    python scratchpad/make_icons.py A         # write icons/ for option A (or B / C)
"""
import os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BG = (0x12, 0x14, 0x17)          # --bg (dark)
BLUE = (0x7D, 0x9B, 0xF5)        # navy swatch, dark value
PURPLE = (0xB5, 0x7C, 0xFF)      # purple swatch, dark value
INK = (0xEC, 0xED, 0xEE)         # --ink

# The 24-unit line icon: bar, two plates, two collars.
# Bar first, so the plates sit over its ends.
SEGS = [((6.5, 12), (17.5, 12)), ((6.5, 6.5), (6.5, 17.5)), ((17.5, 6.5), (17.5, 17.5)),
        ((3.5, 9), (3.5, 15)), ((20.5, 9), (20.5, 15))]

OPTIONS = {
    # name: (background, colour per segment, description)
    "A": (BG, [BLUE] * 5, "Blue mark on the dark page colour"),
    "B": (BLUE, [BG] * 5, "Dark mark on a blue tile (like Create account)"),
    "C": (BG, [INK, BLUE, PURPLE, BLUE, PURPLE], "Two-person: blue and purple ends, light bar"),
}

def draw(opt, size, content):
    """content = fraction of the canvas the 24-unit icon box spans."""
    bg, cols, _ = OPTIONS[opt]
    S = size * 4
    im = Image.new("RGB", (S, S), bg)
    d = ImageDraw.Draw(im)
    box = S * content
    off = (S - box) / 2
    k = box / 24.0
    w = 2.4 * k                   # a touch heavier than the 2px UI stroke, for a small icon
    for (a, b), c in zip(SEGS, cols):
        p1 = (off + a[0] * k, off + a[1] * k); p2 = (off + b[0] * k, off + b[1] * k)
        d.line([p1, p2], fill=c, width=int(round(w)))
        r = int(round(w)) / 2 - .5   # match the line's whole-pixel width
        for (x, y) in (p1, p2):   # round caps
            d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    return im.resize((size, size), Image.LANCZOS)

def write(opt):
    out = os.path.join(ROOT, "icons")
    draw(opt, 192, .74).save(os.path.join(out, "icon-192.png"))
    draw(opt, 512, .74).save(os.path.join(out, "icon-512.png"))
    # Maskable: Android may crop to a circle of 80% - keep the mark well inside it.
    draw(opt, 512, .56).save(os.path.join(out, "icon-512-maskable.png"))
    draw(opt, 180, .70).save(os.path.join(out, "apple-touch-icon.png"))
    print("wrote icons/ for option", opt)

def preview():
    """One sheet: each option at 180 (rounded like iOS), 60 and 40 px, plus the
    maskable crop as a circle, on the dark page colour."""
    W, H = 3 * 300 + 40, 330
    sheet = Image.new("RGB", (W, H), (0x1B, 0x1E, 0x22))
    for i, opt in enumerate("ABC"):
        x0 = 20 + i * 300
        big = draw(opt, 180, .70)
        m = Image.new("L", (180, 180), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, 179, 179], 40, fill=255)
        sheet.paste(big, (x0 + 20, 20), m)
        for j, s in enumerate((60, 40)):
            sm = draw(opt, s, .74)
            mm = Image.new("L", (s, s), 0); ImageDraw.Draw(mm).rounded_rectangle([0, 0, s - 1, s - 1], s * .22, fill=255)
            sheet.paste(sm, (x0 + 20 + j * 75, 220), mm)
        mk = draw(opt, 80, .56)
        cm = Image.new("L", (80, 80), 0); ImageDraw.Draw(cm).ellipse([0, 0, 79, 79], fill=255)
        sheet.paste(mk, (x0 + 175, 210), cm)
        ImageDraw.Draw(sheet).text((x0 + 20, 300), opt + ": " + OPTIONS[opt][2], fill=(0x9B, 0xA1, 0xA8))
    p = os.path.join(HERE, "icon-v3-options.png")
    sheet.save(p); print("wrote", p)

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "preview"
    preview() if arg == "preview" else write(arg)
