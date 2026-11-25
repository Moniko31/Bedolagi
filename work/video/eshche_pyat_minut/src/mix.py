"""Звук «Ещё пять минут»: диктор + синтезированные музыка и шумы -> build/audio.wav"""
import wave, numpy as np
from timeline import SHOTS, TOTAL
SR = 44100; N = int(TOTAL * SR); rng = np.random.default_rng(5)
S = {s["id"]: s for s in SHOTS}
def T(d): return np.arange(int(d * SR)) / SR
def add(buf, x, at, g=1.0):
    i = int(at * SR); n = min(len(x), N - i)
    if n > 0 and i >= 0: buf[i:i + n] += (x[:n] * g).astype(np.float32)
def lp(x, fc):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); return np.fft.irfft(X / np.sqrt(1 + (f / fc) ** 4), len(x)).astype(np.float32)
def hp(x, fc):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR) + 1e-3; return np.fft.irfft(X / np.sqrt(1 + (fc / f) ** 4), len(x)).astype(np.float32)
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def noise(d): return rng.standard_normal(int(d * SR)).astype(np.float32)
def env_adsr(d, a=0.005, r=None):
    x = T(d); e = np.minimum(1, x / a); return e if r is None else e * np.exp(-x * r)
def rms_db(x): x = x[np.abs(x) > 1e-4]; return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9) if len(x) else -120

# ---------- голос
voice = np.zeros(N, np.float32)
for s in SHOTS: add(voice, np.load(f"audio/{s['id']}.npy"), s["vstart"])
rev = np.zeros_like(voice)
for dly, g in ((0.023, .14), (0.041, .1), (0.067, .07), (0.097, .04)):
    k = int(dly * SR); rev[k:] += voice[:-k] * g
voice = voice + lp(rev, 3500)

# ---------- шумы
sfx = np.zeros(N, np.float32)
def beep(f=1760, d=0.11):
    x = T(d); return (np.sign(np.sin(2 * np.pi * f * x)) * 0.35 + np.sin(2 * np.pi * f * x)) * np.minimum(1, x / .003) * np.minimum(1, (d - x) / .01)
def alarm(at, dur, g=0.5):          # «пи-пи-пи-пи» с вибро-гулом
    k = 0
    while k * 0.5 < dur:
        for j in range(4): add(sfx, beep(), at + k * 0.5 + j * 0.13, g)
        k += 1
    x = T(dur); add(sfx, np.sin(2 * np.pi * 120 * x) * (np.sin(2 * np.pi * 2 * x) > 0) * 0.25, at, g)
def whoosh(at, d=0.7, up=True, g=0.5):
    n = noise(d); x = T(d); e = np.sin(np.pi * x / d) ** 2
    add(sfx, lp(hp(n, 300), 2500 if up else 1500) * e, at, g)
def thump(at, g=0.6):
    x = T(0.18); add(sfx, (np.sin(2 * np.pi * (60 + 80 * np.exp(-x * 30)) * x) * np.exp(-x * 22) + lp(noise(.18), 400) * np.exp(-x * 40)), at, g)
def tap(at, g=0.4):
    x = T(0.05); add(sfx, hp(noise(.05), 2000) * np.exp(-x * 120), at, g)
def chirp(at, g=0.18):
    for j in range(3):
        x = T(0.09); f = 3200 + 1200 * np.sin(np.pi * x / 0.09) + rng.uniform(-200, 200)
        add(sfx, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * x / .09), at + j * 0.12, g)
def ding(at, g=0.35):
    x = T(2.0); add(sfx, sum(np.sin(2 * np.pi * f * x) * np.exp(-x * d) * a for f, d, a in ((1318, 2, .6), (1975, 3, .3), (2637, 5, .12))), at, g)
def boing(at, g=0.35):
    x = T(0.5); add(sfx, np.sin(2 * np.pi * np.cumsum(200 + 300 * np.exp(-x * 6) * (1 + .3 * np.sin(2 * np.pi * 18 * x))) / SR) * np.exp(-x * 6), at, g)

alarm(S["s01"]["start"] + 0.15, S["s01"]["dur"] - 0.2 + 1.2, 0.5)       # звенит до нажатия
tap(S["s02"]["start"] + 1.0, 0.6)
x = T(1.6); add(sfx, (np.sin(2 * np.pi * 523 * x) + .5 * np.sin(2 * np.pi * 784 * x)) * np.exp(-x * 2.2) * 0.3, S["s03"]["start"] + .1)  # «засыпание»
whoosh(S["s04"]["start"] - 0.3, 1.4, True, 0.45)
x = T(S["s04"]["dur"] + S["s05"]["dur"]); add(sfx, lp(noise(len(x) / SR), 500) * 0.12, S["s04"]["start"])                         # ветер в облаках
for k in (0.3, 1.1, 2.0): chirp(S["s05"]["start"] + k)
whoosh(S["s06"]["start"] - 0.25, 0.5, False, 0.5)                                                                                  # выход из сна
x = T(0.6); add(sfx, np.sin(2 * np.pi * np.cumsum(np.linspace(900, 300, len(x))) / SR) * np.exp(-x * 3) * .4, S["s07"]["start"] + 0.05)  # «шок»
whoosh(S["s08"]["start"] + 0.2, 0.5, True, 0.6); thump(S["s08"]["start"] + 1.1); boing(S["s08"]["start"] + 1.15)
x = T(S["s09"]["dur"] - 0.3); add(sfx, hp(noise(len(x) / SR), 2500) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 9 * x))) * 0.12, S["s09"]["start"] + .2)  # щётка
for k in np.arange(0.3, S["s10"]["dur"] - 0.2, 0.42): thump(S["s10"]["start"] + k, 0.35)
x = T(0.25); add(sfx, hp(noise(.25), 1500) * np.exp(-x * 18) * .3, S["s11"]["start"] + 0.5)                                     # хруст тоста
thump(S["s11"]["end"] - 0.4, 0.5)                                                                                                   # дверь
for k in np.arange(0.1, S["s12"]["dur"], 0.19): thump(S["s12"]["start"] + k, 0.22)                                                # шаги
x = T(S["s13"]["dur"]); add(sfx, lp(noise(len(x) / SR), 350) * (0.6 + 0.4 * np.sin(2 * np.pi * .3 * x)) * 0.16, S["s13"]["start"])   # ветер, пусто
ding(S["s14"]["vstart"] + 1.75)                                                                                                     # «суббота»
whoosh(S["s15"]["start"] - 0.2, 0.6, False, 0.3)

# ---------- музыка: 3 части (сон / спешка / суббота)
mus = np.zeros(N, np.float32)
def keys(m, d, bright=1.0):
    x = T(d); f = hz(m)
    y = sum(np.sin(2 * np.pi * f * h * x) * a * np.exp(-x * (1.8 + h * bright)) for h, a in ((1, 1), (2, .4), (3, .15), (4, .06)))
    return y * np.minimum(1, x * 300)
def celesta(m, d=1.5):
    x = T(d); f = hz(m); return (np.sin(2 * np.pi * f * x) + .3 * np.sin(2 * np.pi * 4 * f * x) * np.exp(-x * 8)) * np.exp(-x * 3) * np.minimum(1, x * 500)
def pluck(m, d=0.25):
    x = T(d); f = hz(m); return (np.sin(2 * np.pi * f * x) + .5 * np.sin(2 * np.pi * 2 * f * x)) * np.exp(-x * 18) * np.minimum(1, x * 800)
# 1) колыбельная: 0 .. начало s06; C - Am - F - G, 70 bpm
b = 60 / 70; prog = [[48, 52, 55], [45, 48, 52], [41, 45, 48], [43, 47, 50]]
mel = [76, 79, 77, 76, 74, 76, 72, 74, 76, 79, 81, 79, 77, 76, 74, 72]
end1 = S["s06"]["start"] - 0.1
t, k = 0.0, 0
while t < end1:
    ch = prog[(k // 4) % 4]
    if k % 4 == 0: add(mus, keys(ch[0] - 12, b * 4), t, .32); [add(mus, keys(n, b * 4), t, .12) for n in ch]
    if t > S["s03"]["start"] - 0.2: add(mus, celesta(mel[k % 16]), t, .16)        # мелодия входит с засыпанием
    t += b; k += 1
fade = np.ones(N, np.float32); i0, i1 = int((end1 - 0.8) * SR), int(end1 * SR); fade[i0:i1] = np.linspace(1, 0, i1 - i0); fade[i1:] = 0
mus *= fade
# 2) спешка: s07 .. конец s12; 150 bpm, пиццикато + бас + хай-хэт
part2 = np.zeros(N, np.float32)
b = 60 / 150; t0, t1 = S["s07"]["start"] + 0.3, S["s12"]["end"]
riff = [60, 64, 67, 72, 71, 67, 64, 62, 60, 64, 67, 69, 67, 64, 62, 59]
bass = [36, 36, 43, 43, 41, 41, 43, 43]
t, k = t0, 0
while t < t1:
    add(part2, pluck(riff[k % 16] + (5 if (k // 16) % 2 else 0)), t, .3)
    if k % 2 == 0: add(part2, keys(bass[(k // 2) % 8], b * 2, 3), t, .35)
    x = T(0.04); add(part2, hp(noise(.04), 6000) * np.exp(-x * 90), t + b / 2, .12)
    if k % 4 == 0: thump_x = T(0.15); add(part2, np.sin(2 * np.pi * (50 + 70 * np.exp(-thump_x * 35)) * thump_x) * np.exp(-thump_x * 20), t, .5)
    t += b / 2; k += 1
i1 = int(t1 * SR); part2[i1:] = 0; i0 = int((t1 - 0.15) * SR); part2[i0:i1] *= np.linspace(1, 0, i1 - i0)
mus += part2
# 3) суббота: с «Сегодня суббота» до конца — колыбельная в мажоре, ярче
b = 60 / 76; t = S["s14"]["vstart"] + 1.7; k = 0
prog3 = [[53, 57, 60], [48, 52, 55], [50, 53, 57], [43, 47, 50]]
mel3 = [81, 79, 77, 79, 76, 77, 79, 72, 81, 84, 83, 81, 79, 77, 76, 77]
while t < TOTAL - 0.5:
    ch = prog3[(k // 4) % 4]
    if k % 4 == 0: add(mus, keys(ch[0] - 12, b * 4), t, .3); [add(mus, keys(n, b * 4), t, .11) for n in ch]
    add(mus, celesta(mel3[k % 16]), t, .17)
    t += b; k += 1
mus = lp(mus, 5000)

# ---------- уровни и приглушение под голосом
VDB = rms_db(voice)
mus *= 10 ** ((VDB - 13 - rms_db(mus)) / 20)
sfx *= 10 ** ((VDB - 10 - rms_db(sfx)) / 20)
env = np.convolve(np.abs(voice), np.ones(4410) / 4410, mode="same")
duck = 1 - 0.5 * np.clip(env / 0.03, 0, 1); duck = np.convolve(duck, np.ones(6615) / 6615, mode="same").astype(np.float32)
tt = np.arange(N) / SR
out = (voice + mus * duck + sfx * (0.4 + 0.6 * duck)) * np.minimum(tt / 0.2, 1) * np.minimum((TOTAL - tt) / 1.2, 1)
out /= max(1.0, np.abs(out).max() / 0.95)
import os; os.makedirs("build", exist_ok=True)
with wave.open("build/audio.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())
print("audio ok", round(TOTAL, 2), "s; voice", round(VDB, 1), "music", round(rms_db(mus), 1), "sfx", round(rms_db(sfx), 1))
