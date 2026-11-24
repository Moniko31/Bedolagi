"""Озвучка: каждая реплика своим голосом (edge-tts), обрезка тишины, огибающая для липсинка.
python tts.py   ONLY=3,5 — пересинтез отдельных реплик"""
import asyncio, json, os, subprocess
import numpy as np
import edge_tts
from script import LINES, VOICE

SR, FPS = 44100, 30
os.makedirs("audio", exist_ok=True)

def sgn(x, u): return f"{'+' if x >= 0 else ''}{x}{u}"

async def synth(L, path):
    for k in range(30):
        try:
            await edge_tts.Communicate(L["t"], VOICE[L["who"]], rate=sgn(L["r"] - 4, "%"),
                                       pitch=sgn(L["p"], "Hz"), volume=sgn(L["v"], "%")).save(path)
            if os.path.getsize(path) > 2000: return
        except Exception:
            pass
        await asyncio.sleep(1 + k % 4)
    raise SystemExit("TTS failed: " + L["t"])

def load_trim(mp3):
    raw = subprocess.check_output(["ffmpeg", "-loglevel", "error", "-i", mp3, "-af",
        "silenceremove=start_periods=1:start_threshold=-48dB,areverse,silenceremove=start_periods=1:start_threshold=-48dB,areverse,"
        "highpass=f=80,acompressor=threshold=-20dB:ratio=2.2:attack=8:release=140:makeup=1.5",
        "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"])
    return np.frombuffer(raw, np.float32).copy()

async def main():
    only = set(map(int, os.environ["ONLY"].split(","))) if os.environ.get("ONLY") else None
    meta = json.load(open("audio/meta.json")) if only else {}
    for i, L in enumerate(LINES):
        if only and i not in only: continue
        mp3 = f"audio/L{i:02d}.mp3"
        await synth(L, mp3)
        a = load_trim(mp3)
        a *= 0.8 / max(1e-6, np.abs(a).max())
        np.save(f"audio/L{i:02d}.npy", a)
        hop = SR // FPS
        env = [float(np.sqrt((a[j:j + hop] ** 2).mean())) for j in range(0, len(a), hop)]
        m = max(env) or 1
        meta[str(i)] = dict(dur=len(a) / SR, env=[round(min(1, e / m * 1.4), 3) for e in env])
        print(i, L["who"], round(len(a) / SR, 2), L["t"], flush=True)
    json.dump(meta, open("audio/meta.json", "w"))

asyncio.run(main())
