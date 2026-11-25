"""Шкала времени: длительность кадра = подводка + реплика + пауза + доп. время на действие."""
import json
from script import LINES
LEAD = 0.35
EXTRA = {"s01": 1.2, "s04": 1.0, "s05": 0.4, "s07": 0.2, "s08": 1.8, "s09": 0.6, "s10": 0.9, "s11": 0.9,
         "s12": 1.6, "s13": 0.2, "s14": 0.9, "s15": 1.2}
TITLE = 2.6           # финальная плашка с названием
meta = json.load(open("audio/meta.json"))
SHOTS, t = [], 0.0
for L in LINES:
    d = LEAD + meta[L["id"]] + L["pause"] + EXTRA.get(L["id"], 0)
    lead = LEAD + (EXTRA.get(L["id"], 0) if L["id"] in ("s01", "s04") else 0)   # тут сначала звук/действие, потом голос
    SHOTS.append(dict(id=L["id"], start=round(t, 3), end=round(t + d, 3), dur=round(d, 3),
                      vstart=round(t + lead, 3), vdur=meta[L["id"]], text=L["t"]))
    t += d
TOTAL = round(t + TITLE, 3)
if __name__ == "__main__":
    for s in SHOTS: print(s["id"], s["start"], s["dur"], s["text"])
    print("TOTAL", TOTAL)
