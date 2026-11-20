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
