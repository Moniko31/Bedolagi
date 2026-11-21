"""Озвучка голосом Piper Ruslan (локально, бесплатно).
У Piper нет управления интонацией, поэтому для каждой фразы:
  темп      -> --length-scale
  живость   -> --noise-scale / --noise-w (на «горячих» фразах больше вариативности)
  высота    -> rubberband pitch shift с сохранением тембра (formant=preserved)
  громкость -> усиление
Общая высота сдвинута к ~119 Гц (как у голоса из TikTok).
python tts_piper.py [базовый темп %]   ONLY=s01,s05 — пересинтез отдельных сцен
"""
import json, math, os, subprocess, sys
import numpy as np
from script import SEGMENTS

MODEL = "loc/ru_RU-ruslan-medium.onnx"
PIPER = ".venv/bin/piper"
BASE = int(sys.argv[1]) if len(sys.argv) > 1 else -8   # Ruslan говорит быстро; немного замедляем для чёткости
SR = 44100
F0_SRC, F0_DST = 130.0, 119.0                           # медиана тона Ruslan -> TikTok
GLOBAL_ST = 12 * math.log2(F0_DST / F0_SRC)
os.makedirs("audio/ph", exist_ok=True)

# Ударения и написания только для озвучки (проверено Whisper): Piper без них путает имена.
RESPELL = [
    ("Пэ Эс Жэ", "«Пари́ Сен-Жерме́н»"), ("Суарес головой", "Суа́рес голово́й"), ("Один — ноль", "Оди́н — но́ль"),
    ("Два — ноль", "Два́ — но́ль"), ("Три — ноль", "Три́ — но́ль"), ("Четыре — ноль", "Четы́ре — но́ль"),
    ("ноль — четыре", "но́ль — четы́ре"), ("Месси", "Ме́сси"), ("Кавани", "Кава́ни"), ("Серджи Роберто", "Се́рджи Робе́рто"),
    ("«Камп Ноу»", "«Ка́мп Но́у»"), ("Ремонтада", "Ремонта́да"), ("Ди Мария", "Ди Мари́я"), ("Дракслер", "Дра́кслер"),
    ("Курзава", "Курза́ва"), ("Неймар", "Нейма́р"), ("Луис Энрике", "Луи́с Энри́ке"),
]
def respell(t):
    for a, b in RESPELL: t = t.replace(a, b)
    return t

def synth(text, path, r, p, v, hot):
    tmp = path + ".raw.wav"
    r = max(-10, min(r, 6))                       # сильнее ускорять нельзя: слова смазываются
    ls = 1.0 / (1 + (BASE + r) / 100)
    ns, nw = (0.7, 0.85) if hot else (0.6, 0.75)
    subprocess.run([PIPER, "-m", MODEL, "-f", tmp, "--length-scale", f"{ls:.3f}", "--noise-scale", str(ns),
                    "--noise-w-scale", str(nw), "--sentence-silence", "0.15", "--volume", "0.55"],
                   input=respell(text).encode(), check=True, capture_output=True)
    st = GLOBAL_ST + 12 * math.log2((F0_DST + p) / F0_DST)
    gain = 20 * math.log10(1 + v / 100)
    af = (f"rubberband=pitch={2 ** (st / 12):.4f}:formant=preserved,volume={gain:.1f}dB,"
          "silenceremove=start_periods=1:start_threshold=-50dB,areverse,"
          "silenceremove=start_periods=1:start_threshold=-50dB,areverse")
    raw = subprocess.check_output(["ffmpeg", "-loglevel", "error", "-i", tmp, "-af", af,
                                   "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"])
    os.remove(tmp)
    return np.frombuffer(raw, np.float32).copy()

def main():
    only = os.environ.get("ONLY", "").split(",") if os.environ.get("ONLY") else None
    durs, timing = ({}, {}) if not only else (json.load(open("audio/durations.json")), json.load(open("audio/timing.json")))
    for s in SEGMENTS:
        if only and s["id"] not in only: continue
        parts, offs, t = [], [], 0.0
        for i, p in enumerate(s["phrases"]):
            a = synth(p["t"], f"audio/ph/{s['id']}_{i}.wav", p["r"], p["p"], p["v"], p["hot"])
            offs.append([t, t + len(a) / SR])
            pz = max(p["pause"], 0.12) if i + 1 < len(s["phrases"]) else p["pause"]
            parts += [a, np.zeros(int(pz * SR), np.float32)]
            t += len(a) / SR + pz
        x = np.concatenate(parts)
        x *= 0.7 / max(1e-6, np.abs(x).max())                # запас по громкости, без перегруза
        raw = (x * 32767).astype(np.int16).tobytes()
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-",
                        "-af", "highpass=f=90,equalizer=f=250:t=q:w=1:g=-2,equalizer=f=2800:t=q:w=1.4:g=3,"
                               "acompressor=threshold=-18dB:ratio=2.5:attack=8:release=150:makeup=2",
                        f"audio/{s['id']}.wav"], input=raw, check=True)
        durs[s["id"]] = t; timing[s["id"]] = offs
        print(s["id"], round(t, 2), flush=True)
    json.dump(durs, open("audio/durations.json", "w"))
    json.dump(timing, open("audio/timing.json", "w"))
    print("TOTAL", round(sum(durs.values()), 2))

main()
