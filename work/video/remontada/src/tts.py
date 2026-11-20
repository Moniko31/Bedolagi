import asyncio, json, subprocess, sys, os
import edge_tts
from script import SEGMENTS

RATE = sys.argv[1] if len(sys.argv) > 1 else "+10%"
VOICE = "ru-RU-DmitryNeural"
os.makedirs("audio", exist_ok=True)

async def main():
    out = {}
    for s in SEGMENTS:
        mp3 = f"audio/{s['id']}.mp3"
        for attempt in range(40):
            try:
                await edge_tts.Communicate(s["say"], VOICE, rate=RATE, pitch="-4Hz").save(mp3); break
            except Exception as e:
                print("retry", s["id"], attempt); await asyncio.sleep(1 + attempt % 5)
        else:
            raise SystemExit("TTS failed " + s["id"])
        wav = f"audio/{s['id']}.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-af",
                        "silenceremove=start_periods=1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse,silenceremove=stop_periods=-1:stop_duration=0.3:stop_threshold=-50dB:stop_silence=0.28",
                        "-ar", "44100", "-ac", "1", wav], check=True)
        d = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wav]))
        out[s["id"]] = d
        print(s["id"], round(d, 2))
    json.dump(out, open("audio/durations.json", "w"))
    print("TOTAL", round(sum(out.values()), 2))

asyncio.run(main())
