"""Фразовая озвучка: каждая фраза со своим темпом/тоном/громкостью, затем склейка с паузами
и обработка голоса (компрессия, «присутствие») для динамики.
python tts.py [базовый темп %]"""
import asyncio, json, subprocess, sys, os
import numpy as np
import edge_tts
from script import SEGMENTS

BASE = int(sys.argv[1]) if len(sys.argv) > 1 else 4
# чёткость: сужаем скачки тона/темпа/громкости, чтобы слова не «плыли»
PSCALE, RMAX, VMAX = 0.6, 16, 20
VOICE = "en-US-BrianMultilingualNeural"  # самый разборчивый по Whisper-тесту (vtest/)
SR = 44100
os.makedirs("audio/ph", exist_ok=True)

def sgn(x, unit): return f"{'+' if x >= 0 else ''}{x}{unit}"

async def synth(text, path, r, p, v):
    for attempt in range(40):
        try:
            await edge_tts.Communicate(text, VOICE, rate=sgn(r, "%"), pitch=sgn(p, "Hz"), volume=sgn(v, "%")).save(path)
            return
        except Exception:
            await asyncio.sleep(1 + attempt % 5)
    raise SystemExit("TTS failed: " + text)

def load_trim(mp3):
    raw = subprocess.check_output(["ffmpeg", "-loglevel", "error", "-i", mp3, "-af",
        "silenceremove=start_periods=1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse,"
        "silenceremove=stop_periods=-1:stop_duration=0.25:stop_threshold=-50dB:stop_silence=0.2",
        "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"])
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768

async def main():
    ONLY = os.environ.get("ONLY", "").split(",") if os.environ.get("ONLY") else None
    durs, timing = ({}, {}) if not ONLY else (json.load(open("audio/durations.json")), json.load(open("audio/timing.json")))
    for s in SEGMENTS:
        if ONLY and s["id"] not in ONLY: continue
        parts, offs, t = [], [], 0.0
        for i, p in enumerate(s["phrases"]):
            mp3 = f"audio/ph/{s['id']}_{i}.mp3"
            await synth(p["t"], mp3, BASE + min(p["r"], RMAX), round(p["p"] * PSCALE), min(p["v"], VMAX))
            a = load_trim(mp3)
            offs.append([t, t + len(a) / SR])
            pz = max(p["pause"], 0.12) if i + 1 < len(s["phrases"]) else p["pause"]
            parts += [a, np.zeros(int(pz * SR), np.float32)]
            t += len(a) / SR + pz
        x = np.concatenate(parts)
        raw = (np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes()
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-",
                        "-af", "highpass=f=100,equalizer=f=250:t=q:w=1:g=-2,equalizer=f=2500:t=q:w=1.4:g=3,equalizer=f=7000:t=q:w=1:g=-1.5,"
                               "acompressor=threshold=-18dB:ratio=2.5:attack=8:release=150:makeup=2",
                        f"audio/{s['id']}.wav"], input=raw, check=True)
        durs[s["id"]] = t; timing[s["id"]] = offs
        print(s["id"], round(t, 2), flush=True)
    json.dump(durs, open("audio/durations.json", "w"))
    json.dump(timing, open("audio/timing.json", "w"))
    print("TOTAL", round(sum(durs.values()), 2))

asyncio.run(main())
