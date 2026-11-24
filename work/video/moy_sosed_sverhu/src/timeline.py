"""Общая шкала времени для картинки и звука."""
import json
from script import LINES, TAIL

META = json.load(open("audio/meta.json"))
FPS = 30
TL = []          # реплики: start, end, who, i
SHOTS = []       # кадры: name, start, end
cur = 0.0
for i, L in enumerate(LINES):
    if not SHOTS or SHOTS[-1]["name"] != L["shot"]:
        if SHOTS: SHOTS[-1]["end"] = cur
        SHOTS.append(dict(name=L["shot"], start=cur, end=None, lines=[]))
    s = cur + L["pre"]; e = s + META[str(i)]["dur"]
    TL.append(dict(i=i, who=L["who"], start=s, end=e, L=L))
    SHOTS[-1]["lines"].append(TL[-1])
    cur = e
TOTAL = round(cur + TAIL, 2)
SHOTS[-1]["end"] = TOTAL

def shot_at(T):
    for s in SHOTS:
        if s["start"] <= T < s["end"]: return s
    return SHOTS[-1]

def talk(who, T):
    """0..1 — насколько открыт рот персонажа в момент T (по огибающей голоса)."""
    for l in TL:
        if l["who"] == who and l["start"] <= T < l["end"]:
            env = META[str(l["i"])]["env"]; k = int((T - l["start"]) * FPS)
            return env[min(k, len(env) - 1)]
    return 0.0

def line_at(T, lag=0.35):
    """реплика для субтитра (держим чуть дольше после конца)"""
    for l in TL:
        if l["start"] - 0.05 <= T < l["end"] + lag: return l
    return None

def mood(who, T, default):
    """эмоция: из последней реплики этого персонажа в текущем кадре"""
    sh = shot_at(T); m = default
    for l in sh["lines"]:
        if l["who"] == who and l["start"] - 0.2 <= T: m = l["L"]["mood"]
    return m
