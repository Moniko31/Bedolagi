"""DJ DIZEL — мультяшный паровозик в облаке дыма.

Генерирует векторный исходник (SVG, весь текст переведён в кривые) и
экспорт: EPS, PDF (открывается в Illustrator), JPG 3000x3000 px @300 dpi.

Запуск:  python build.py   (нужны cairosvg, fonttools, pillow)
"""
import io
import math
import random
from pathlib import Path

import cairosvg
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FONT = HERE / "fonts" / "LuckiestGuy-Regular.ttf"
OUT = ROOT / "exports"

W = H = 3000
S = 22  # толщина основного контура

C = dict(
    ink="#161616",
    green="#2EA64B",
    green_d="#1B7434",
    green_l="#79D36A",
    gold="#F4C84A",
    red="#E2271E",
    red_d="#9E1612",
    steel="#3A3D42",
    steel_l="#8A9099",
    glass="#DDF0F8",
    glass_d="#9CC9DC",
    smoke="#FFFFFF",
    smoke_d="#D3DAE2",
    ground="#E4E7EB",
)

parts: list[str] = []


def add(s: str) -> None:
    parts.append(s)


def st(fill, sw=S, extra=""):
    return (f'fill="{fill}" stroke="{C["ink"]}" stroke-width="{sw}" '
            f'stroke-linejoin="round" stroke-linecap="round" {extra}')


def rivets(points, r=9, fill=None):
    fill = fill or C["green_d"]
    for x, y in points:
        add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"/>')


def wheel(cx, cy, r, spokes=10):
    add(f'<circle cx="{cx}" cy="{cy}" r="{r}" {st(C["steel"])}/>')
    rin = r * 0.80
    add(f'<circle cx="{cx}" cy="{cy}" r="{rin}" {st(C["red"], S * 0.7)}/>')
    # светлый блик на шине
    add(f'<path d="M{cx - r * 0.62},{cy - r * 0.62} A{r * 0.88},{r * 0.88} 0 0 1 '
        f'{cx + r * 0.2},{cy - r * 0.86}" fill="none" stroke="{C["steel_l"]}" '
        f'stroke-width="{r * 0.07}" stroke-linecap="round"/>')
    for i in range(spokes):
        a = 2 * math.pi * i / spokes + 0.15
        x1, y1 = cx + math.cos(a) * r * 0.22, cy + math.sin(a) * r * 0.22
        x2, y2 = cx + math.cos(a) * rin * 0.93, cy + math.sin(a) * rin * 0.93
        add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{C["red_d"]}" stroke-width="{max(10, r * 0.075):.1f}" stroke-linecap="round"/>')
    add(f'<circle cx="{cx}" cy="{cy}" r="{rin * 0.93}" fill="none" stroke="{C["red_d"]}" stroke-width="{r * 0.05}"/>')
    add(f'<circle cx="{cx}" cy="{cy}" r="{r * 0.24}" {st(C["red"], S * 0.7)}/>')
    add(f'<circle cx="{cx}" cy="{cy}" r="{r * 0.09}" fill="{C["ink"]}"/>')


# ---------------------------------------------------------------- фон
add(f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>')
add('<g id="art" transform="translate(0 220)">')

# ---------------------------------------------------------------- поезд (группа с наклоном)
TILT, PIV = -3.0, (1500, 2250)
add(f'<g transform="rotate({TILT} {PIV[0]} {PIV[1]})">')

RAIL = 2335
# тень
add(f'<ellipse cx="1480" cy="{RAIL + 40}" rx="1330" ry="55" fill="{C["ground"]}"/>')
# шпалы
for i, x in enumerate(range(140, 2900, 130)):
    fade = min(1, (x - 100) / 400, (2900 - x) / 400)
    v = round(0x16 + (255 - 0x16) * (1 - max(fade, 0)))  # без прозрачности: EPS остаётся чисто векторным
    add(f'<path d="M{x - 40},{RAIL + 70} L{x + 30},{RAIL - 5}" stroke="#{v:02x}{v:02x}{v:02x}" '
        f'stroke-width="18" stroke-linecap="round"/>')
# рельс
add(f'<path d="M120,{RAIL + 8} L2880,{RAIL + 8}" stroke="{C["ink"]}" stroke-width="34" stroke-linecap="round"/>')
add(f'<path d="M140,{RAIL + 3} L2860,{RAIL + 3}" stroke="{C["steel_l"]}" stroke-width="8" stroke-linecap="round"/>')
add(f'<path d="M180,{RAIL + 60} L2820,{RAIL + 60}" stroke="#8C8C8C" stroke-width="14" stroke-linecap="round"/>')

# --- вагон ---------------------------------------------------------
add(f'<rect x="230" y="1985" width="930" height="95" rx="20" {st(C["ink"])}/>')
add(f'<path d="M190,1400 L1190,1400 L1180,2000 L200,2000 Z" {st(C["green"])}/>')
add(f'<path d="M205,1860 L1175,1860 L1180,2000 L200,2000 Z" fill="{C["green_d"]}"/>')
add(f'<path d="M190,1400 L1190,1400 L1180,2000 L200,2000 Z" fill="none" stroke="{C["ink"]}" stroke-width="{S}" stroke-linejoin="round"/>')
# крыша
add(f'<path d="M150,1420 Q690,1215 1230,1420 Z" {st(C["green_d"])}/>')
add(f'<path d="M400,1372 Q690,1290 980,1372" fill="none" stroke="{C["green_l"]}" stroke-width="14" stroke-linecap="round"/>')
add(f'<rect x="140" y="1405" width="1100" height="50" rx="22" {st(C["green"])}/>')
# окна
for wx in (290, 520, 750, 980):
    add(f'<path d="M{wx - 80},1720 L{wx - 80},1560 Q{wx},1470 {wx + 80},1560 L{wx + 80},1720 Z" {st(C["glass"])}/>')
    add(f'<path d="M{wx - 60},1700 L{wx - 60},1640 L{wx + 60},1640 L{wx + 60},1700 Z" fill="{C["glass_d"]}"/>')
    add(f'<path d="M{wx - 35},1700 L{wx + 40},1575" stroke="#FFFFFF" stroke-width="20" stroke-linecap="round"/>')
    add(f'<path d="M{wx - 80},1720 L{wx - 80},1560 Q{wx},1470 {wx + 80},1560 L{wx + 80},1720 Z" fill="none" stroke="{C["ink"]}" stroke-width="{S}" stroke-linejoin="round"/>')
# золотые полосы
add(f'<rect x="200" y="1770" width="980" height="34" rx="10" {st(C["gold"], 12)}/>')
add(f'<rect x="590" y="1880" width="200" height="70" rx="10" {st(C["gold"], 12)}/>')
rivets([(x, 1835) for x in range(240, 1170, 70)])
rivets([(x, 1980) for x in range(240, 1170, 70)])
# сцепка
add(f'<path d="M1150,2035 L1300,2035" stroke="{C["ink"]}" stroke-width="34" stroke-linecap="round"/>')
add(f'<rect x="1195" y="2012" width="60" height="46" rx="12" {st(C["red"], 12)}/>')
wheel(410, 2190, 140)
wheel(960, 2190, 140)

# --- паровоз ---------------------------------------------------------
# рама
add(f'<rect x="1250" y="1920" width="1300" height="150" rx="30" {st(C["ink"])}/>')
# метельник (скотоотбрасыватель)
add(f'<path d="M2470,1975 L2610,1975 L2810,2305 L2470,2305 Z" {st(C["red"])}/>')
for t in (0.2, 0.42, 0.64, 0.86):
    x_top = 2470 + 140 * t
    x_bot = 2470 + 340 * t
    add(f'<path d="M{x_top:.0f},1995 L{x_bot:.0f},2290" stroke="{C["ink"]}" stroke-width="14" stroke-linecap="round"/>')
add(f'<rect x="2440" y="1935" width="200" height="70" rx="16" {st(C["red"])}/>')

# котёл
add(f'<rect x="1640" y="1440" width="790" height="500" rx="70" {st(C["green"])}/>')
add(f'<path d="M1660,1830 L2410,1830 L2410,1870 Q2410,1925 2355,1925 L1715,1925 Q1660,1925 1660,1870 Z" fill="{C["green_d"]}"/>')
add(f'<path d="M1720,1492 L2340,1492" stroke="{C["green_l"]}" stroke-width="22" stroke-linecap="round"/>')
add(f'<rect x="1640" y="1440" width="790" height="500" rx="70" fill="none" stroke="{C["ink"]}" stroke-width="{S}"/>')
for bx in (1850, 2080):
    add(f'<rect x="{bx}" y="1440" width="44" height="500" {st(C["gold"], 12)}/>')
    rivets([(bx + 22, y) for y in range(1490, 1920, 60)], r=7, fill="#B38B1E")
# дымовая коробка (перед котла)
add(f'<rect x="2360" y="1405" width="150" height="555" rx="40" {st(C["green_d"])}/>')
add(f'<ellipse cx="2525" cy="1682" rx="70" ry="250" {st(C["green"])}/>')
add(f'<ellipse cx="2538" cy="1682" rx="34" ry="160" {st(C["green_d"], 14)}/>')
rivets([(2400, y) for y in range(1450, 1930, 60)], r=8, fill=C["ink"])
# сухопарник
add(f'<path d="M1900,1450 L1900,1380 Q1960,1300 2020,1380 L2020,1450 Z" {st(C["green"])}/>')
add(f'<rect x="1880" y="1430" width="160" height="34" rx="10" {st(C["gold"], 12)}/>')
# прожектор
add(f'<rect x="2400" y="1280" width="130" height="120" rx="20" {st(C["green_d"])}/>')
add(f'<circle cx="2500" cy="1340" r="38" {st(C["gold"], 14)}/>')
add(f'<circle cx="2490" cy="1330" r="12" fill="#FFFFFF"/>')
add(f'<rect x="2445" y="1390" width="40" height="30" {st(C["ink"], 10)}/>')
# труба
add(f'<path d="M2150,1450 L2172,1250 L2100,1010 L2340,1010 L2268,1250 L2290,1450 Z" {st(C["green"])}/>')
add(f'<path d="M2246,1440 L2255,1250 L2310,1030" fill="none" stroke="{C["green_d"]}" stroke-width="40" stroke-linecap="round"/>')
add(f'<path d="M2185,1240 L2125,1040" stroke="{C["green_l"]}" stroke-width="18" stroke-linecap="round"/>')
add(f'<path d="M2150,1450 L2172,1250 L2100,1010 L2340,1010 L2268,1250 L2290,1450 Z" fill="none" stroke="{C["ink"]}" stroke-width="{S}" stroke-linejoin="round"/>')
add(f'<rect x="2150" y="1235" width="140" height="30" rx="8" {st(C["gold"], 12)}/>')
add(f'<path d="M2070,1015 L2370,1015 L2350,945 Q2220,905 2090,945 Z" {st(C["ink"])}/>')
add(f'<rect x="2130" y="1425" width="180" height="40" rx="12" {st(C["green_d"], 14)}/>')

# будка машиниста
add(f'<path d="M1235,1190 L1655,1190 L1675,1960 L1215,1960 Z" {st(C["green"])}/>')
add(f'<path d="M1222,1840 L1670,1840 L1675,1960 L1215,1960 Z" fill="{C["green_d"]}"/>')
add(f'<path d="M1235,1190 L1655,1190 L1675,1960 L1215,1960 Z" fill="none" stroke="{C["ink"]}" stroke-width="{S}" stroke-linejoin="round"/>')
add(f'<rect x="1300" y="1290" width="290" height="300" rx="34" {st(C["gold"], S)}/>')
add(f'<rect x="1328" y="1318" width="234" height="244" rx="22" {st(C["glass"], 14)}/>')
add(f'<path d="M1340,1550 L1340,1470 L1550,1470 L1550,1550 Z" fill="{C["glass_d"]}"/>')
add(f'<path d="M1380,1520 L1480,1350" stroke="#FFFFFF" stroke-width="24" stroke-linecap="round"/>')
add(f'<rect x="1328" y="1318" width="234" height="244" rx="22" fill="none" stroke="{C["ink"]}" stroke-width="14"/>')
add(f'<rect x="1230" y="1660" width="440" height="36" rx="10" {st(C["gold"], 12)}/>')
add(f'<rect x="1360" y="1735" width="170" height="70" rx="10" {st(C["gold"], 12)}/>')
rivets([(x, 1235) for x in range(1280, 1630, 60)])
rivets([(x, 1940) for x in range(1260, 1660, 60)])
# крыша будки
add(f'<path d="M1170,1215 Q1180,1110 1300,1100 L1650,1100 Q1735,1105 1740,1180 L1740,1225 L1170,1225 Z" {st(C["green_d"])}/>')
add(f'<path d="M1240,1150 L1660,1150" stroke="{C["green_l"]}" stroke-width="16" stroke-linecap="round"/>')

# цилиндр и дышло
add(f'<rect x="2220" y="1890" width="230" height="140" rx="36" {st(C["green"])}/>')
add(f'<rect x="2240" y="1945" width="190" height="20" fill="{C["gold"]}"/>')
wheel(1430, 2145, 190)
wheel(1830, 2145, 190)
wheel(2175, 2210, 125)
wheel(2410, 2210, 125)
add(f'<path d="M1430,2215 L1830,2215" stroke="{C["ink"]}" stroke-width="54" stroke-linecap="round"/>')
add(f'<path d="M1430,2215 L1830,2215" stroke="{C["steel_l"]}" stroke-width="26" stroke-linecap="round"/>')
add(f'<path d="M1830,2215 L2290,1965" stroke="{C["ink"]}" stroke-width="46" stroke-linecap="round"/>')
add(f'<path d="M1830,2215 L2290,1965" stroke="{C["steel_l"]}" stroke-width="20" stroke-linecap="round"/>')
for x in (1430, 1830):
    add(f'<circle cx="{x}" cy="2215" r="24" {st(C["gold"], 12)}/>')

# линии скорости
for y, x0, x1 in ((1500, 20, 140), (1650, -40, 150), (1800, 30, 150)):
    add(f'<path d="M{x0},{y} L{x1},{y}" stroke="{C["ink"]}" stroke-width="18" stroke-linecap="round"/>')
add('</g>')


# ---------------------------------------------------------------- облако дыма
def rot(x, y):
    a = math.radians(TILT)
    dx, dy = x - PIV[0], y - PIV[1]
    return (PIV[0] + dx * math.cos(a) - dy * math.sin(a),
            PIV[1] + dx * math.sin(a) + dy * math.cos(a))


chx, chy = rot(2220, 880)
random.seed(7)
puffs = []
CX, CY, RX, RY = 1300, 560, 1020, 300
n = 22
for i in range(n):
    t = 2 * math.pi * i / n
    r = 175 + random.uniform(-30, 45)
    puffs.append((CX + math.cos(t) * RX, CY + math.sin(t) * RY, r))
puffs.append((CX, CY, None))  # центральный эллипс
# цепочка клубов от трубы к облаку
for (fx, fy, r) in ((0, 0, 60), (-40, -85, 90), (-130, -180, 125)):
    puffs.append((chx + fx, chy + fy, r))


def puff_shape(x, y, r, grow=0.0, dx=0, dy=0, **attrs):
    a = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    if r is None:
        return f'<ellipse cx="{x + dx}" cy="{y + dy}" rx="{RX + grow}" ry="{RY + grow}" {a}/>'
    return f'<circle cx="{x + dx:.1f}" cy="{y + dy:.1f}" r="{r + grow:.1f}" {a}/>'


add('<g id="smoke">')
for p in puffs:  # внешний контур (общий для всех клубов)
    add(puff_shape(*p, grow=S, fill=C["ink"]))
for p in puffs:  # тень снизу
    add(puff_shape(*p, fill=C["smoke_d"]))
for p in puffs:  # белая масса, сдвинута вверх
    add(puff_shape(*p, grow=-34, dx=-14, dy=-30, fill=C["smoke"]))
# пара отдельных колечек дыма
for x, y, r in ((2560, 330, 52), (2700, 210, 34)):
    add(f'<circle cx="{x}" cy="{y}" r="{r}" {st(C["smoke"], 18)}/>')
add('</g>')

# ---------------------------------------------------------------- надпись в кривых
font = TTFont(FONT)
gs = font.getGlyphSet()
cmap = font.getBestCmap()
upm = font["head"].unitsPerEm
TEXT = "DJ DIZEL"
SIZE = 430
k = SIZE / upm
glyphs = [cmap[ord(ch)] for ch in TEXT]
adv = [gs[g].width * k for g in glyphs]
track = 18
total = sum(adv) + track * (len(TEXT) - 1)
tx, ty = CX - 20, CY + 150  # базовая линия
ARCH = 70


def letter_path(g):
    pen = SVGPathPen(gs)
    gs[g].draw(TransformPen(pen, (k, 0, 0, -k, 0, 0)))
    return pen.getCommands()


letters = []
x = tx - total / 2
for ch, g, a in zip(TEXT, glyphs, adv):
    if ch != " ":
        mid = x + a / 2
        t = (mid - tx) / (total / 2)
        dy = -ARCH * (1 - t * t)
        ang = math.degrees(math.atan(2 * ARCH * t / (total / 2)))
        tr = f'translate({x:.1f} {ty + dy:.1f}) rotate({ang:.2f} {a / 2:.1f} 0) skewX(-6)'
        letters.append((tr, letter_path(g)))
    x += a + track

add('<g id="logo">')
for tr, d in letters:  # «объём» — смещённая тень
    add(f'<path transform="translate(18 24) {tr}" d="{d}" fill="{C["ink"]}" stroke="{C["ink"]}" stroke-width="60" stroke-linejoin="round"/>')
for tr, d in letters:
    add(f'<path transform="{tr}" d="{d}" fill="{C["ink"]}" stroke="{C["ink"]}" stroke-width="56" stroke-linejoin="round"/>')
for tr, d in letters:
    add(f'<path transform="{tr}" d="{d}" fill="{C["red"]}"/>')
for tr, d in letters:  # блик сверху
    add(f'<path transform="translate(-6 -8) {tr}" d="{d}" fill="none" stroke="#FF8A7A" stroke-width="8" '
        f'stroke-dasharray="40 900" stroke-linecap="round"/>')
add('</g>')
add('</g>')

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
       f'viewBox="0 0 {W} {H}">\n<title>DJ DIZEL</title>\n' + "\n".join(parts) + "\n</svg>\n")

OUT.mkdir(exist_ok=True)
(OUT / "dj-dizel.svg").write_text(svg, encoding="utf-8")
cairosvg.svg2eps(bytestring=svg.encode(), write_to=str(OUT / "dj-dizel.eps"))
cairosvg.svg2pdf(bytestring=svg.encode(), write_to=str(OUT / "dj-dizel.pdf"))
png = cairosvg.svg2png(bytestring=svg.encode(), output_width=W, output_height=H)
Image.open(io.BytesIO(png)).convert("RGB").save(
    OUT / "dj-dizel_3000x3000.jpg", quality=95, dpi=(300, 300), subsampling=0)
Image.open(io.BytesIO(png)).convert("RGB").resize((900, 900), Image.LANCZOS).save(
    OUT / "dj-dizel_preview.png")
print("ok")
