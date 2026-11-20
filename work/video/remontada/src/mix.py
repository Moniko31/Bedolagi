import subprocess, wave, numpy as np
import render as R

SR = 44100
N = int(R.TOTAL * SR)
rng = np.random.default_rng(1)

def load(path):
    raw = subprocess.check_output(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"])
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768

def lowpass(x, a):  # one-pole, vectorised via cumulative trick is hard; use FFT filter
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / (1 + (f / a) ** 2), len(x))

def bandpass(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x))

voice = np.zeros(N, np.float32)
for e in R.TL:
    v = load(f"audio/{e['seg']['id']}.wav")
    i = int(e["vo"] * SR); voice[i:i + len(v)] += v[:N - i]

# crowd bed: band-limited noise, level per scene
crowd = bandpass(rng.standard_normal(N), 200, 1200).astype(np.float32)
crowd /= np.abs(crowd).max()
lvl = np.zeros(N, np.float32)
LV = {"paris": 0.0, "paris_goals": 0.0, "coach": 0.0, "campnou": 0.10, "final": 0.12}
for e in R.TL:
    a, b = int(e["start"] * SR), int(e["end"] * SR)
    lvl[a:b] = LV.get(e["seg"]["scene"], 0.05)
k = int(0.4 * SR); lvl = np.convolve(lvl, np.ones(k) / k, mode="same").astype(np.float32)
bed = crowd * lvl

# goal roars + impact hits
fx = np.zeros(N, np.float32)
for tg, scn in R.goal_times():
    i = int(tg * SR); L = int(3.2 * SR)
    t = np.arange(L) / SR
    env = np.minimum(t / 0.25, 1) * np.exp(-np.maximum(t - 0.6, 0) / 1.1)
    big = 1.5 if scn == "g_roberto" else (0.3 if scn == "g_cavani" else 1.0)
    roar = bandpass(rng.standard_normal(L), 250, 1600)
    roar = roar / np.abs(roar).max() * env * 0.22 * big
    hit = np.sin(2 * np.pi * 52 * t) * np.exp(-t / 0.35) * 0.55
    seg = (roar + hit).astype(np.float32)
    fx[i:i + L] += seg[:max(0, min(L, N - i))]

def whistle(t0, dur):
    L = int(dur * SR); t = np.arange(L) / SR
    w = np.sin(2 * np.pi * (2950 + 60 * np.sin(2 * np.pi * 28 * t)) * t) * np.minimum(t / 0.02, 1) * np.minimum((dur - t) / 0.05, 1) * 0.18
    i = int(t0 * SR); fx[i:i + L] += w[:max(0, min(L, N - i))].astype(np.float32)

camp = next(e for e in R.TL if e["seg"]["scene"] == "campnou")
whistle(camp["end"] - 0.6, 0.45)                     # kick-off
fin = R.TL[-1]
for k_, d_ in enumerate([0.25, 0.25, 0.8]):          # final whistle
    whistle(fin["start"] + 0.1 + k_ * 0.35, d_)

# low tension drone under the whole piece (rises toward the end)
t = np.arange(N) / SR
drone = (np.sin(2 * np.pi * 55 * t) + 0.5 * np.sin(2 * np.pi * 82.5 * t)) * (0.012 + 0.02 * t / R.TOTAL)
drone *= np.minimum(t / 1.0, 1) * np.minimum((R.TOTAL - t) / 1.5, 1)

# ducking: lower bed/fx under the voice
venv = np.convolve(np.abs(voice), np.ones(2205) / 2205, mode="same")
duck = 1 - 0.8 * np.clip(venv / 0.04, 0, 1)
mixed = voice * 1.0 + (bed + fx * 0.8) * duck + drone
mixed /= max(1.0, np.abs(mixed).max() / 0.95)
with wave.open("build/audio.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mixed * 32767).astype(np.int16).tobytes())
print("audio ok", len(mixed) / SR)
