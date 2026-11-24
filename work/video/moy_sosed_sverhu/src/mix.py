"""Звук: голоса (каждый своим голосом) + шумы + своя музыка (синтез) -> build/audio.wav"""
import subprocess, wave, numpy as np
from timeline import TL, SHOTS, TOTAL
SR = 44100; N = int(TOTAL * SR)
rng = np.random.default_rng(3)
def t_(d): return np.arange(int(d * SR)) / SR
def add(buf, x, at, g=1.0):
    i = int(at * SR); n = min(len(x), N - i)
    if n > 0: buf[i:i + n] += x[:n] * g
def lp(x, a):  # однополюсный ФНЧ
    y = np.empty_like(x); s = 0.0
    for i in range(len(x)): s += a * (x[i] - s); y[i] = s
    return y
def lp_fast(x, cutoff):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / np.sqrt(1 + (f / cutoff) ** 4), len(x)).astype(np.float32)
def hz(m): return 440 * 2 ** ((m - 69) / 12)

# ---- голоса
voice = np.zeros(N, np.float32)
for l in TL:
    add(voice, np.load(f"audio/L{l['i']:02d}.npy"), l["start"])
# лёгкая «комната»
rev = np.zeros_like(voice)
for dly, g in ((0.031, 0.18), (0.047, 0.12), (0.071, 0.08), (0.11, 0.05)):
    k = int(dly * SR); rev[k:] += voice[:-k] * g
voice = voice + lp_fast(rev, 3000)

# ---- музыка соседки сверху (глухо через потолок)
sh = {s["name"]: s for s in SHOTS}
party_end = TL[2]["end"] + 0.1                    # «я выключу!» — и выключила
bpm = 122; b = 60 / bpm
party = np.zeros(int(party_end * SR) + SR, np.float32)
kick = np.sin(2 * np.pi * (50 + 90 * np.exp(-t_(0.3) * 30)) * t_(0.3)) * np.exp(-t_(0.3) * 9)
bassn = [36, 36, 39, 41]
for k in range(int(party_end / b) + 1):
    add_at = k * b
    i = int(add_at * SR); party[i:i + len(kick)] += kick[:len(party) - i]
    bt = t_(b * 0.9); bs = np.sign(np.sin(2 * np.pi * hz(bassn[(k // 2) % 4]) * bt)) * 0.25 * np.exp(-bt * 3)
    party[i:i + len(bs)] += bs[:len(party) - i]
party = lp_fast(party, 180)
pg = np.ones(len(party), np.float32)
d0 = sh["door"]["start"]
pg[int(d0 * SR):] = 1.6                           # у двери громче
party *= pg
party[int(party_end * SR):] *= 0
fade = int(0.05 * SR); party[int(party_end * SR) - fade:int(party_end * SR)] *= np.linspace(1, 0, fade)
sfx = np.zeros(N, np.float32)
add(sfx, party, 0, 0.55)

# ---- шумы
def knock():
    x = t_(0.12); n = rng.standard_normal(len(x)) * np.exp(-x * 60)
    return lp_fast(n.astype(np.float32), 500) * 2.2 + np.sin(2 * np.pi * 120 * x) * np.exp(-x * 40) * 0.6
for k in (0.35, 0.58, 0.81, 1.15): add(sfx, knock(), d0 + k, 0.9)
t_open = TL[2]["start"] - 0.9
x = t_(0.9); creak = np.sin(2 * np.pi * (300 + 180 * np.sin(x * 9)) * x + 3 * np.sin(2 * np.pi * 37 * x)) * np.exp(-x * 2.5) * (x < 0.8)
add(sfx, lp_fast(creak.astype(np.float32), 1500), t_open, 0.18)
st = sh["stop"]["start"]
x = t_(0.4); add(sfx, lp_fast((rng.standard_normal(len(x)) * np.exp(-x * 25)).astype(np.float32), 300) * 3 +
                np.sin(2 * np.pi * 70 * x) * np.exp(-x * 15), st + 0.03, 0.8)
kt = sh["kitchen"]
for k in np.arange(kt["start"], kt["end"], 2.2):          # «пуф» муки
    x = t_(0.5); add(sfx, lp_fast((rng.standard_normal(len(x)) * np.exp(-x * 8) * np.minimum(1, x * 30)).astype(np.float32), 2500), k, 0.12)
x = t_(2.5)
ding = sum(np.sin(2 * np.pi * f * x) * np.exp(-x * dcy) * a for f, dcy, a in ((1568, 1.6, 0.5), (3136, 3, 0.15), (4700, 5, 0.06)))
add(sfx, ding.astype(np.float32), sh["oven"]["start"] + 0.25, 0.45)
fs = sh["final"]["start"]
for k, f in ((0.05, 659), (0.45, 523)):
    x = t_(1.2); add(sfx, (np.sin(2 * np.pi * f * x) * np.exp(-x * 3)).astype(np.float32), fs + k, 0.3)

# ---- своя романтическая музыка: мягкое пианино + пэд (Fmaj7 Em7 Dm7 Cmaj7), 76 bpm
m0 = TL[10]["start"] - 0.2                         # «Будем печь заново» — начинается музыка
bpm = 76; bt = 60 / bpm
chords = [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]]
mus = np.zeros(N, np.float32)
def piano(m, d=2.2):
    x = t_(d); f = hz(m)
    y = sum(np.sin(2 * np.pi * f * h * x) * a * np.exp(-x * (1.5 + h)) for h, a in ((1, 1), (2, .35), (3, .12), (4, .05)))
    return (y * np.minimum(1, x * 200)).astype(np.float32)
arp = [0, 2, 1, 3, 2, 1, 3, 2]
k = 0; t = m0
while t < TOTAL:
    ch = chords[(k // 8) % 4]
    add(mus, piano(ch[arp[k % 8]] + 12, 2.0), t, 0.16)
    if k % 8 == 0:
        add(mus, piano(ch[0] - 12, 4.0), t, 0.28)
        x = t_(bt * 8); pad = sum(np.sin(2 * np.pi * hz(n) * x) for n in ch) * np.minimum(1, x / 1.2) * np.minimum(1, (bt * 8 - x) / 0.8)
        add(mus, pad.astype(np.float32), t, 0.03)
    if k % 8 == 0 and k // 8 >= 2:
        add(mus, piano(ch[3] + 24, 2.5), t + bt * 2, 0.07)          # мелодия-подголосок
    t += bt / 2; k += 1
mus = lp_fast(mus, 2800)
def rms_db(x): return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
VDB = rms_db(voice[np.abs(voice) > 0.01])
mus *= 10 ** ((VDB - 15 - rms_db(mus[np.abs(mus) > 1e-4])) / 20)
sfx *= 10 ** ((VDB - 9 - rms_db(sfx[np.abs(sfx) > 1e-4])) / 20)
g = np.ones(N, np.float32)
ov = sh["oven"]["start"]; tail = TL[-1]["end"]
g[:int(m0 * SR)] = 0
a, c = int(m0 * SR), int((m0 + 2) * SR); g[a:c] = np.linspace(0, 1, c - a)
a, c = int(ov * SR), int((ov + 1.0) * SR); g[a:c] = np.linspace(1, 1.5, c - a); g[c:] = 1.5
a = int(tail * SR); g[a:] = np.linspace(1.5, 2.2, N - a)
mus *= g

# ---- микс с приглушением музыки под голосом
def rms_db(x): return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
vm = voice[np.abs(voice) > 0.01]
env = np.convolve(np.abs(voice), np.ones(4410) / 4410, mode="same")
duck = 1 - 0.45 * np.clip(env / 0.03, 0, 1)
duck = np.convolve(duck, np.ones(8820) / 8820, mode="same").astype(np.float32)
tt = np.arange(N) / SR
fade = np.minimum(tt / 0.4, 1) * np.minimum((TOTAL - tt) / 1.0, 1)
out = (voice + (mus + sfx * 0.9) * duck) * fade
out /= max(1.0, np.abs(out).max() / 0.95)
with wave.open("build/audio.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("audio ok", round(N / SR, 2), "voice", round(rms_db(vm), 1), "music", round(rms_db(mus[mus != 0]), 1), "sfx", round(rms_db(sfx[sfx != 0]), 1))
