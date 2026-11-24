"""«Мой сосед сверху» — вертикальный мультфильм в стиле reference_frame_01.png.
python render.py frame <t> <out.png> | python render.py sheet | python render.py video
"""
import math, os, random, subprocess, sys
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import timeline as TLM
from timeline import SHOTS, TOTAL, talk, line_at, mood, shot_at

W, H, SS, FPS = 1080, 1920, 2, 30
OUT = (17, 17, 20)
LW = 7
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_fonts = {}
def font(sz):
    k = max(8, int(sz * SS))
    if k not in _fonts: _fonts[k] = ImageFont.truetype(FONT_B, k)
    return _fonts[k]

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def back(x):
    x = clamp(x); c = 1.7
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def lerp(a, b, x): return a + (b - a) * x
def mix(c1, c2, x): return tuple(int(lerp(a, b, x)) for a, b in zip(c1, c2))

# персонажи
MAX = dict(skin=(222, 168, 124), hair=(132, 78, 36), shirt=(58, 126, 68), collar=(44, 100, 54))
VERA = dict(skin=(238, 194, 162), hair=(58, 36, 32), shirt=(232, 116, 106), collar=(200, 90, 84))
APRON = (250, 206, 84)
FLOUR = (250, 248, 240)

class Cv:
    def __init__(s, bg):
        s.im = Image.new("RGBA", (W * SS, H * SS), bg + (255,)); s.d = ImageDraw.Draw(s.im)
    def P(s, *v): return [int(x * SS) for x in v]
    def ell(s, cx, cy, rx, ry, fill, ol=OUT, w=LW):
        s.d.ellipse(s.P(cx - rx, cy - ry, cx + rx, cy + ry), fill=fill, outline=ol if w else None, width=int(w * SS))
    def rect(s, x0, y0, x1, y1, fill, ol=OUT, w=LW, r=0):
        if x1 <= x0 or y1 <= y0: return
        r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
        s.d.rounded_rectangle(s.P(x0, y0, x1, y1), radius=int(r * SS), fill=fill, outline=ol if w else None, width=int(w * SS))
    def poly(s, pts, fill, ol=OUT, w=LW):
        pp = [(x * SS, y * SS) for x, y in pts]
        s.d.polygon(pp, fill=fill)
        if w and ol: s.d.line(pp + [pp[0]], fill=ol, width=int(w * SS), joint="curve")
    def line(s, pts, col, w=LW):
        s.d.line([(x * SS, y * SS) for x, y in pts], fill=col, width=int(w * SS), joint="curve")
    def tube(s, pts, col, wd, L=LW):
        """рука-«трубка» как в референсе: контур + заливка + круглые концы"""
        s.line(pts, OUT, wd + 2 * L)
        for x, y in (pts[0], pts[-1]): s.ell(x, y, wd / 2 + L, wd / 2 + L, OUT, w=0)
        s.line(pts, col, wd)
        for x, y in (pts[0], pts[-1]): s.ell(x, y, wd / 2, wd / 2, col, w=0)
    def arc(s, cx, cy, rx, ry, a0, a1, col=OUT, w=5):
        s.d.arc(s.P(cx - rx, cy - ry, cx + rx, cy + ry), a0, a1, fill=col, width=int(w * SS))
    def text(s, x, y, txt, sz, fill=(255, 255, 255), stroke=0, sc=OUT, anchor="mm"):
        s.d.text((x * SS, y * SS), txt, font=font(sz), fill=fill, anchor=anchor,
                 stroke_width=int(stroke * SS), stroke_fill=sc)
    def tsize(s, txt, sz):
        b = s.d.textbbox((0, 0), txt, font=font(sz)); return (b[2] - b[0]) / SS, (b[3] - b[1]) / SS
    def soft(s, items, blur=0):
        """полупрозрачные пятна: items = [(kind, coords, rgba)]"""
        lay = Image.new("RGBA", s.im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for kind, c, col in items:
            if kind == "e": d.ellipse(s.P(c[0] - c[2], c[1] - c[3], c[0] + c[2], c[1] + c[3]), fill=col)
            elif kind == "p": d.polygon([(x * SS, y * SS) for x, y in c], fill=col)
            elif kind == "r": d.rectangle(s.P(*c), fill=col)
        if blur: lay = lay.filter(ImageFilter.GaussianBlur(blur * SS))
        s.im = Image.alpha_composite(s.im, lay); s.d = ImageDraw.Draw(s.im)

# ---------------- персонаж анфас ----------------
def char(cv, who, x, y, sc=1.0, md="neutral", tk=0.0, t=0.0, look=0.0, arms="down", apron=False, flour=0,
         hand=None, bottom=H + 80):
    P = MAX if who == "M" else VERA
    R = 150 * sc; L = LW * max(0.6, sc)
    sk, sh = P["skin"], P["shirt"]
    tw = R * 1.45; ty0 = y + R * 0.88
    hands = {}
    # длинные волосы сзади
    if who == "F":
        cv.poly([(x - R * 1.12, y - R * 0.3), (x - R * 0.9, y - R * 1.0), (x, y - R * 1.2), (x + R * 0.9, y - R * 1.0),
                 (x + R * 1.12, y - R * 0.3), (x + R * 1.3, y + R * 1.7), (x + R * 0.9, y + R * 1.95), (x, y + R * 1.6),
                 (x - R * 0.9, y + R * 1.95), (x - R * 1.3, y + R * 1.7)], P["hair"], w=L)
    sway = math.sin(t * 2.1) * 0.04
    def arm_down(side):
        sx, sy = x + side * tw * 0.84, ty0 + R * 0.42
        ex, ey = sx + side * R * (0.25 + sway), sy + R * 1.6
        cv.tube([(sx, sy), (ex, ey)], sh, R * 0.46, L); cv.ell(ex, ey + R * 0.12, R * 0.22, R * 0.24, sk, w=L)
    front = []
    for side in (-1, 1):
        mode = arms if isinstance(arms, str) else arms[0 if side < 0 else 1]
        if mode == "down": arm_down(side)
        else: front.append((side, mode))
    # торс
    cv.rect(x - tw, ty0, x + tw, bottom, sh, w=L, r=R * 0.7)
    if apron:
        cv.line([(x - R * 0.55, ty0 + R * 0.05), (x - R * 0.35, ty0 + R * 0.6)], APRON, L * 2.2)
        cv.line([(x + R * 0.55, ty0 + R * 0.05), (x + R * 0.35, ty0 + R * 0.6)], APRON, L * 2.2)
        cv.rect(x - R * 0.85, ty0 + R * 0.55, x + R * 0.85, bottom, APRON, w=L, r=R * 0.2)
        cv.rect(x - R * 0.4, ty0 + R * 1.25, x + R * 0.4, ty0 + R * 1.75, mix(APRON, (200, 140, 40), 0.4), w=L * 0.7, r=R * 0.08)
        if flour:
            for fx, fy, fr in ((-0.5, 0.95, 0.12), (0.35, 1.1, 0.09), (-0.1, 2.0, 0.14), (0.55, 1.9, 0.08)):
                cv.ell(x + R * fx, ty0 + R * fy, R * fr, R * fr * 0.8, FLOUR, w=0)
    cv.ell(x, ty0 + 2, R * 0.5, R * 0.2, P["collar"], w=L)
    # руки спереди
    for side, mode in front:
        sx, sy = x + side * tw * 0.84, ty0 + R * 0.42
        if mode == "knock":
            k = abs(math.sin(t * 9)) if hand is None else 0
            ex, ey = x + side * R * 2.1, y + R * (0.1 + 0.25 * k)
            mxp, myp = sx + side * R * 0.7, sy + R * 0.7
            cv.tube([(sx, sy), (mxp, myp), (ex, ey)], sh, R * 0.46, L)
            cv.ell(ex, ey, R * 0.26, R * 0.26, sk, w=L); hands[side] = (ex, ey)
        elif mode == "reach":
            ex, ey = hand
            mxp, myp = lerp(sx, ex, 0.5), max(sy, ey) + R * 0.35
            cv.tube([(sx, sy), (mxp, myp), (ex, ey)], sh, R * 0.46, L)
            cv.ell(ex, ey, R * 0.26, R * 0.3, sk, w=L); hands[side] = (ex, ey)
        elif mode == "hold":
            ex, ey = x + side * R * 0.55, ty0 + R * 1.55
            cv.tube([(sx, sy), (sx + side * R * 0.15, ey - R * 0.2), (ex, ey)], sh, R * 0.46, L)
            cv.ell(ex, ey, R * 0.24, R * 0.22, sk, w=L); hands[side] = (ex, ey)
        elif mode == "stir":
            a = t * 7
            ex, ey = x + side * R * 0.2 + math.cos(a) * R * 0.25, ty0 + R * 1.25 + math.sin(a) * R * 0.1
            cv.tube([(sx, sy), (sx + side * R * 0.25, ey + R * 0.1), (ex, ey)], sh, R * 0.46, L)
            cv.ell(ex, ey, R * 0.24, R * 0.22, sk, w=L); hands[side] = (ex, ey)
        elif mode == "egg":
            ex, ey = x + side * R * 1.15, y + R * (0.55 + 0.06 * math.sin(t * 5))
            cv.tube([(sx, sy), (sx + side * R * 0.5, sy + R * 0.9), (ex, ey)], sh, R * 0.46, L)
            cv.ell(ex, ey - R * 0.3, R * 0.17, R * 0.22, (252, 246, 232), w=L * 0.8)
            cv.ell(ex, ey, R * 0.24, R * 0.22, sk, w=L); hands[side] = (ex, ey)
    # уши
    if who == "M":
        for side in (-1, 1): cv.ell(x + side * R * 0.95, y + R * 0.1, R * 0.18, R * 0.24, sk, w=L)
    cv.ell(x, y, R, R * 1.05, sk, w=L)
    if who == "M":
        pts = [(x - R * 1.0, y - R * 0.05), (x - R * 0.98, y - R * 0.7), (x - R * 0.5, y - R * 1.05), (x - R * 0.15, y - R * 1.6),
               (x + R * 0.05, y - R * 1.05), (x + R * 0.35, y - R * 1.55), (x + R * 0.45, y - R * 1.0), (x + R * 0.95, y - R * 0.75),
               (x + R * 1.0, y - R * 0.05), (x + R * 0.8, y - R * 0.4), (x + R * 0.55, y - R * 0.32), (x + R * 0.35, y - R * 0.55),
               (x + R * 0.1, y - R * 0.35), (x - R * 0.12, y - R * 0.58), (x - R * 0.35, y - R * 0.36), (x - R * 0.6, y - R * 0.55),
               (x - R * 0.8, y - R * 0.3)]
        cv.poly(pts, P["hair"], w=L)
    else:
        pts = [(x - R * 1.04, y + R * 0.35), (x - R * 1.0, y - R * 0.55), (x - R * 0.55, y - R * 1.02), (x, y - R * 1.12),
               (x + R * 0.55, y - R * 1.02), (x + R * 1.0, y - R * 0.55), (x + R * 1.04, y + R * 0.35), (x + R * 0.86, y - R * 0.2),
               (x + R * 0.62, y - R * 0.36), (x + R * 0.42, y - R * 0.3), (x + R * 0.2, y - R * 0.4), (x, y - R * 0.33),
               (x - R * 0.22, y - R * 0.42), (x - R * 0.45, y - R * 0.32), (x - R * 0.68, y - R * 0.4), (x - R * 0.86, y - R * 0.2)]
        cv.poly(pts, P["hair"], w=L)
        cv.ell(x - R * 0.98, y + R * 0.42, R * 0.06, R * 0.06, (240, 210, 120), w=L * 0.5)   # серёжка
        cv.ell(x + R * 0.98, y + R * 0.42, R * 0.06, R * 0.06, (240, 210, 120), w=L * 0.5)
    face(cv, x, y, R, md, L, t, tk, look, who)
    if flour:
        cv.ell(x - R * 0.5, y + R * 0.45, R * 0.16, R * 0.11, FLOUR, w=0)
        cv.ell(x + R * 0.25, y - R * 0.55, R * 0.12, R * 0.08, FLOUR, w=0)
        if flour > 1: cv.ell(x + R * 0.55, y + R * 0.35, R * 0.13, R * 0.09, FLOUR, w=0)
    return hands

def face(cv, x, y, R, md, L, t, tk, look, who):
    ew = L * 0.8
    blink = (t % 3.7) < 0.12
    lx = look * R * 0.07
    # брови
    def brows(lo, li):   # смещение внешнего / внутреннего конца (в R), + вниз
        for sd in (-1, 1):
            cv.line([(x + sd * R * 0.58, y - R * (0.3 - lo)), (x + sd * R * 0.18, y - R * (0.3 - li))], OUT, ew * 1.5)
    if md in ("angry", "determined"): brows(-0.04, 0.1)
    elif md in ("sad", "guilty"): brows(0.08, -0.06)
    elif md in ("panic", "surprised"): brows(-0.12, -0.14)
    elif md == "suspicious":
        cv.line([(x - R * 0.58, y - R * 0.27), (x - R * 0.18, y - R * 0.22)], OUT, ew * 1.5)
        cv.arc(x + R * 0.37, y - R * 0.33, R * 0.2, R * 0.12, 200, 340, OUT, ew * 1.5)
    elif md == "offended": brows(0.0, 0.06)
    elif md == "sleepy": brows(0.06, 0.06)
    else:
        cv.arc(x - R * 0.37, y - R * 0.24, R * 0.2, R * 0.1, 200, 340, OUT, ew * 1.4)
        cv.arc(x + R * 0.37, y - R * 0.24, R * 0.2, R * 0.1, 200, 340, OUT, ew * 1.4)
    # глаза
    for sd in (-1, 1):
        ex, ey = x + sd * R * 0.37, y + R * 0.04
        if md == "sleepy" and tk < 0.05 or md == "offended" or blink:
            cv.arc(ex, ey - R * 0.02, R * 0.15, R * 0.1, 20, 160, OUT, ew * 1.3)       # закрыты, как в референсе
        elif md in ("sleepy", "deadpan", "suspicious"):
            cv.ell(ex + lx, ey + R * 0.03, R * 0.07, R * 0.06, OUT, w=0)
            cv.line([(ex - R * 0.15, ey - R * 0.02), (ex + R * 0.15, ey - R * 0.02)], OUT, ew * 1.3)
        elif md in ("panic", "surprised"):
            cv.ell(ex, ey, R * 0.15, R * 0.17, (255, 255, 255), w=ew)
            cv.ell(ex + lx, ey + R * 0.02, R * 0.065, R * 0.075, OUT, w=0)
        elif md == "happy" and tk < 0.05:
            cv.arc(ex, ey + R * 0.06, R * 0.15, R * 0.12, 200, 340, OUT, ew * 1.3)
        else:
            cv.ell(ex + lx, ey, R * 0.075, R * 0.095, OUT, w=0)
            cv.ell(ex + lx + R * 0.025, ey - R * 0.03, R * 0.022, R * 0.022, (255, 255, 255), w=0)
        if who == "F" and md not in ("sleepy",):
            cv.line([(ex + sd * R * 0.12, ey - R * 0.08), (ex + sd * R * 0.2, ey - R * 0.14)], OUT, ew)   # ресницы
    if who == "F" or md in ("happy",):
        for sd in (-1, 1): cv.ell(x + sd * R * 0.56, y + R * 0.36, R * 0.13, R * 0.07, (240, 150, 140), w=0)
    cv.arc(x + R * 0.02, y + R * 0.22, R * 0.08, R * 0.12, 100, 280, OUT, ew)   # нос-крючок
    my = y + R * 0.58
    if tk > 0.06:
        h = R * (0.05 + 0.2 * tk)
        cv.ell(x, my, R * (0.17 + 0.05 * tk), h, (110, 30, 40), w=L * 0.8)
        if h > R * 0.1: cv.ell(x, my + h * 0.5, R * 0.1, h * 0.35, (232, 120, 128), w=0)
    elif md in ("sleepy", "surprised", "panic"):
        cv.ell(x, my, R * 0.08, R * 0.1, (110, 30, 40), w=L * 0.7)            # «о» как у спящего в референсе
        cv.ell(x, my + R * 0.04, R * 0.04, R * 0.03, (232, 120, 128), w=0)
    elif md == "happy":
        cv.d.chord(cv.P(x - R * 0.3, my - R * 0.2, x + R * 0.3, my + R * 0.2), 0, 180, fill=(110, 30, 40), outline=OUT, width=int(L * 0.8 * SS))
    elif md == "smirk":
        cv.line([(x - R * 0.2, my), (x + R * 0.1, my + R * 0.02), (x + R * 0.24, my - R * 0.08)], OUT, ew * 1.2)
    elif md in ("sad", "offended", "guilty"):
        cv.arc(x, my + R * 0.1, R * 0.18, R * 0.1, 200, 340, OUT, ew * 1.2)
    else:
        cv.line([(x - R * 0.16, my), (x + R * 0.16, my)], OUT, ew * 1.2)

# ---------------- реквизит ----------------
def cake_burnt(cv, x, y, s=1.0, t=0.0):
    cv.ell(x, y + 70 * s, 260 * s, 60 * s, (235, 235, 240), w=LW)
    cv.ell(x, y + 62 * s, 200 * s, 42 * s, (215, 215, 222), w=3)
    cv.rect(x - 170 * s, y - 80 * s, x + 170 * s, y + 60 * s, (40, 30, 28), w=LW, r=30 * s)
    cv.ell(x, y - 80 * s, 170 * s, 40 * s, (55, 42, 38), w=LW)
    for i, (dx, dy) in enumerate(((-90, -80), (40, -88), (100, -70), (-20, -70))):
        cv.line([(x + dx * s, y + dy * s), (x + (dx + 25) * s, y + (dy + 10) * s)], (90, 70, 60), 4)
    for dx in (-120, -40, 60, 130): cv.line([(x + dx * s, y - 50 * s), (x + (dx + 10) * s, y + 40 * s)], (25, 18, 16), 5)

def smoke(cv, x, y, t, n=7, spread=120, col=(150, 150, 160), alpha=110, speed=60, size=1.0):
    it = []
    for i in range(n):
        ph = (t * speed / 300 + i / n) % 1
        sx = x + math.sin(i * 2.3 + t * 1.3) * spread * (0.3 + ph)
        sy = y - ph * 420 * size
        r = (40 + 110 * ph) * size
        it.append(("e", (sx, sy, r, r * 0.85), col + (int(alpha * (1 - ph) * min(1, ph * 6)),)))
    cv.soft(it, blur=6)

def cake_nice(cv, x, y, s=1.0, t=0.0, lit=True):
    cv.ell(x, y + 95 * s, 290 * s, 60 * s, (245, 245, 250), w=LW)
    cv.rect(x - 200 * s, y - 40 * s, x + 200 * s, y + 90 * s, (250, 226, 200), w=LW, r=26 * s)
    cv.rect(x - 170 * s, y - 160 * s, x + 170 * s, y - 30 * s, (250, 226, 200), w=LW, r=24 * s)
    for yy, ww in ((-40, 200), (-160, 170)):
        pts = [(x - ww * s, (y + yy + 10) * 1)]
        for k in range(9):
            px = x - ww * s + k * ww * 2 * s / 8
            pts.append((px, y + (yy + 28 + 16 * (k % 2)) * s))
        pts += [(x + ww * s, y + (yy + 10) * s), (x + ww * s, y + (yy - 6) * s), (x - ww * s, y + (yy - 6) * s)]
        cv.poly(pts, (244, 140, 170), w=LW * 0.7)
    for i in range(5):
        cv.ell(x + (-120 + i * 60) * s, y - 168 * s, 17 * s, 17 * s, (210, 30, 60), w=4)
    cv.text(x, y + 35 * s, "С ЮБИЛЕЕМ, МАМА", 30 * s, (180, 60, 90))
    for i in range(3):
        cx = x + (-60 + i * 60) * s
        cv.rect(cx - 9 * s, y - 250 * s, cx + 9 * s, y - 175 * s, [(120, 180, 240), (250, 250, 250), (250, 200, 80)][i], w=4)
        if lit:
            f = 1 + 0.15 * math.sin(t * 18 + i)
            cv.ell(cx, y - 272 * s, 12 * s * f, 22 * s * f, (255, 200, 60), w=3)

def sparkles(cv, x, y, t, n=10, rad=320, col=(255, 236, 160)):
    for i in range(n):
        a = i * 2.4 + t * 0.6
        r = rad * (0.6 + 0.4 * math.sin(i * 1.7 + t * 2))
        px, py = x + math.cos(a) * r, y + math.sin(a) * r * 0.7
        k = 0.5 + 0.5 * math.sin(t * 6 + i * 1.3)
        s = 10 + 14 * k
        cv.poly([(px, py - s), (px + s * 0.3, py - s * 0.3), (px + s, py), (px + s * 0.3, py + s * 0.3),
                 (px, py + s), (px - s * 0.3, py + s * 0.3), (px - s, py), (px - s * 0.3, py - s * 0.3)], col, w=0)

def door(cv, x0, y0, x1, y1, col, num=None, open_=0.0, inside=(30, 24, 22)):
    """дверь; open_ 0..1 — створка уходит вправо внутрь (сужается)"""
    cv.rect(x0 - 26, y0 - 26, x1 + 26, y1, (70, 56, 50), w=LW)
    cv.rect(x0, y0, x1, y1, inside, w=LW)
    w = (x1 - x0) * (1 - 0.85 * ease(open_))
    cv.poly([(x1 - w, y0 + 10 * open_), (x1, y0), (x1, y1), (x1 - w, y1 - 10 * open_)], col, w=LW)
    if open_ < 0.6:
        cx = x1 - w
        cv.rect(cx + w * 0.2, y0 + 120, cx + w * 0.8, y0 + 460, mix(col, OUT, 0.15), w=4, r=8)
        cv.rect(cx + w * 0.2, y0 + 520, cx + w * 0.8, y1 - 80, mix(col, OUT, 0.15), w=4, r=8)
        cv.ell(cx + w * 0.12, (y0 + y1) / 2 + 40, 16, 16, (230, 196, 90), w=4)
        if num: cv.text(cx + w * 0.5, y0 + 70, num, 56, (236, 206, 120), stroke=3)

def wall(cv, col, y_floor, floor=(86, 64, 52), stripes=True):
    cv.rect(0, 0, W, y_floor, col, w=0)
    if stripes:
        for xx in range(0, W, 90): cv.rect(xx, 0, xx + 45, y_floor, mix(col, (0, 0, 0), 0.05), w=0)
    cv.rect(0, y_floor, W, H, floor, w=0)
    cv.rect(0, y_floor - 22, W, y_floor, mix(floor, (255, 255, 255), 0.15), w=LW)
    for xx in range(-200, W + 200, 160):
        cv.line([(xx, y_floor), (xx - 260, H)], mix(floor, (0, 0, 0), 0.2), 4)

def clock(cv, x, y, r, hh, mm):
    cv.ell(x, y, r, r, (250, 248, 240), w=LW)
    for k in range(12):
        a = k * math.pi / 6
        cv.line([(x + math.cos(a) * r * 0.78, y + math.sin(a) * r * 0.78), (x + math.cos(a) * r * 0.9, y + math.sin(a) * r * 0.9)], OUT, 4)
    am = math.radians(mm * 6 - 90); ah = math.radians((hh % 12 + mm / 60) * 30 - 90)
    cv.line([(x, y), (x + math.cos(ah) * r * 0.5, y + math.sin(ah) * r * 0.5)], OUT, 9)
    cv.line([(x, y), (x + math.cos(am) * r * 0.75, y + math.sin(am) * r * 0.75)], OUT, 6)
    cv.ell(x, y, 8, 8, OUT, w=0)

# ---------------- сцены ----------------
def beat(T):  # удары баса сверху (122 bpm), пока музыка соседки не выключена
    return max(0.0, 1 - ((T * 122 / 60) % 1) * 4)

def sc_bed(cv, t, d, T):
    """как в референсе: кровать сверху, ночь, телефон 03:12"""
    cv.rect(0, 0, W, H, (24, 26, 40), w=0)
    cv.rect(-20, 70, W + 20, H + 40, (66, 46, 40), w=LW)                       # рама кровати
    cv.rect(20, 110, W - 20, H + 40, (176, 196, 226), w=LW, r=30)              # простыня
    cv.rect(150, 140, 940, 560, (196, 214, 238), w=LW, r=60)                   # подушка
    cv.rect(180, 170, 910, 530, (196, 214, 238), ol=(140, 160, 190), w=3, r=50)
    cv.ell(545, 360, 270, 150, (166, 186, 214), w=0)
    md = mood("M", T, "sleepy")
    tk = talk("M", T)
    lift = ease((T - TLM.TL[1]["start"] + 0.3) / 0.3) if T > TLM.TL[1]["start"] - 0.3 else 0
    char(cv, "M", 500, 370 - 40 * lift, 1.12, md, tk, t, bottom=H + 80)
    # одеяло
    by = 760
    cv.poly([(20, by), (300, by - 30), (700, by + 10), (W - 20, by - 25), (W - 20, H + 40), (20, H + 40)], (40, 64, 120), w=LW)
    for k in range(-6, 12):
        cv.line([(k * 140, by + 30), (k * 140 + 900, H)], (52, 78, 138), 3)
        cv.line([(k * 140 + 900, by + 30), (k * 140, H)], (52, 78, 138), 3)
    cv.tube([(260, 820), (170, 1080), (330, 1290)], MAX["shirt"], 64)
    cv.ell(352, 1318, 40, 34, MAX["skin"], w=LW)
    # телефон
    ph_ = 1.0 if T > TLM.TL[1]["start"] - 0.2 else 0.85
    cv.poly([(830, 200), (990, 230), (940, 500), (780, 470)], (24, 24, 30), w=LW)
    cv.poly([(842, 218), (974, 244), (928, 482), (796, 456)], mix((120, 160, 220), (210, 230, 255), ph_), w=0)
    cv.text(884, 330, "03:12", 46, OUT)
    # бас сверху: тряска + «бум» + ноты
    b = beat(T)
    for k in range(3):
        ph = (T * 0.6 + k / 3) % 1
        cv.text(160 + k * 330, 60 + ph * 260, "♪", 70, (230, 230, 255, int(255 * (1 - ph))))
    if b > 0.6: cv.text(540 + 300 * math.sin(T * 5), 120, "БУМ", 64, (255, 230, 140), stroke=6)
    cv.soft([("p", [(-40, 200), (160, 120), (520, H), (60, H)], (200, 220, 255, 34))], blur=20)   # луч света слева
    return dict(shake=b * 7)

def hallway(cv, warm=(70, 60, 74)):
    wall(cv, warm, 1500, floor=(60, 52, 54))
    cv.soft([("e", (300, 240, 260, 160), (255, 220, 160, 50))], blur=30)
    cv.rect(270, 150, 330, 230, (240, 220, 160), w=LW, r=10)

def sc_door(cv, t, d, T):
    hallway(cv)
    lines = SHOTS[1]["lines"]
    t_open = lines[0]["start"] - SHOTS[1]["start"] - 0.9
    op = ease((t - t_open) / 0.5)
    door(cv, 540, 330, 990, 1500, (128, 82, 58), num="24", open_=op)
    if op > 0.3:
        smoke(cv, 740, 900, t, n=8, spread=140, alpha=int(150 * op))
        tkf = talk("F", T)
        char(cv, "F", 760, 830, 0.95, mood("F", T, "panic"), tkf, t, look=-1, apron=True, flour=2, bottom=1560)
    knocking = t < t_open - 0.05
    tkm = talk("M", T)
    char(cv, "M", 290, 860, 0.95, mood("M", T, "angry"), tkm, t + 1.3, look=1,
         arms=("down", "knock") if knocking else "down", bottom=1560)
    if knocking and 0.3 < t < t_open:
        cv.text(560, 520, "ТУК-ТУК", 54, (255, 240, 200), stroke=6)
    return dict(shake=0)

def sc_cake(cv, t, d, T):
    cv.rect(0, 0, W, H, (54, 40, 40), w=0)
    cv.soft([("e", (540, 900, 520, 420), (255, 190, 120, 50))], blur=40)
    cv.rect(0, 1150, W, H, (120, 90, 70), w=LW)
    z = 1 + 0.08 * ease(t / d)
    cake_burnt(cv, 540, 1040, 1.4 * z, t)
    smoke(cv, 540, 900, t, n=9, spread=90, col=(120, 120, 130), alpha=160, speed=45)
    if t > d * 0.55:
        cv.ell(360 * 1, 1000 + (t - d * 0.55) * 500, 26, 20, (35, 26, 24), w=LW * 0.6)   # отвалился кусок
    return dict(shake=0, zoom=1.0)

def sc_vera(cv, t, d, T):
    cv.rect(0, 0, W, H, (34, 26, 24), w=0)
    smoke(cv, 540, 900, t, n=6, spread=200, alpha=80)
    char(cv, "F", 540, 760, 1.85, mood("F", T, "offended"), talk("F", T), t, apron=True, flour=2, bottom=H + 100)
    cl = ease((t - (d - 1.1)) / 1.0)                    # дверь закрывается
    x = W - (W - 200) * cl
    cv.rect(x, -20, W + 40, H + 20, (128, 82, 58), w=LW)
    cv.rect(x + 80, 200, W - 60, 900, (112, 70, 50), w=4, r=8)
    return dict(shake=0)

def sc_stop(cv, t, d, T):
    hallway(cv, warm=(64, 56, 70))
    g0, g1 = 640, 900
    cv.rect(g0, 200, W + 40, 1600, (30, 24, 22), w=LW)
    smoke(cv, 770, 700, t, n=5, spread=60, alpha=70)
    char(cv, "F", 790, 780, 0.9, mood("F", T, "surprised"), talk("F", T), t, look=-1, apron=True, flour=2, bottom=1700)
    cv.rect(g0 - 40, 180, g0, 1620, (70, 56, 50), w=LW)                                           # косяк
    cv.rect(g1, 180, W + 40, 1620, (128, 82, 58), w=LW)                                           # створка
    cv.rect(g1 + 50, 300, W - 20, 800, (112, 70, 50), w=4, r=8)
    m = mood("M", T, "determined")
    char(cv, "M", 330, 860, 1.25, m, talk("M", T), t + 0.7, look=1, arms=("down", "reach"),
         hand=(g1 + 6, 560), bottom=H + 80)
    if t < 0.35: cv.text(820, 560, "ХЛОП", 60, (255, 230, 150), stroke=6)
    return dict(shake=6 * max(0, 1 - t / 0.25))

def kitchen_bg(cv, t):
    cv.rect(0, 0, W, H, (238, 196, 140), w=0)
    for yy in range(140, 1100, 110):
        for xx in range(0 if (yy // 110) % 2 else 55, W, 110):
            cv.rect(xx + 4, yy + 4, xx + 106, yy + 106, (244, 214, 170), ol=(222, 180, 130), w=2, r=6)
    cv.rect(80, 140, 520, 520, (40, 50, 90), w=LW, r=10)                          # окно, за ним ночь
    cv.line([(300, 140), (300, 520)], OUT, LW); cv.line([(80, 330), (520, 330)], OUT, LW)
    cv.ell(430, 220, 34, 34, (250, 240, 200), w=0)
    for i in range(14):
        cv.ell(110 + (i * 97) % 380, 170 + (i * 53) % 330, 3, 3, (250, 250, 220), w=0)

def sc_kitchen(cv, t, d, T):
    kitchen_bg(cv, t)
    clock(cv, 820, 300, 110, 4, 10 + int(t * 3))
    char(cv, "M", 320, 820, 0.95, mood("M", T, "smirk"), talk("M", T), t, look=1, arms=("down", "stir"), flour=1, bottom=1500)
    char(cv, "F", 770, 840, 0.95, mood("F", T, "surprised"), talk("F", T), t + 0.5, look=-1, arms=("down", "egg"),
         apron=True, flour=2, bottom=1500)
    cv.rect(-20, 1300, W + 20, H + 20, (150, 104, 72), w=LW)                       # столешница
    cv.rect(-20, 1300, W + 20, 1360, (200, 200, 205), w=LW)
    cv.d.chord(cv.P(220, 1180, 470, 1430), 0, 180, fill=(220, 236, 250), outline=OUT, width=int(LW * SS))   # миска
    cv.ell(345, 1305, 125, 26, (250, 236, 200), w=LW)
    cv.line([(345 + math.cos(t * 7) * 40, 1300), (380 + math.cos(t * 7) * 60, 1150)], (200, 170, 120), 12)  # венчик
    cv.rect(560, 1150, 720, 1345, (240, 236, 226), w=LW, r=10)                    # пакет муки
    cv.text(640, 1250, "МУКА", 34, (60, 90, 160))
    cv.ell(860, 1330, 60, 20, (250, 250, 250), w=LW)
    for k in range(3): cv.ell(830 + k * 30, 1318, 16, 20, (252, 244, 226), w=4)   # яйца
    # облачко муки
    ph = (t % 2.2) / 2.2
    if ph < 0.6:
        cv.soft([("e", (640 + math.cos(i * 1.9) * 140 * ph, 1150 - 200 * ph + math.sin(i * 2.7) * 50, 60 + 90 * ph, 55 + 80 * ph),
                  (255, 255, 255, int(160 * (1 - ph / 0.6)))) for i in range(6)], blur=8)
    return dict(shake=0)

def sc_oven(cv, t, d, T):
    kitchen_bg(cv, t)
    clock(cv, 840, 260, 100, 5, 40)
    cv.text(840, 410, "05:40", 40, OUT)
    char(cv, "M", 190, 860, 0.85, mood("M", T, "happy"), talk("M", T), t, look=1, flour=1, bottom=1300)
    char(cv, "F", 890, 870, 0.85, mood("F", T, "happy"), talk("F", T), t + 0.4, look=-1, apron=True, flour=2, bottom=1300)
    cv.rect(-20, 1240, W + 20, H + 20, (150, 104, 72), w=LW)
    cv.rect(-20, 1240, W + 20, 1300, (200, 200, 205), w=LW)
    p = back((t - 0.6) / 0.6)
    cake_nice(cv, 540, 1150, 0.95 * max(0.01, p), t)
    if p > 0.5: sparkles(cv, 540, 1000, t, n=12, rad=330)
    if 0.2 < t < 1.4: cv.text(540, 620, "ДЗЫНЬ!", 80, (255, 236, 140), stroke=8)
    return dict(shake=0)

def sc_final(cv, t, d, T):
    # следующий вечер, дверь Макса, тёплый свет
    wall(cv, (96, 74, 80), 1520, floor=(70, 56, 52))
    cv.soft([("e", (540, 260, 520, 260), (255, 200, 140, 60))], blur=40)
    cv.text(540, 180, "на следующий вечер", 44, (255, 236, 200), stroke=5)
    door(cv, 60, 400, 500, 1520, (90, 120, 150), num="19", open_=1.0, inside=(250, 220, 170))
    char(cv, "M", 260, 880, 0.95, mood("M", T, "smirk"), talk("M", T), t, look=1, bottom=1600)
    h = char(cv, "F", 760, 860, 0.95, mood("F", T, "happy"), talk("F", T), t + 0.5, look=-1, arms="hold", bottom=1600)
    px, py = (h[-1][0] + h[1][0]) / 2, h[1][1] - 20
    cv.ell(px, py, 150, 36, (245, 245, 250), w=LW)
    cv.poly([(px - 60, py - 10), (px + 70, py - 30), (px + 60, py - 110), (px - 60, py - 90)], (250, 226, 200), w=LW)
    cv.poly([(px - 60, py - 90), (px + 60, py - 110), (px + 40, py - 128), (px - 70, py - 106)], (244, 140, 170), w=LW * 0.7)
    cv.ell(px, py - 125, 14, 14, (210, 30, 60), w=4)
    # финальная заставка
    tail0 = TLM.TL[-1]["end"] + 0.4 - SHOTS[-1]["start"]
    k = ease((t - tail0) / 0.6)
    if k > 0:
        cv.soft([("r", (0, 0, W, H), (10, 8, 16, int(200 * k)))])
        for i in range(8):
            a = i * 0.8 + t
            cv.text(540 + math.cos(a) * 380, 860 + math.sin(a * 1.3) * 300, "♥", 50, (255, 120, 150, int(220 * k)))
        cv.text(540, 820, "МОЙ СОСЕД", 104, (255, 255, 255, int(255 * k)), stroke=9)
        cv.text(540, 940, "СВЕРХУ", 104, (255, 200, 120, int(255 * k)), stroke=9)
        cv.text(540, 1070, "1 серия", 54, (255, 255, 255, int(255 * k)), stroke=5)
        cv.text(540, 1180, "продолжение следует...", 44, (230, 230, 240, int(255 * k)), stroke=4)
    return dict(shake=0, sub=k == 0)

SCENES = dict(bed=sc_bed, door=sc_door, cake=sc_cake, vera=sc_vera, stop=sc_stop, kitchen=sc_kitchen, oven=sc_oven, final=sc_final)

# ---------------- субтитры ----------------
def wrap(text, maxc=26):
    out, cur = [], ""
    for w_ in text.split():
        if cur and len(cur) + 1 + len(w_) > maxc: out.append(cur); cur = w_
        else: cur = (cur + " " + w_).strip()
    return out + ([cur] if cur else [])

def draw_sub(cv, T):
    l = line_at(T)
    if not l: return
    rows = wrap(l["L"]["sub"])
    age = T - l["start"]; pop = 1 + 0.12 * (1 - clamp(age / 0.12))
    y0 = 1590 - (len(rows) - 1) * 36
    for k, r in enumerate(rows):
        cv.text(540, y0 + k * 72, r, 56 * pop, (255, 255, 255), stroke=7)

VIG = None
def vignette_img(strength=0.5):
    v = Image.new("L", (W // 4, H // 4), 0); d = ImageDraw.Draw(v)
    for i in range(60):
        k = i / 60
        d.ellipse([-W // 4 * 0.3 + k * W // 8 * 0.8, -H // 4 * 0.15 + k * H // 8 * 0.6,
                   W // 4 * 1.3 - k * W // 8 * 0.8, H // 4 * 1.15 - k * H // 8 * 0.6], fill=int(255 * k))
    v = v.filter(ImageFilter.GaussianBlur(14)).resize((W, H))
    return v.point(lambda p: int(255 - (255 - p) * strength))

TINT = dict(bed=((10, 14, 40), 0.18), door=((20, 14, 30), 0.1), cake=((20, 10, 10), 0.08), vera=((20, 14, 30), 0.1),
            stop=((20, 14, 30), 0.1), kitchen=((40, 20, 0), 0.05), oven=((40, 20, 0), 0.03), final=((40, 16, 10), 0.06))

def frame(T):
    global VIG
    sh = shot_at(T); t = T - sh["start"]; d = sh["end"] - sh["start"]
    cv = Cv((0, 0, 0))
    info = SCENES[sh["name"]](cv, t, d, T) or {}
    if info.get("sub", True): draw_sub(cv, T)
    im = cv.im.convert("RGB").resize((W, H), Image.LANCZOS)
    # камера: медленный наезд + тряска
    z = 1 + 0.035 * ease(t / d) + 0.0
    s_ = info.get("shake", 0)
    dx, dy = int(math.sin(T * 61) * s_), int(math.cos(T * 47) * s_)
    if z > 1.001 or s_:
        z = max(z, 1 + 2.2 * s_ / W * 2)
        cw, ch = int(W / z), int(H / z)
        x0 = (W - cw) // 2 + dx; y0 = (H - ch) // 2 + dy
        im = im.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BILINEAR)
    col, a = TINT[sh["name"]]
    im = Image.blend(im, Image.new("RGB", (W, H), col), a)
    if VIG is None: VIG = vignette_img()
    im = Image.composite(im, Image.new("RGB", (W, H), (8, 6, 14)), VIG)
    fade = min(clamp(t / 0.15), clamp((d - t) / 0.15))
    if sh is SHOTS[0]: fade = min(clamp(t / 0.6), clamp((d - t) / 0.15))
    if sh is SHOTS[-1]: fade = min(clamp(t / 0.15), clamp((d - t) / 0.8))
    if fade < 1: im = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, fade)
    return im

def render_chunk(args):
    i0, i1, path = args
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-threads", "1", "-crf", "19",
                          "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for i in range(i0, i1): p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait()
    return path

if __name__ == "__main__":
    os.makedirs("build", exist_ok=True)
    if sys.argv[1] == "frame":
        frame(float(sys.argv[2])).save(sys.argv[3])
    elif sys.argv[1] == "sheet":
        ts = [float(x) for x in sys.argv[2:]] or [s["start"] + (s["end"] - s["start"]) * 0.6 for s in SHOTS]
        ims = [frame(x).resize((W // 4, H // 4)) for x in ts]
        sheet = Image.new("RGB", (W // 4 * 4, H // 4 * ((len(ims) + 3) // 4)))
        for k, im in enumerate(ims): sheet.paste(im, ((k % 4) * W // 4, (k // 4) * H // 4))
        sheet.save("build/sheet.png")
    elif sys.argv[1] == "shots":
        for s in SHOTS: print(s["name"], round(s["start"], 2), round(s["end"], 2))
        print("TOTAL", TOTAL)
    elif sys.argv[1] == "video":
        n = int(TOTAL * FPS); k = 3
        jobs = [(n * j // k, n * (j + 1) // k, f"build/part{j}.mp4") for j in range(k)]
        with Pool(k) as pool: parts = pool.map(render_chunk, jobs)
        open("build/list.txt", "w").write("".join(f"file '{os.path.basename(p)}'\n" for p in parts))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "build/list.txt",
                        "-c", "copy", "build/video.mp4"], check=True)
        print("video ok")
