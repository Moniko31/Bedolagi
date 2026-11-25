"""Озвучка диктора (edge-tts ru-RU-DmitryNeural): реплика -> audio/sNN.npy + meta.json (длительности)."""
import asyncio, json, os, subprocess
import numpy as np, edge_tts
from script import LINES, VOICE
SR = 44100
os.makedirs("audio", exist_ok=True)
def sgn(x, u): return f"{'+' if x >= 0 else ''}{x}{u}"
async def synth(L, path):
    for k in range(20):
        try:
            await edge_tts.Communicate(L["t"], VOICE, rate=sgn(L["r"], "%"), pitch=sgn(L["p"], "Hz"),
                                       volume=sgn(L["v"], "%")).save(path)
            if os.path.getsize(path) > 2000: return
        except Exception: pass
        await asyncio.sleep(1 + k % 4)
    raise SystemExit("TTS failed: " + L["t"])
def load(mp3):
    raw = subprocess.check_output(["ffmpeg", "-loglevel", "error", "-i", mp3, "-af",
        "silenceremove=start_periods=1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse,"
        "highpass=f=70,equalizer=f=180:t=q:w=1:g=2,equalizer=f=3500:t=q:w=1.2:g=2,"
        "acompressor=threshold=-20dB:ratio=2.5:attack=6:release=120:makeup=1.6",
        "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"])
    a = np.frombuffer(raw, np.float32).copy(); return a * 0.85 / max(1e-6, np.abs(a).max())
async def main():
    meta = {}
    for L in LINES:
        mp3 = f"audio/{L['id']}.mp3"; await synth(L, mp3); a = load(mp3)
        np.save(f"audio/{L['id']}.npy", a); meta[L["id"]] = len(a) / SR
        print(L["id"], round(len(a) / SR, 2), L["t"], flush=True)
    json.dump(meta, open("audio/meta.json", "w"), indent=1)
    tot = sum(meta[L["id"]] + L["pause"] for L in LINES) + 0.5
    print("TOTAL", round(tot, 1))
asyncio.run(main())
