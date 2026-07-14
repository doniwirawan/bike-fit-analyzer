"""Generate web/og.png — the 1200x630 social preview card. Run from repo root: python tools/make-og.py"""
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
BG, CARD, FG, MUT, LINE, GRID = "#ffffff", "#ffffff", "#0e1620", "#59647a", "#dbe1ea", "#eef1f6"
ACCENT, GREEN, AMBER, RED = "#1f6feb", "#16a34a", "#d97706", "#dc2626"

F = "C:/Windows/Fonts/"
sans_b = lambda s: ImageFont.truetype(F + "segoeuib.ttf", s)
sans = lambda s: ImageFont.truetype(F + "segoeui.ttf", s)
mono_b = lambda s: ImageFont.truetype(F + "consolab.ttf", s)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

# clinical grid backdrop
for x in range(0, W, 40):
    d.line([(x, 0), (x, H)], fill=GRID)
for y in range(0, H, 40):
    d.line([(0, y), (W, y)], fill=GRID)


def tracked(xy, text, font, fill, track):
    """Draw text with letter-spacing (Pillow has none). Returns end x."""
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + track
    return x


PAD = 72

# brand lockup
logo = Image.open("web/logo.png").convert("RGBA").resize((60, 60), Image.LANCZOS)
img.paste(logo, (PAD, 62), logo)
tracked((PAD + 76, 78), "BIKE FIT ANALYZER", mono_b(23), FG, 3.2)

# headline
d.text((PAD, 178), "Grade your bike fit", font=sans_b(76), fill=FG)
d.text((PAD, 262), "in your browser.", font=sans_b(76), fill=FG)

# subhead
d.text((PAD, 372), "Drop a clip of yourself pedaling and get every", font=sans(30), fill=MUT)
d.text((PAD, 412), "joint angle graded — nothing leaves your device.", font=sans(30), fill=MUT)

# chips
cx = PAD
for label, col in [("100% ON-DEVICE", GREEN), ("NO UPLOAD", GREEN), ("FREE", GREEN)]:
    f = mono_b(18)
    w = sum(d.textlength(c, font=f) + 2.4 for c in label)
    d.rounded_rectangle([cx, 496, cx + w + 40, 540], 8, fill=CARD, outline=LINE, width=2)
    d.ellipse([cx + 16, 514, cx + 24, 522], fill=col)
    tracked((cx + 32, 507), label, f, MUT, 2.4)
    cx += w + 54

# right: mini graded readout, the thing the product actually outputs
PX, PY, PW = 792, 168, 336
d.rounded_rectangle([PX, PY, PX + PW, PY + 300], 18, fill=CARD, outline=LINE, width=2)
tracked((PX + 26, PY + 26), "FIT REPORT", mono_b(17), MUT, 2.6)

rows = [("KNEE EXT", "146°", GREEN), ("HIP ANGLE", "52°", GREEN), ("BACK", "38°", AMBER), ("ELBOW", "171°", RED)]
ry = PY + 72
for name, val, col in rows:
    d.text((PX + 26, ry + 6), name, font=mono_b(19), fill=MUT)
    vf = sans_b(30)
    d.text((PX + PW - 26 - d.textlength(val, font=vf) - 26, ry - 2), val, font=vf, fill=FG)
    d.rounded_rectangle([PX + PW - 42, ry + 2, PX + PW - 26, ry + 28], 5, fill=col)
    ry += 54
    if name != rows[-1][0]:
        d.line([(PX + 26, ry - 12), (PX + PW - 26, ry - 12)], fill=GRID, width=2)

# footer url
uf = mono_b(21)
d.text((PAD, H - 60), "bikefit.doniwirawan.xyz", font=uf, fill=ACCENT)

# accent rule along the top edge
d.rectangle([0, 0, W, 6], fill=ACCENT)

img.save("web/og.png", optimize=True)
print("wrote web/og.png", img.size)
