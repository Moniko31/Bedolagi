"""Звук v3: наша озвучка + фоновая музыка из TikTok (голос диктора вырезан Demucs)."""
import subprocess, wave, numpy as np
import render as R

SR = 44100
N = int(R.TOTAL * SR)
MUSIC = "sep/htdemucs/tiktok_audio/no_vocals.wav"
MUSIC_START = 0.0

def load(path, start=0.0):
    raw = subprocess.check_output(["ffmpeg", "-loglevel", "error", "-ss", str(start), "-i", path,
                                   "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"])
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768

def rms_db(x): return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)

voice = np.zeros(N, np.float32)
for e in R.TL:
    v = load(f"audio/{e['seg']['id']}.wav")
    i = int(e["vo"] * SR); voice[i:i + len(v)] += v[:N - i]

music = load(MUSIC, MUSIC_START)[:N]
music = np.pad(music, (0, N - len(music)))
vm = voice[np.abs(voice) > 0.01]
music *= 10 ** (((rms_db(vm) - 16) - rms_db(music)) / 20)   # музыка на 16 дБ тише голоса

# драматургия музыки: провал на голе Кавани, затишье перед голом Роберто, взрыв на голе
g = np.ones(N, np.float32)
gt = dict((scn, tg) for tg, scn in R.goal_times())
seg = {e["seg"]["scene"]: e for e in R.TL}
def ramp(t0, t1, v0, v1):
    a, b = int(t0 * SR), int(t1 * SR)
    g[a:b] = np.linspace(v0, v1, max(1, b - a))
c = gt["g_cavani"]; ramp(c - 0.3, c + 0.2, 1, 0.35); ramp(c + 0.2, seg["g_cavani"]["end"], 0.35, 0.35)
ramp(seg["g_cavani"]["end"], seg["g_cavani"]["end"] + 1.0, 0.35, 1)
r0, rg = seg["g_roberto"]["start"], gt["g_roberto"]
ramp(r0, rg - 0.2, 0.8, 0.15); ramp(rg - 0.2, rg, 0.15, 1.8); ramp(rg, seg["g_roberto"]["end"], 1.8, 1.4)
ramp(seg["final"]["start"], seg["final"]["end"], 1.4, 1.2)
music *= g

# ducking: под голосом музыка ещё на ~6 дБ тише, плавно
venv = np.convolve(np.abs(voice), np.ones(4410) / 4410, mode="same")
duck = 1 - 0.5 * np.clip(venv / 0.03, 0, 1)
duck = np.convolve(duck, np.ones(4410) / 4410, mode="same")
t = np.arange(N) / SR
fade = np.minimum(t / 0.5, 1) * np.minimum((R.TOTAL - t) / 1.5, 1)
mixed = voice + music * duck * fade
mixed /= max(1.0, np.abs(mixed).max() / 0.95)
with wave.open("build/audio.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mixed * 32767).astype(np.int16).tobytes())
print("audio ok", len(mixed) / SR, "voice dB", round(rms_db(vm), 1))
