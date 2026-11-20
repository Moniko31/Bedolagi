"""Чертёж фланца (лист A4, масштаб 1:1) -> flange_drawing.svg.

Размеры берутся из тех же параметров, что и в flange.py.
Запуск: python3 drawing.py
"""
import math
import os

OUT = os.path.dirname(os.path.abspath(__file__))

# --- параметры детали (как в flange.py), мм ---
D_OUT, D_HUB, D_BORE = 100.0, 50.0, 30.0
T_PLATE, H_HUB = 12.0, 25.0
D_BC, D_BOLT, N_BOLTS = 75.0, 9.0, 4
DENSITY = 7.85e-3  # г/мм3, сталь
MASS_KG = 99048.1 * DENSITY / 1000  # объём из flange.py (FreeCAD)

els = []


def add(s):
    els.append(s)


def line(x1, y1, x2, y2, cls="thin"):
    add(f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" class="{cls}"/>')


def circle(cx, cy, r, cls="thick"):
    add(f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{r:.3f}" class="{cls}"/>')


def text(x, y, s, size=3.5, anchor="middle", extra=""):
    add(f'<text x="{x:.3f}" y="{y:.3f}" font-size="{size}" text-anchor="{anchor}" {extra}>{s}</text>')


def rect(x, y, w, h, cls="thin"):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" class="{cls}"/>')


def dim_h(x1, x2, y, label, ext_from=None, ext_to=None, label_dy=-1.0):
    """Горизонтальный размер; выносные линии идут от ext_from вдоль вертикали до y."""
    if ext_from is not None:
        line(x1, ext_from, x1, y + 1.5 * (1 if y > ext_from else -1), "thin")
        line(x2, ext_from, x2, y + 1.5 * (1 if y > ext_from else -1), "thin")
    add(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" class="dim" marker-start="url(#arr)" marker-end="url(#arr)"/>')
    text((x1 + x2) / 2, y + label_dy, label)


def dim_v(y1, y2, x, label, ext_from=None, rot_dx=-1.2):
    if ext_from is not None:
        s = 1 if x > ext_from else -1
        line(ext_from, y1, x + 1.5 * s, y1, "thin")
        line(ext_from, y2, x + 1.5 * s, y2, "thin")
    add(f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" class="dim" marker-start="url(#arr)" marker-end="url(#arr)"/>')
    ym = (y1 + y2) / 2
    add(f'<text x="{x + rot_dx}" y="{ym}" font-size="3.5" text-anchor="middle" transform="rotate(-90 {x + rot_dx} {ym})">{label}</text>')


# ---------- рамка и основная надпись ----------
rect(0, 0, 297, 210, "sheet")
rect(20, 5, 272, 200, "thick")

SX, SY, SW, SH = 107, 150, 185, 55
rect(SX, SY, SW, SH, "thick")
line(SX, 165, SX + SW, 165, "thin")           # строка обозначения
line(SX, 185, SX + SW, 185, "thin")           # низ: подписи
line(232, 165, 232, 205, "thin")
line(252, 165, 252, 185, "thin")
line(272, 165, 272, 185, "thin")
line(262, 185, 262, 205, "thin")
text(SX + SW / 2, 160.5, "BDL-001", 6, extra='font-weight="bold"')
text(169.5, 168.5, "Наименование", 2.2)
text(169.5, 178.5, "Фланец", 8, extra='font-weight="bold"')
for (xc, lab, val) in [(242, "Масса, кг", f"{MASS_KG:.3f}".replace(".", ",")),
                       (262, "Масштаб", "1:1"),
                       (282, "Материал", "Сталь 45")]:
    text(xc, 168.5, lab, 2.2)
    text(xc, 180, val, 3.5 if len(val) < 8 else 3)
text(247, 196, "Лист 1", 3.5)
text(277, 196, "Листов 1", 3.5)
text(110, 190, "Разработал:", 3, "start")
text(110, 200, "Проверил:", 3, "start")
line(130, 190.5, 170, 190.5, "thin")
line(130, 200.5, 170, 200.5, "thin")

# технические требования
text(23, 136, "Технические требования", 3.5, "start", 'font-weight="bold"')
text(23, 141, "1. Неуказанные предельные отклонения", 3.2, "start")
text(23, 145, "    размеров ±IT14/2.", 3.2, "start")
text(23, 149, "2. Острые кромки притупить.", 3.2, "start")

# ---------- вид сверху ----------
CX, CY = 85, 62
R = D_OUT / 2
circle(CX, CY, R)
circle(CX, CY, D_HUB / 2)
circle(CX, CY, D_BORE / 2)
bc = D_BC / 2
circle(CX, CY, bc, "center")
for i in range(N_BOLTS):
    a = 2 * math.pi * i / N_BOLTS + math.pi / 4
    hx, hy = CX + bc * math.cos(a), CY - bc * math.sin(a)
    circle(hx, hy, D_BOLT / 2)
    line(hx - 6, hy, hx + 6, hy, "center")
    line(hx, hy - 6, hx, hy + 6, "center")
line(CX - R - 6, CY, CX + R + 6, CY, "center")
line(CX, CY - R - 6, CX, CY + R + 6, "center")

# линия разреза A–A по диагонали через два отверстия
d = 62 / math.sqrt(2)
d0 = (R + 2) / math.sqrt(2)
p1 = (CX - d, CY + d)
p2 = (CX + d, CY - d)
line(p1[0], p1[1], CX - d0, CY + d0, "cut")
line(CX + d0, CY - d0, p2[0], p2[1], "cut")
# стрелки направления взгляда (влево-вверх, перпендикулярно линии разреза)
nx, ny = -1 / math.sqrt(2), -1 / math.sqrt(2)
for (px, py) in (p1, p2):
    add(f'<line x1="{px:.3f}" y1="{py:.3f}" x2="{px + nx * 8:.3f}" y2="{py + ny * 8:.3f}" class="dim" marker-end="url(#arr)"/>')
text(p1[0] - 5, p1[1] + 7, "A", 5, extra='font-weight="bold"')
text(p2[0] + 7, p2[1] - 4, "A", 5, extra='font-weight="bold"')

# выноска «4 отв. Ø9»
a45 = math.pi / 4
hx, hy = CX + bc * math.cos(a45), CY - bc * math.sin(a45)
sx, sy = hx + (D_BOLT / 2) * math.cos(a45), hy - (D_BOLT / 2) * math.sin(a45)
line(sx, sy, 142, 15, "thin")
line(142, 15, 178, 15, "thin")
text(160, 13.2, f"{N_BOLTS} отв. Ø{D_BOLT:g}", 3.5)

# ---------- разрез А–А ----------
SCX, Z0 = 210, 72.0          # ось и нижняя плоскость на листе
ZH = Z0 - H_HUB              # верх ступицы
ZP = Z0 - T_PLATE            # верх плиты
ro, rh, rb = D_OUT / 2, D_HUB / 2, D_BORE / 2
rbc, rbh = D_BC / 2, D_BOLT / 2

add('<g class="section">')
for sgn in (-1, 1):
    # внешняя часть плиты (от края до отверстия)
    xa, xb = sgn * ro, sgn * (rbc + rbh)
    add(f'<polygon points="{SCX + xa:.3f},{Z0} {SCX + xb:.3f},{Z0} {SCX + xb:.3f},{ZP} {SCX + xa:.3f},{ZP}" class="cutpoly"/>')
    # внутренняя часть: между отверстием и расточкой, со ступицей
    x1, x2, x3 = sgn * (rbc - rbh), sgn * rh, sgn * rb
    pts = [(x1, Z0), (x3, Z0), (x3, ZH), (x2, ZH), (x2, ZP), (x1, ZP)]
    add('<polygon points="' + " ".join(f"{SCX + x:.3f},{y:.3f}" for x, y in pts) + '" class="cutpoly"/>')
add('</g>')

# оси отверстий и детали
for sgn in (-1, 1):
    xc = SCX + sgn * rbc
    line(xc, ZH - 5, xc, Z0 + 5, "center")
line(SCX, ZH - 8, SCX, Z0 + 8, "center")
text(SCX, Z0 + 33, "А–А", 5, extra='font-weight="bold"')

# размеры
dim_v(ZH, Z0, SCX - ro - 12, f"{H_HUB:g}", ext_from=SCX - rh)       # 25
dim_v(ZP, Z0, SCX + ro + 10, f"{T_PLATE:g}", ext_from=SCX + ro)      # 12
dim_h(SCX - ro, SCX + ro, Z0 + 14, f"Ø{D_OUT:g}", ext_from=Z0)
dim_h(SCX - rbc, SCX + rbc, Z0 + 23, f"{D_BC:g}", ext_from=Z0 + 5)
dim_h(SCX - rh, SCX + rh, ZH - 9, f"Ø{D_HUB:g}", ext_from=ZH)
dim_h(SCX - rb, SCX + rb, ZH + 8, f"Ø{D_BORE:g}")

# ---------- сборка SVG ----------
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 297 210" font-family="Arial, Helvetica, sans-serif" font-style="italic">
<defs>
  <marker id="arr" viewBox="0 0 10 6" refX="10" refY="3" markerWidth="3.2" markerHeight="1.9" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,0 L10,3 L0,6 z" fill="#000"/></marker>
  <pattern id="hatch" width="2" height="2" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="2" stroke="#000" stroke-width="0.25"/></pattern>
  <style>
    .sheet {{ fill:#fff; stroke:none }}
    .thick {{ fill:none; stroke:#000; stroke-width:0.7 }}
    .thin  {{ fill:none; stroke:#000; stroke-width:0.25 }}
    .dim   {{ fill:none; stroke:#000; stroke-width:0.25 }}
    .center{{ fill:none; stroke:#000; stroke-width:0.25; stroke-dasharray:8 1.5 1.5 1.5 }}
    .cut   {{ fill:none; stroke:#000; stroke-width:0.9 }}
    .cutpoly {{ fill:url(#hatch); stroke:#000; stroke-width:0.7; stroke-linejoin:round }}
    text {{ fill:#000 }}
  </style>
</defs>
<rect width="297" height="210" fill="#fff"/>
{chr(10).join(els)}
</svg>
'''
path = os.path.join(OUT, "flange_drawing.svg")
with open(path, "w", encoding="utf-8") as f:
    f.write(svg)
print("written", path, "mass kg", round(MASS_KG, 3))
