"""Remontada — 1-minute vertical cartoon (style of reference_frame_01.png).
Usage: python render.py frame <t> <out.png>   |  python render.py video
"""
import json, math, os, random, subprocess, sys
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from script import SEGMENTS

W, H, SS, FPS = 1080, 1920, 2, 30
OUT = (17, 17, 20)
LW = 7
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_fonts = {}
def font(sz):
    k = int(sz * SS)
    if k not in _fonts: _fonts[k] = ImageFont.truetype(FONT_B, k)
    return _fonts[k]

# palette
BLUE, GARNET = (29, 75, 155), (165, 0, 68)
PSG_NAVY, PSG_RED = (22, 34, 74), (218, 41, 28)
SKIN = {"light": (232, 186, 150), "tan": (214, 160, 118), "med": (180, 124, 86), "dark": (122, 80, 52)}
GRASS1, GRASS2 = (46, 112, 64), (52, 124, 71)
NIGHT = (14, 20, 40)

# ---------------- timeline ----------------
DUR = json.load(open("audio/durations.json"))
TIMING = json.load(open("audio/timing.json"))
speech = sum(DUR[s["id"]] for s in SEGMENTS)
TOTAL = max(60.0, round(speech + 1.4 + 0.3 * len(SEGMENTS), 1))   # не жертвуем чёткостью ради ровной минуты
TAIL = 1.4
pad = (TOTAL - speech - TAIL) / len(SEGMENTS)
PAD_IN, PAD_OUT = pad * 0.4, pad * 0.6
TL = []
t = 0.0
for i, s in enumerate(SEGMENTS):
    d = PAD_IN + DUR[s["id"]] + PAD_OUT + (TAIL if i == len(SEGMENTS) - 1 else 0)
    TL.append(dict(seg=s, start=t, end=t + d, vo=t + PAD_IN, vodur=DUR[s["id"]]))
    t += d

def key_time(e):
    ph = e["seg"]["phrases"]
    for i, p in enumerate(ph):
        if p["key"]:
            a, b = TIMING[e["seg"]["id"]][i]
            return PAD_IN + a + (b - a) * 0.6
    return None

def goal_times():
    return [(e["start"] + key_time(e), e["seg"]["scene"]) for e in TL if key_time(e) is not None]

# ---------------- easing ----------------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def back(x):
    x = clamp(x); c = 1.9
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def lerp(a, b, x): return a + (b - a) * x
def mix(c1, c2, x): return tuple(int(lerp(a, b, x)) for a, b in zip(c1, c2))

# ---------------- canvas ----------------
class Cv:
    def __init__(s, bg):
        s.im = Image.new("RGB", (W * SS, H * SS), bg); s.d = ImageDraw.Draw(s.im)
    def P(s, *v): return [int(x * SS) for x in v]
    def ell(s, cx, cy, rx, ry, fill, ol=OUT, w=LW):
        s.d.ellipse(s.P(cx - rx, cy - ry, cx + rx, cy + ry), fill=fill, outline=ol if w else None, width=int(w * SS))
    def rect(s, x0, y0, x1, y1, fill, ol=OUT, w=LW, r=0):
        s.d.rounded_rectangle(s.P(x0, y0, x1, y1), radius=int(r * SS), fill=fill, outline=ol if w else None, width=int(w * SS))
    def poly(s, pts, fill, ol=OUT, w=LW):
        pp = [(x * SS, y * SS) for x, y in pts]
        s.d.polygon(pp, fill=fill)
        if w and ol: s.d.line(pp + [pp[0]], fill=ol, width=int(w * SS), joint="curve")
    def line(s, pts, col, w=LW):
        s.d.line([(x * SS, y * SS) for x, y in pts], fill=col, width=int(w * SS), joint="curve")
    def arc(s, cx, cy, rx, ry, a0, a1, col=OUT, w=5):
        s.d.arc(s.P(cx - rx, cy - ry, cx + rx, cy + ry), a0, a1, fill=col, width=int(w * SS))
    def text(s, x, y, txt, sz, fill=(255, 255, 255), stroke=0, sc=OUT, anchor="mm"):
        s.d.text((x * SS, y * SS), txt, font=font(sz), fill=fill, anchor=anchor,
                 stroke_width=int(stroke * SS), stroke_fill=sc)
    def tsize(s, txt, sz):
        b = s.d.textbbox((0, 0), txt, font=font(sz)); return (b[2] - b[0]) / SS, (b[3] - b[1]) / SS
    def overlay(s, color, alpha):
        if alpha <= 0: return
        s.im = Image.blend(s.im, Image.new("RGB", s.im.size, color), clamp(alpha)); s.d = ImageDraw.Draw(s.im)
    def stripes_in(s, bbox, maskfn, cols, sw, vertical=True):
        """fill a shape (drawn by maskfn on a local mask) with stripes"""
        x0, y0, x1, y1 = [int(v * SS) for v in bbox]
        w, h = x1 - x0, y1 - y0
        if w <= 0 or h <= 0: return
        layer = Image.new("RGB", (w, h), cols[0]); ld = ImageDraw.Draw(layer)
        n = 0; p = 0; step = int(sw * SS)
        while p < (w if vertical else h):
            if n % 2: ld.rectangle([p, 0, p + step, h] if vertical else [0, p, w, p + step], fill=cols[1])
            p += step; n += 1
        mask = Image.new("L", (w, h), 0); md = ImageDraw.Draw(mask)
        maskfn(md, x0, y0)
        s.im.paste(layer, (x0, y0), mask)

# ---------------- kits ----------------
def kit_fill(cv, kit, bbox, maskfn):
    x0, y0, x1, y1 = bbox
    if kit == "barca":
        cv.stripes_in(bbox, maskfn, [BLUE, GARNET], (x1 - x0) / 5)
    elif kit == "psg":
        cv.stripes_in(bbox, maskfn, [PSG_NAVY, PSG_NAVY], 999)
        cx = (x0 + x1) / 2; bw = (x1 - x0) * 0.16
        def m2(md, ox, oy):
            maskfn(md, ox, oy)
        layer_box = (cx - bw, y0, cx + bw, y1)
        # red band: intersect by drawing band through mask
        X0, Y0, X1, Y1 = [int(v * SS) for v in bbox]
        mask = Image.new("L", (X1 - X0, Y1 - Y0), 0); maskfn(ImageDraw.Draw(mask), X0, Y0)
        band = Image.new("L", mask.size, 0)
        ImageDraw.Draw(band).rectangle([int((cx - bw) * SS) - X0, 0, int((cx + bw) * SS) - X0, mask.size[1]], fill=255)
        from PIL import ImageChops
        m = ImageChops.multiply(mask, band)
        cv.im.paste(Image.new("RGB", mask.size, PSG_RED), (X0, Y0), m)
        whitew = bw * 0.25
        for sx in (cx - bw, cx + bw):
            b2 = Image.new("L", mask.size, 0)
            ImageDraw.Draw(b2).rectangle([int((sx - whitew) * SS) - X0, 0, int((sx + whitew) * SS) - X0, mask.size[1]], fill=255)
            cv.im.paste(Image.new("RGB", mask.size, (240, 240, 240)), (X0, Y0), ImageChops.multiply(mask, b2))
    else:
        col = {"coach": (30, 32, 40), "keeper": (226, 200, 40)}.get(kit, kit)
        cv.stripes_in(bbox, maskfn, [col, col], 999)

# ---------------- front-view character (like the reference) ----------------
def person(cv, x, y, sc=1.0, kit="barca", skin="light", hair=(110, 62, 30), style="spiky", mood="happy",
           arms="down", beard=False, number=None, t=0.0, label=None, headband=False):
    """x,y = center of head. Head radius 150*sc."""
    R = 150 * sc; L = LW * max(0.6, sc)
    sk = SKIN[skin]
    # torso
    tw, th = R * 1.55, R * 1.9
    ty0 = y + R * 0.85
    bbox = (x - tw, ty0, x + tw, ty0 + th)
    def tmask(md, ox, oy):
        md.rounded_rectangle([int((x - tw) * SS) - ox, int(ty0 * SS) - oy, int((x + tw) * SS) - ox, int((ty0 + th + 60) * SS) - oy],
                             radius=int(R * 0.7 * SS), fill=255)
    # arms
    sw = math.sin(t * 9) * 0.12
    def arm(side):
        sx = x + side * tw * 0.86; sy = ty0 + R * 0.35
        if arms == "up":
            a = math.radians(-90 + side * (32 + 10 * sw * 8))
        elif arms == "head":
            a = math.radians(-90 + side * 70)
        elif arms == "point" and side == 1:
            a = math.radians(-35)
        elif arms == "fist" and side == 1:
            a = math.radians(-70 + 8 * math.sin(t * 12))
        else:
            a = math.radians(90 - side * 18)
        ln = R * 1.5
        ex, ey = sx + math.cos(a) * ln, sy + math.sin(a) * ln
        if arms == "head":
            ex, ey = x + side * R * 0.95, y - R * 0.35
            mx, my = sx + side * R * 0.9, sy - R * 0.45
            cv.line([(sx, sy), (mx, my), (ex, ey)], OUT, R * 0.48 + 2 * L)
            cv.line([(sx, sy), (mx, my), (ex, ey)], kitcol(kit), R * 0.48)
        else:
            cv.line([(sx, sy), (ex, ey)], OUT, R * 0.48 + 2 * L)
            cv.line([(sx, sy), (ex, ey)], kitcol(kit), R * 0.48)
        cv.ell(ex, ey, R * 0.25, R * 0.25, sk, w=L)
    if arms in ("down", "point", "fist"):
        pass
    for side in (-1, 1):
        if arms != "head": arm(side)
    # torso on top of shoulders
    cv.rect(x - tw - L, ty0 - L, x + tw + L, ty0 + th + 60, OUT, w=0, r=R * 0.72)
    kit_fill(cv, kit, bbox, tmask)
    # collar
    cv.ell(x, ty0 + 4, R * 0.55, R * 0.22, kitcol(kit, collar=True), w=L)
    if number is not None:
        cv.text(x + tw * 0.48, ty0 + th * 0.42, str(number), R * 0.42, (255, 230, 120), stroke=4 * sc + 1)
    # ears
    for side in (-1, 1): cv.ell(x + side * R * 0.95, y + R * 0.08, R * 0.2, R * 0.24, sk, w=L)
    # head
    cv.ell(x, y, R, R * 1.05, sk, w=L)
    if beard:
        cv.d.chord(cv.P(x - R * 0.98, y - R * 0.6, x + R * 0.98, y + R * 1.05), 10, 170, fill=hair)
        cv.ell(x, y + R * 0.52, R * 0.5, R * 0.3, sk, w=0)
    # hair
    hair_shape(cv, x, y, R, hair, style, L)
    if headband:
        cv.rect(x - R * 0.98, y - R * 0.62, x + R * 0.98, y - R * 0.46, (240, 240, 240), w=L * 0.7, r=8)
    face(cv, x, y, R, mood, L, t)
    if label:
        tag(cv, x, y - R * 1.75, label, max(34, 46 * sc))

def kitcol(kit, collar=False):
    if kit == "barca": return GARNET if collar else BLUE
    if kit == "psg": return PSG_RED if collar else PSG_NAVY
    if kit == "coach": return (60, 62, 72) if collar else (30, 32, 40)
    if kit == "keeper": return (190, 160, 20) if collar else (226, 200, 40)
    return kit

def hair_shape(cv, x, y, R, col, style, L):
    if style == "spiky":   # same as the reference character
        pts = [(x - R * 1.0, y - R * 0.05), (x - R * 0.98, y - R * 0.7), (x - R * 0.5, y - R * 1.05), (x - R * 0.15, y - R * 1.6),
               (x + R * 0.05, y - R * 1.05), (x + R * 0.35, y - R * 1.55), (x + R * 0.45, y - R * 1.0), (x + R * 0.95, y - R * 0.75),
               (x + R * 1.0, y - R * 0.05), (x + R * 0.8, y - R * 0.4), (x + R * 0.55, y - R * 0.32), (x + R * 0.35, y - R * 0.55),
               (x + R * 0.1, y - R * 0.35), (x - R * 0.12, y - R * 0.58), (x - R * 0.35, y - R * 0.36), (x - R * 0.6, y - R * 0.55),
               (x - R * 0.8, y - R * 0.3)]
    elif style == "short":
        pts = [(x - R * 0.98, y - R * 0.15), (x - R * 0.9, y - R * 0.75), (x - R * 0.4, y - R * 1.1), (x + R * 0.4, y - R * 1.1),
               (x + R * 0.9, y - R * 0.75), (x + R * 0.98, y - R * 0.15), (x + R * 0.75, y - R * 0.5), (x, y - R * 0.62),
               (x - R * 0.75, y - R * 0.5)]
    elif style == "quiff":
        pts = [(x - R * 0.98, y - R * 0.15), (x - R * 0.92, y - R * 0.8), (x - R * 0.3, y - R * 1.25), (x + R * 0.5, y - R * 1.45),
               (x + R * 0.95, y - R * 0.9), (x + R * 0.98, y - R * 0.15), (x + R * 0.78, y - R * 0.55), (x, y - R * 0.66),
               (x - R * 0.75, y - R * 0.5)]
    elif style == "long":
        pts = [(x - R * 1.15, y + R * 0.9), (x - R * 1.05, y - R * 0.6), (x - R * 0.4, y - R * 1.12), (x + R * 0.4, y - R * 1.12),
               (x + R * 1.05, y - R * 0.6), (x + R * 1.15, y + R * 0.9), (x + R * 0.88, y + R * 0.9), (x + R * 0.85, y - R * 0.3),
               (x, y - R * 0.6), (x - R * 0.85, y - R * 0.3), (x - R * 0.88, y + R * 0.9)]
    elif style == "buzz":
        pts = [(x - R * 0.96, y - R * 0.25), (x - R * 0.85, y - R * 0.78), (x - R * 0.3, y - R * 1.06), (x + R * 0.3, y - R * 1.06),
               (x + R * 0.85, y - R * 0.78), (x + R * 0.96, y - R * 0.25), (x + R * 0.8, y - R * 0.62), (x, y - R * 0.8),
               (x - R * 0.8, y - R * 0.62)]
    else:
        return
    cv.poly(pts, col, w=L)

def face(cv, x, y, R, mood, L, t):
    ew = L * 0.8
    # eyebrows
    if mood in ("angry", "shout", "determined"):
        cv.line([(x - R * 0.55, y - R * 0.33), (x - R * 0.18, y - R * 0.22)], OUT, ew * 1.6)
        cv.line([(x + R * 0.55, y - R * 0.33), (x + R * 0.18, y - R * 0.22)], OUT, ew * 1.6)
    elif mood == "sad":
        cv.line([(x - R * 0.55, y - R * 0.22), (x - R * 0.18, y - R * 0.34)], OUT, ew * 1.4)
        cv.line([(x + R * 0.55, y - R * 0.22), (x + R * 0.18, y - R * 0.34)], OUT, ew * 1.4)
    else:
        cv.arc(x - R * 0.37, y - R * 0.22, R * 0.2, R * 0.1, 200, 340, OUT, ew * 1.4)
        cv.arc(x + R * 0.37, y - R * 0.22, R * 0.2, R * 0.1, 200, 340, OUT, ew * 1.4)
    # eyes
    for sx in (-1, 1):
        ex = x + sx * R * 0.37; ey = y + R * 0.02
        if mood in ("happy", "shout"):
            cv.arc(ex, ey + R * 0.06, R * 0.16, R * 0.12, 200, 340, OUT, ew * 1.3)
        elif mood == "sad":
            cv.arc(ex, ey - R * 0.02, R * 0.15, R * 0.1, 20, 160, OUT, ew * 1.3)
        else:
            cv.ell(ex, ey, R * 0.07, R * 0.09, OUT, w=0)
    # nose (like reference: little hook)
    cv.arc(x + R * 0.02, y + R * 0.2, R * 0.08, R * 0.12, 100, 280, OUT, ew)
    # mouth
    if mood == "shout":
        oy = R * (0.32 + 0.04 * math.sin(t * 20))
        cv.ell(x, y + R * 0.58, R * 0.26, oy, (90, 20, 30), w=L * 0.8)
        cv.ell(x, y + R * 0.72, R * 0.15, R * 0.08, (230, 110, 120), w=0)
    elif mood == "happy":
        cv.d.chord(cv.P(x - R * 0.32, y + R * 0.32, x + R * 0.32, y + R * 0.8), 0, 180, fill=(90, 20, 30), outline=OUT, width=int(L * 0.8 * SS))
    elif mood == "sad":
        cv.arc(x, y + R * 0.7, R * 0.22, R * 0.12, 200, 340, OUT, ew * 1.2)
    elif mood == "calm":
        cv.line([(x - R * 0.18, y + R * 0.55), (x + R * 0.18, y + R * 0.55)], OUT, ew * 1.2)
    else:  # determined / talking
        cv.ell(x, y + R * 0.55, R * 0.16, R * (0.08 + 0.06 * abs(math.sin(t * 14))), (90, 20, 30), w=L * 0.7)

def tag(cv, x, y, txt, sz, bg=(255, 255, 255), fg=OUT):
    tw, th = cv.tsize(txt, sz)
    cv.rect(x - tw / 2 - 22, y - th / 2 - 16, x + tw / 2 + 22, y + th / 2 + 18, bg, w=5, r=18)
    cv.text(x, y + 2, txt, sz, fg)

# ---------------- top-down pieces (pitch like the bed in the reference: seen from above) ----------------
def pitch(cv, t, cam_y=0.0):
    sw = 150
    for i in range(-2, 16):
        y0 = i * sw - (cam_y % (2 * sw))
        cv.rect(0, y0, W, y0 + sw, GRASS1 if i % 2 == 0 else GRASS2, w=0)
    lw = 8; wc = (235, 240, 235)
    # goal line, penalty box, 6-yard box, penalty spot, arc
    gy = 470 - cam_y
    cv.line([(0, gy), (W, gy)], wc, lw)
    cv.d.rectangle(cv.P(140, gy, 940, gy + 620), outline=wc, width=lw * SS)
    cv.d.rectangle(cv.P(340, gy, 740, gy + 210), outline=wc, width=lw * SS)
    cv.ell(540, gy + 420, 9, 9, wc, w=0)
    cv.arc(540, gy + 420, 300, 300, 37, 143, wc, lw)
    return gy

def goal_net(cv, gy, bulge=0.0, side_bulge=0.0):
    x0, x1 = 400, 680; depth = 120
    cv.rect(x0 - 12, gy - depth - 12 - bulge * 40, x1 + 12, gy, (225, 230, 235), w=LW, r=10)
    cv.rect(x0, gy - depth - bulge * 40, x1, gy - 6, (60, 70, 70), w=0)
    for i in range(0, 29):
        xx = x0 + i * 10
        cv.line([(xx, gy - depth - bulge * 40 * (1 - abs(xx - 540 - side_bulge) / 200) ), (xx, gy - 6)], (200, 210, 210), 2)
    for j in range(0, 12):
        yy = gy - 6 - j * 10
        cv.line([(x0, yy), (x1, yy)], (200, 210, 210), 2)
    cv.line([(x0 - 6, gy), (x1 + 6, gy)], (255, 255, 255), 14)

def topdown(cv, x, y, kit, hair=(60, 36, 20), r=46, label=None, ang=0.0, skin="light"):
    # shadow
    cv.ell(x + 8, y + 12, r * 1.45, r * 0.95, (20, 50, 30), w=0)
    bbox = (x - r * 1.45, y - r * 0.9, x + r * 1.45, y + r * 0.9)
    def m(md, ox, oy): md.ellipse([int((x - r * 1.45) * SS) - ox, int((y - r * 0.9) * SS) - oy, int((x + r * 1.45) * SS) - ox, int((y + r * 0.9) * SS) - oy], fill=255)
    cv.ell(x, y, r * 1.45 + 3, r * 0.9 + 3, OUT, w=0)
    kit_fill(cv, kit, bbox, m)
    cv.ell(x, y, r * 1.45, r * 0.9, None, w=LW * 0.8)
    cv.ell(x, y - r * 0.05, r * 0.62, r * 0.62, SKIN[skin], w=LW * 0.8)
    cv.d.chord(cv.P(x - r * 0.62, y - r * 0.67, x + r * 0.62, y + r * 0.57), 180, 360, fill=hair, outline=OUT, width=int(LW * 0.8 * SS))
    if label: tag(cv, x, y - r * 2.0, label, 34)

def ball(cv, x, y, r=24, rot=0.0):
    cv.ell(x + 6, y + 9, r, r * 0.8, (20, 50, 30), w=0)
    cv.ell(x, y, r, r, (250, 250, 250), w=LW * 0.75)
    for k in range(5):
        a = rot + k * 2 * math.pi / 5
        cv.ell(x + math.cos(a) * r * 0.55, y + math.sin(a) * r * 0.55, r * 0.17, r * 0.17, OUT, w=0)
    cv.ell(x, y, r * 0.2, r * 0.2, OUT, w=0)

def bez(p0, p1, p2, u):
    return ((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0], (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1])

# ---------------- HUD ----------------
def scoreboard(cv, home, away, hs, as_, minute, agg=None, punch=0.0, title=None):
    y = 120; s = 1 + 0.25 * punch
    cv.rect(110, y - 70, 970, y + 70, (16, 18, 28), w=LW, r=30)
    cv.rect(118, y - 62, 175, y + 62, BLUE if home == "БАР" else PSG_NAVY, w=0, r=24)
    cv.rect(905, y - 62, 962, y + 62, PSG_NAVY if away == "ПСЖ" else BLUE, w=0, r=24)
    cv.rect(118 + 28, y - 62, 175, y + 62, GARNET if home == "БАР" else PSG_RED, w=0)
    cv.rect(905, y - 62, 932, y + 62, PSG_RED if away == "ПСЖ" else GARNET, w=0)
    cv.text(290, y, home, 58)
    cv.text(790, y, away, 58)
    cv.text(540, y, f"{hs}:{as_}", 84 * s, (255, 222, 90), stroke=5, sc=OUT)
    if minute:
        mw, _ = cv.tsize(minute, 40)
        cv.rect(540 - mw / 2 - 30, y + 70, 540 + mw / 2 + 30, y + 130, (230, 40, 50), w=5, r=14)
        cv.text(540, y + 101, minute, 40)
    if agg:
        tw, _ = cv.tsize(agg, 36)
        cv.rect(540 - tw / 2 - 24, y + 142, 540 + tw / 2 + 24, y + 200, (255, 255, 255), w=5, r=14)
        cv.text(540, y + 172, agg, 36, OUT)
    if title:
        cv.text(540, y - 98 + 10, title, 34, (210, 220, 255), stroke=4)

def vignette_img(strength=0.55):
    v = Image.new("L", (W // 4, H // 4), 0); d = ImageDraw.Draw(v)
    for i in range(60):
        k = i / 60
        d.ellipse([-W // 4 * 0.3 + k * W // 8 * 0.8, -H // 4 * 0.15 + k * H // 8 * 0.6,
                   W // 4 * 1.3 - k * W // 8 * 0.8, H // 4 * 1.15 - k * H // 8 * 0.6], fill=int(255 * k))
    v = v.filter(ImageFilter.GaussianBlur(14)).resize((W, H))
    return v.point(lambda p: int(255 - (255 - p) * strength))
VIG = None

# ---------------- crowd / stadium ----------------
def crowd(cv, y0, y1, t, density=1.0, seed=1, colors=None, jump=0.0):
    rnd = random.Random(seed)
    colors = colors or [BLUE, GARNET, (230, 200, 60), (200, 200, 210)]
    rows = int((y1 - y0) / 46)
    for r_ in range(rows):
        yy = y0 + r_ * 46
        for c in range(0, int(26 * density)):
            xx = c * (W / (26 * density)) + (r_ % 2) * 20 + rnd.uniform(-8, 8)
            jj = jump * abs(math.sin(t * 9 + rnd.uniform(0, 6))) * 22
            col = rnd.choice(colors)
            cv.ell(xx, yy - jj + 10, 24, 22, col, w=3)
            cv.ell(xx, yy - jj - 20, 14, 14, rnd.choice(list(SKIN.values())[:3]), w=3)

def confetti(cv, t, t0, n=90, seed=7):
    if t < t0: return
    rnd = random.Random(seed); dt = t - t0
    for i in range(n):
        x = rnd.uniform(0, W) + math.sin(dt * 3 + i) * 40
        y = -60 + (rnd.uniform(0, 1.2) * H + dt * rnd.uniform(380, 700)) % (H + 120) if dt > 0 else 0
        y = -60 + rnd.uniform(-300, 200) + dt * rnd.uniform(500, 900)
        if y > H + 40: continue
        col = rnd.choice([BLUE, GARNET, (255, 210, 60), (255, 255, 255)])
        a = dt * rnd.uniform(4, 10) + i
        w_, h_ = 14 * abs(math.cos(a)) + 3, 9
        cv.rect(x - w_, y - h_, x + w_, y + h_, col, w=0)

def rays(cv, cx, cy, t, col, n=14, alpha=1.0):
    for k in range(n):
        a = t * 0.4 + k * 2 * math.pi / n
        pts = [(cx, cy), (cx + math.cos(a - 0.09) * 2000, cy + math.sin(a - 0.09) * 2000),
               (cx + math.cos(a + 0.09) * 2000, cy + math.sin(a + 0.09) * 2000)]
        cv.poly(pts, col, w=0)

# ---------------- scenes ----------------
def sc_paris(cv, t, d):
    cv.rect(0, 0, W, H, (24, 22, 52), w=0)
    # rain-blue night, Eiffel tower silhouette, stadium lights
    for i in range(40):
        rnd = random.Random(i)
        cv.ell(rnd.uniform(0, W), rnd.uniform(0, 700), 3, 3, (200, 210, 255), w=0)
    ex, ey = 780, 1100
    cv.poly([(ex - 150, ey), (ex - 20, 420), (ex + 20, 420), (ex + 150, ey), (ex + 90, ey), (ex + 10, 700), (ex - 10, 700), (ex - 90, ey)], (12, 12, 30), w=0)
    cv.line([(ex - 85, 860), (ex + 85, 860)], (12, 12, 30), 22); cv.line([(ex - 45, 640), (ex + 45, 640)], (12, 12, 30), 16)
    cv.line([(ex, 420), (ex, 360)], (12, 12, 30), 8)
    cv.d.chord(cv.P(ex - 80, ey - 90, ex + 80, ey + 90), 180, 360, fill=(24, 22, 52))
    cv.rect(0, 1000, W, H, (16, 16, 34), w=0)
    # scoreboard big
    p = back((t - 0.2) / 0.6)
    scoreboard(cv, "ПСЖ", "БАР", 4 if t > 0.0 else 0, 0, "КОНЕЦ", agg=None, punch=0, title="1/8 ФИНАЛА · ПЕРВЫЙ МАТЧ")
    # big "4:0"
    cv.text(320, 600, "4:0", 260 * (0.3 + 0.7 * p), (255, 80, 70), stroke=10)
    # sad Barça boy in the rain
    person(cv, 540, 1250 + 8 * math.sin(t * 2), 1.0, kit="barca", mood="sad", arms="down", t=t, style="spiky")
    for i in range(70):
        rnd = random.Random(100 + i)
        x = rnd.uniform(0, W); y = (rnd.uniform(0, H) + t * 1400) % H
        cv.line([(x, y), (x - 8, y + 40)], (150, 170, 230), 3)

def sc_paris_goals(cv, t, d):
    sc_bg_dark(cv, (28, 24, 56))
    scoreboard(cv, "ПСЖ", "БАР", 4, 0, "КОНЕЦ", title="14 ФЕВРАЛЯ 2017 · ПАРИЖ")
    goals = [("18'", "ДИ МАРИЯ"), ("40'", "ДРАКСЛЕР"), ("55'", "ДИ МАРИЯ"), ("72'", "КАВАНИ")]
    per = (d - 1.0) / 4.5
    for i, (m, n) in enumerate(goals):
        ti = 0.15 + i * per
        if t < ti: continue
        p = back((t - ti) / 0.35)
        y = 470 + i * 175
        x = lerp(-500, 540, p)
        cv.rect(x - 400, y - 70, x + 400, y + 70, PSG_NAVY, w=LW, r=26)
        cv.rect(x - 400, y - 70, x - 260, y + 70, PSG_RED, w=LW, r=26)
        cv.text(x - 330, y, m, 56)
        cv.text(x + 60, y, n, 64)
        ball(cv, x + 340, y, 32, rot=t * 3)
    # "game over" stamp
    ts = 0.15 + 4 * per
    if t > ts:
        p = back((t - ts) / 0.4)
        s = lerp(2.4, 1.0, p)
        cv.rect(540 - 380 * s, 1280 - 95 * s, 540 + 380 * s, 1280 + 95 * s, None, ol=(230, 50, 50), w=14)
        cv.text(540, 1280, "ВСЁ КОНЧЕНО?", 92 * s, (230, 50, 50))
    person(cv, 540, 1720, 0.75, kit="barca", mood="sad", arms="head", t=t)

def sc_bg_dark(cv, col):
    cv.rect(0, 0, W, H, col, w=0)
    for i in range(0, H, 120):
        cv.rect(0, i, W, i + 60, mix(col, (0, 0, 0), 0.18), w=0)

def sc_coach(cv, t, d):
    # dressing room: lockers
    cv.rect(0, 0, W, H, (40, 46, 70), w=0)
    for i in range(6):
        x = 20 + i * 180
        cv.rect(x, 260, x + 160, 1250, (60, 74, 110), w=LW, r=8)
        cv.line([(x + 125, 640), (x + 125, 720)], (180, 190, 210), 8)
        for j in range(4): cv.line([(x + 30, 320 + j * 18), (x + 130, 320 + j * 18)], (40, 50, 80), 5)
    cv.rect(0, 1250, W, H, (60, 50, 44), w=0)
    cv.rect(0, 1250, W, 1300, (90, 70, 56), w=0)
    # tactic board
    cv.rect(60, 330, 440, 600, (245, 245, 240), w=LW, r=10)
    cv.text(250, 400, "ПСЖ — БАР", 40, OUT)
    cv.text(250, 515, "4:0", 110, (220, 40, 40))
    if t > 1.2:
        cv.line([(90, 480), (410, 560)], (220, 40, 40), 12)
    # Luis Enrique (coach), talking
    person(cv, 560, 1080, 1.15, kit="coach", skin="tan", hair=(70, 60, 55), style="buzz", mood="determined",
           arms="fist", t=t, label="ЛУИС ЭНРИКЕ")
    # speech bubble with 4 -> 6
    p = back((t - 0.6) / 0.5)
    if p > 0:
        bx, by = 780, 560
        cv.ell(760, 700, 26 * p, 20 * p, (255, 255, 255), w=LW)
        cv.rect(bx - 250 * p, by - 120 * p, bx + 250 * p, by + 120 * p, (255, 255, 255), w=LW, r=60)
        if p > 0.8:
            cv.text(bx - 150, by, "4", 150, PSG_NAVY)
            cv.text(bx - 20, by, "➜", 90, OUT)
            six = 1 + 0.15 * math.sin(t * 10) if t > 2.0 else 1.0
            if t > 1.6: cv.text(bx + 140, by, "6", 170 * six, GARNET, stroke=6, sc=(255, 210, 60))

def sc_campnou(cv, t, d):
    cv.rect(0, 0, W, H, NIGHT, w=0)
    zoom = lerp(1.0, 1.12, ease(t / d))
    cx, cy = 540, 1000
    # stadium bowl (top-down) with crowd rings
    rnd = random.Random(3)
    for ring in range(9, 0, -1):
        rx, ry = (430 + ring * 60) * zoom, (300 + ring * 70) * zoom
        cv.ell(cx, cy, rx, ry, mix((40, 40, 70), (20, 20, 40), ring / 9), w=4)
        n = 50 + ring * 10
        for k in range(n):
            a = k / n * 2 * math.pi + ring
            px = cx + math.cos(a) * (rx - 28); py = cy + math.sin(a) * (ry - 28)
            col = [BLUE, GARNET, (255, 210, 60), (230, 230, 240)][(k + ring) % 4]
            if rnd.random() < 0.5 + 0.5 * math.sin(t * 6 + k + ring): col = mix(col, (255, 255, 255), 0.4)
            cv.ell(px, py, 9, 9, col, w=0)
    # pitch in the middle
    cv.rect(cx - 330 * zoom, cy - 230 * zoom, cx + 330 * zoom, cy + 230 * zoom, GRASS1, w=LW, r=10)
    for i in range(6):
        if i % 2: cv.rect(cx - 330 * zoom + i * 110 * zoom, cy - 226 * zoom, cx - 220 * zoom + i * 110 * zoom, cy + 226 * zoom, GRASS2, w=0)
    cv.d.rectangle(cv.P(cx - 320 * zoom, cy - 220 * zoom, cx + 320 * zoom, cy + 220 * zoom), outline=(230, 240, 230), width=5 * SS)
    cv.line([(cx, cy - 220 * zoom), (cx, cy + 220 * zoom)], (230, 240, 230), 5)
    cv.ell(cx, cy, 60 * zoom, 60 * zoom, None, ol=(230, 240, 230), w=5)
    # floodlights
    for (lx, ly) in [(80, 360), (1000, 360), (80, 1640), (1000, 1640)]:
        cv.ell(lx, ly, 40, 40, (255, 250, 200), w=LW)
    scoreboard(cv, "БАР", "ПСЖ", 0, 0, "0'", agg="СУММА 0:4", title="8 МАРТА 2017 · ОТВЕТНЫЙ МАТЧ")
    p = back((t - 0.5) / 0.5)
    if p > 0:
        cv.text(540, 1600, "КАМП НОУ", 120 * p, (255, 255, 255), stroke=9)
    if t > 1.8:
        cv.text(540, 1720, "≈ 96 000 ЗРИТЕЛЕЙ", 52, (255, 210, 60), stroke=6)

GOALS = {
    # scene: (score after, minute, aggregate after, scorer label, scorer look, attacker kit, team that scored, kind)
    "g_suarez":     ((1, 0), "3'",    "СУММА 1:4", "СУАРЕС", dict(skin="tan", hair=(40, 28, 20), style="short", number=9), "header"),
    "g_kurzawa":    ((2, 0), "40'",   "СУММА 2:4", "КУРЗАВА", dict(skin="dark", hair=(20, 16, 14), style="buzz", number=20), "owngoal"),
    "g_messi":      ((3, 0), "50'",   "СУММА 3:4", "МЕССИ", dict(skin="light", hair=(90, 56, 28), style="short", beard=True, number=10), "penalty"),
    "g_cavani":     ((3, 1), "62'",   "СУММА 3:5", "КАВАНИ", dict(skin="tan", hair=(40, 30, 22), style="long", beard=True, number=9, headband=True), "cavani"),
    "g_neymar_fk":  ((4, 1), "88'",   "СУММА 4:5", "НЕЙМАР", dict(skin="med", hair=(50, 34, 24), style="quiff", number=11), "freekick"),
    "g_neymar_pen": ((5, 1), "90+1'", "СУММА 5:5", "НЕЙМАР", dict(skin="med", hair=(50, 34, 24), style="quiff", number=11), "penalty"),
    "g_roberto":    ((6, 1), "90+5'", "СУММА 6:5", "СЕРДЖИ РОБЕРТО", dict(skin="light", hair=(70, 44, 26), style="spiky", number=20), "cross"),
}
PREV = {"g_suarez": (0, 0), "g_kurzawa": (1, 0), "g_messi": (2, 0), "g_cavani": (3, 0), "g_neymar_fk": (3, 1),
        "g_neymar_pen": (4, 1), "g_roberto": (5, 1)}
PREV_AGG = {"g_suarez": "СУММА 0:4", "g_kurzawa": "СУММА 1:4", "g_messi": "СУММА 2:4", "g_cavani": "СУММА 3:4",
            "g_neymar_fk": "СУММА 3:5", "g_neymar_pen": "СУММА 4:5", "g_roberto": "СУММА 5:5"}

def sc_goal(cv, t, d, scene, tg):
    score, minute, agg, name, look, kind = GOALS[scene]
    after = t >= tg
    psg_scores = kind == "cavani"
    if not after or t < tg + 0.22:
        # ---------- phase A: top-down action, camera on the PSG goal (Barça attacks upward)
        pre = clamp(t / max(0.3, tg))
        cam = 0
        if kind == "cavani":  # Barça goal at top, PSG attacking
            pass
        gy = pitch(cv, t, cam)
        u = ease(pre)
        attk = "psg" if psg_scores else "barca"
        defk = "barca" if psg_scores else "psg"
        if kind == "header":
            p0, p1, p2 = (900, 1000), (700, 500), (560, 760)
            if pre < 0.7:
                bx, by = bez(p0, p1, p2, pre / 0.7)
            else:
                bx, by = bez((560, 760), (520, 500), (500, gy - 60), (pre - 0.7) / 0.3)
            shooter = (560, 800); helper = (900, 1050, "barca", None)
        elif kind == "owngoal":
            if pre < 0.55: bx, by = bez((330, 640), (300, 470), (420, 420), pre / 0.55)
            else: bx, by = bez((420, 420), (470, 380), (470, gy - 60), (pre - 0.55) / 0.45)
            shooter = (450, 470); helper = (300, 660, "barca", "ИНЬЕСТА")
        elif kind == "penalty":
            bx, by = bez((540, gy + 420), (560, gy + 200), (600 if scene == "g_messi" else 470, gy - 60), ease(clamp((pre - 0.35) / 0.65)))
            shooter = (540 - 20 + 30 * ease(pre), gy + 520 - 80 * ease(pre)); helper = None
        elif kind == "freekick":
            if pre < 0.3: bx, by = 560, gy + 640
            else: bx, by = bez((560, gy + 640), (300, gy + 150), (430, gy - 70), (pre - 0.3) / 0.7)
            shooter = (600, gy + 720 - 40 * ease(pre * 3)); helper = None
        elif kind == "cross":
            if pre < 0.6: bx, by = bez((830, 980), (900, 520), (600, 330 + gy - 300 + 140), pre / 0.6)
            else: bx, by = bez((600, gy + 140), (560, gy + 60), (520, gy - 60), (pre - 0.6) / 0.4)
            shooter = (lerp(520, 600, ease(pre)), lerp(700, gy + 170, ease(pre))); helper = (830, 1030, "barca", "НЕЙМАР")
        else:  # cavani volley into Barça net
            if pre < 0.55: bx, by = bez((240, 980), (260, 700), (520, 620), pre / 0.55)
            else: bx, by = bez((520, 620), (520, 450), (560, gy - 60), (pre - 0.55) / 0.45)
            shooter = (540, 660); helper = None
        net_bulge = clamp((t - tg) / 0.12) * (1 - clamp((t - tg - 0.25) / 0.3))
        goal_net(cv, gy, bulge=net_bulge)
        # keeper
        kx = lerp(540, bx, clamp(pre * 1.2) * 0.75) if kind != "penalty" else lerp(540, 540 - (bx - 540) * 1.4, ease(clamp((pre - 0.5) / 0.4)))
        topdown(cv, kx, gy + 60, "keeper" if not psg_scores else (240, 120, 30), hair=(40, 30, 20), r=44)
        # defenders / wall
        if kind == "freekick":
            for i in range(5): topdown(cv, 400 + i * 70, gy + 420, defk, r=34, hair=(50, 35, 25))
        elif kind != "penalty":
            for (dx, dy) in [(380, 560), (680, 520), (760, 760)]:
                topdown(cv, dx + 20 * math.sin(t * 3 + dx), dy, defk, r=42, hair=(45, 32, 22))
        if helper:
            topdown(cv, helper[0], helper[1], helper[2], r=44, label=helper[3], hair=(40, 28, 20))
        lab = "КУРЗАВА" if kind == "owngoal" else name
        sk = "dark" if kind == "owngoal" else look.get("skin", "light")
        topdown(cv, shooter[0], shooter[1], "psg" if kind == "owngoal" else attk, r=48, label=lab, hair=look["hair"], skin=sk)
        if not after:
            ball(cv, bx, by, 24, rot=t * 14)
        # speed lines
        if kind != "penalty" or pre > 0.4:
            for k in range(3):
                cv.line([(bx + 30 + k * 18, by + 40 + k * 26), (bx + 70 + k * 18, by + 110 + k * 26)], (255, 255, 255), 4)
        scoreboard(cv, "БАР", "ПСЖ", *PREV[scene], minute, agg=PREV_AGG[scene])
    else:
        # ---------- phase B: close-up celebration (front view, like the reference character)
        tb = t - tg
        bg = (90, 10, 30) if psg_scores else (20, 40, 110)
        cv.rect(0, 0, W, H, bg, w=0)
        rays(cv, 540, 1150, t, mix(bg, (255, 255, 255), 0.12 if psg_scores else 0.18))
        crowd(cv, 1500, 1980, t, seed=5, jump=0 if psg_scores else 1.0,
              colors=[PSG_NAVY, PSG_RED] if psg_scores else None)
        if kind == "owngoal":
            person(cv, 540, 1000, 1.15, kit="psg", mood="sad", arms="head", t=t, label="КУРЗАВА (АВТОГОЛ)", **{k: v for k, v in look.items() if k != "number"})
        elif psg_scores:
            person(cv, 540, 950, 1.15, kit="psg", mood="shout", arms="fist", t=t, label=name, **look)
            cv.text(540, 560, "НУЖНО ЕЩЁ 3 ГОЛА", 70, (255, 255, 255), stroke=8)
        else:
            sc_ = 1.15 + 0.03 * math.sin(t * 8)
            person(cv, 540, 980, sc_, kit="barca", mood="shout", arms="up" if kind != "penalty" else "fist", t=t, label=name, **look)
        p = back(tb / 0.45)
        scoreboard(cv, "БАР", "ПСЖ", *score, minute, agg=agg, punch=max(0.0, 1 - tb / 0.5))
        if scene == "g_roberto":
            confetti(cv, t, tg)
        if not psg_scores and kind != "owngoal":
            cv.text(540, 520, "ГОООЛ!", 150 * (0.4 + 0.6 * p), (255, 222, 90), stroke=10)
        elif kind == "owngoal":
            cv.text(540, 520, "АВТОГОЛ!", 130 * (0.4 + 0.6 * p), (255, 222, 90), stroke=10)

def sc_final(cv, t, d):
    cv.rect(0, 0, W, H, (20, 40, 110), w=0)
    rays(cv, 540, 900, t, (40, 70, 150), n=16)
    crowd(cv, 1080, 1980, t, seed=11, jump=1.0, density=1.0)
    # advertising board with Messi standing on it (iconic celebration)
    cv.rect(60, 1180, 1020, 1300, (230, 230, 235), w=LW, r=6)
    cv.text(540, 1240, "ЛИГА ЧЕМПИОНОВ · 1/8 ФИНАЛА", 46, (30, 40, 90))
    person(cv, 540, 690 + 10 * math.sin(t * 7), 1.0, kit="barca", mood="shout", arms="up", t=t,
           skin="light", hair=(90, 56, 28), style="short", beard=True, number=10, label="МЕССИ")
    confetti(cv, t, -1.0, n=120, seed=21)
    scoreboard(cv, "БАР", "ПСЖ", 6, 1, "КОНЕЦ", agg="СУММА 6:5")
    if t > d - 3.6:
        p = back((t - (d - 3.6)) / 0.5)
        cv.rect(0, 1580, W, 1820, (17, 17, 20), w=0)
        cv.text(540, 1665, "РЕМОНТАДА", 140 * (0.5 + 0.5 * p), (255, 222, 90), stroke=10)
        cv.text(540, 1770, "впервые в истории ЛЧ отыгран дефицит в 4 мяча", 34, (255, 255, 255))

SCENES = {"paris": sc_paris, "paris_goals": sc_paris_goals, "coach": sc_coach, "campnou": sc_campnou, "final": sc_final}

# ---------------- subtitles (same look as the reference) ----------------
def sub_chunks(text, maxc=22):
    words = text.split(); out = []; cur = ""
    for w_ in words:
        if cur and len(cur) + 1 + len(w_) > maxc:
            out.append(cur); cur = w_
        else: cur = (cur + " " + w_).strip()
        if cur.endswith((".", "!", "?")) and len(cur) > 10: out.append(cur); cur = ""
    if cur: out.append(cur)
    return out

def subtitle_at(e, tl):
    """subtitle synced to the exact phrase timings; returns (text, hot, age)"""
    v0 = e["vo"] - e["start"]
    offs = TIMING[e["seg"]["id"]]; ph = e["seg"]["phrases"]
    for i, (a, b) in enumerate(offs):
        a += v0; b += v0
        nxt = offs[i + 1][0] + v0 if i + 1 < len(offs) else b + 0.3
        if a - 0.05 <= tl < nxt:
            ch = sub_chunks(ph[i]["sub"]); tot = sum(len(c) for c in ch); acc = 0
            for c in ch:
                ca = a + (b - a) * acc / tot; acc += len(c); cb = a + (b - a) * acc / tot
                if tl < cb or c is ch[-1]: return c, ph[i]["hot"], tl - max(ca, a)
    return None

def draw_sub(cv, sub):
    txt, hot, age = sub
    pop = 1 + 0.18 * (1 - clamp(age / 0.12))   # small "pop" when a subtitle appears
    if hot:
        cv.text(540, 1480, txt, 76 * pop, (255, 222, 90), stroke=9, sc=OUT)
    else:
        cv.text(540, 1480, txt, 66 * pop, (255, 255, 255), stroke=8, sc=OUT)

# ---------------- frame ----------------
def frame(T):
    global VIG
    e = next((x for x in TL if x["start"] <= T < x["end"]), TL[-1])
    tl = T - e["start"]; d = e["end"] - e["start"]; scn = e["seg"]["scene"]
    cv = Cv(NIGHT)
    tg = key_time(e)
    if scn in GOALS: sc_goal(cv, tl, d, scn, tg)
    else: SCENES[scn](cv, tl, d)
    st = subtitle_at(e, tl)
    if st: draw_sub(cv, st)
    im = cv.im.resize((W, H), Image.LANCZOS)
    # camera: shake + flash on goal
    if tg is not None and 0 <= tl - tg < 0.6:
        k = 1 - (tl - tg) / 0.6
        dx, dy = int(math.sin(T * 90) * 26 * k), int(math.cos(T * 77) * 26 * k)
        z = 1 + 0.06 * k
        cw, ch = int(W / z), int(H / z)
        im = im.crop(((W - cw) // 2 + dx, (H - ch) // 2 + dy, (W - cw) // 2 + dx + cw, (H - ch) // 2 + dy + ch)).resize((W, H))
        if tl - tg < 0.2:
            im = Image.blend(im, Image.new("RGB", (W, H), (255, 255, 255)), 0.7 * (1 - (tl - tg) / 0.2))
    # night lighting + vignette like the reference
    if VIG is None: VIG = vignette_img()
    im = Image.composite(im, Image.new("RGB", (W, H), (6, 8, 20)), VIG)
    # soft light beam from the left (as in reference)
    # scene transitions: quick dip
    fade = min(clamp(tl / 0.12), clamp((d - tl) / 0.12)) if not (e is TL[0] and tl < 0.12) else clamp(tl / 0.3)
    if e is TL[-1] and tl > d - 0.6: fade = clamp((d - tl) / 0.6)
    if fade < 1: im = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, fade)
    return im

def render_chunk(args):
    i0, i1, path = args
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-threads", "2", "-crf", "18", "-pix_fmt", "yuv420p", path],
                         stdin=subprocess.PIPE)
    for i in range(i0, i1):
        p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait()
    return path

if __name__ == "__main__":
    if sys.argv[1] == "frame":
        frame(float(sys.argv[2])).save(sys.argv[3])
    elif sys.argv[1] == "timeline":
        for e in TL: print(e["seg"]["id"], e["seg"]["scene"], round(e["start"], 2), round(e["end"], 2), key_time(e))
        print(goal_times())
    elif sys.argv[1] == "video":
        n = int(TOTAL * FPS); k = 3; os.makedirs("build", exist_ok=True)
        jobs = [(n * j // k, n * (j + 1) // k, f"build/part{j}.mp4") for j in range(k)]
        with Pool(k) as pool: parts = pool.map(render_chunk, jobs)
        open("build/list.txt", "w").write("".join(f"file '{os.path.basename(p)}'\n" for p in parts))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "build/list.txt", "-c", "copy", "build/video.mp4"], check=True)
        print("video ok")
