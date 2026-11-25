"""Сборка: клипы clips/sNN.mp4 -> 1080x1920 30 fps по шкале времени, субтитры как в опорном кадре
(белый жирный с чёрной обводкой), финальная плашка, звук build/audio.wav -> eshche_pyat_minut.mp4"""
import json, os, subprocess, textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from timeline import SHOTS, TOTAL, TITLE
W, H, FPS = 1080, 1920, 30
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
os.makedirs("build/subs", exist_ok=True)
def run(c): subprocess.run(c, check=True)
def dur(p): return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))

def sub_png(text, path, size=70):
    f = ImageFont.truetype(FONT, size)
    lines = textwrap.wrap(text, 22)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    lh = size + 16; y = int(H * 0.80) - lh * len(lines) // 2
    for ln in lines:
        w = d.textlength(ln, font=f)
        d.text(((W - w) / 2, y), ln, font=f, fill="white", stroke_width=8, stroke_fill="black"); y += lh
    im.save(path)

# 1) каждый кадр: масштаб/кроп, подгонка длительности (замедление <= ~1.6x, иначе стоп-кадр в конце)
parts = []
for s in SHOTS:
    src, out = f"clips/{s['id']}.mp4", f"build/{s['id']}.mp4"
    L = dur(src); speed = min(1.0, L / s["dur"]) if L < s["dur"] else 1.0
    slow = max(speed, 0.62)
    vf = (f"setpts=PTS/{slow:.4f},minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir,"
          f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},"
          f"tpad=stop_mode=clone:stop_duration=5,trim=duration={s['dur']:.3f},setpts=PTS-STARTPTS,"
          f"eq=saturation=1.06:contrast=1.03,format=yuv420p")
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", vf, "-r", str(FPS), "-an", "-c:v", "libx264", "-crf", "16", "-preset", "medium", out])
    parts.append(out); print(s["id"], f"clip {L:.2f}s -> {s['dur']:.2f}s (x{slow:.2f})", flush=True)

# 2) финальная плашка: последний кадр, размытие, название
run(["ffmpeg", "-v", "error", "-y", "-sseof", "-0.1", "-i", parts[-1], "-frames:v", "1", "build/last.png"])
bg = Image.open("build/last.png").convert("RGB").filter(ImageFilter.GaussianBlur(18))
bg = Image.blend(bg, Image.new("RGB", bg.size, (10, 14, 40)), 0.35); d = ImageDraw.Draw(bg)
for txt, size, y in (("ЕЩЁ", 130, 0.40), ("ПЯТЬ МИНУТ", 118, 0.48), ("конец", 60, 0.60)):
    f = ImageFont.truetype(FONT, size); w = d.textlength(txt, font=f)
    d.text(((W - w) / 2, H * y), txt, font=f, fill=(255, 236, 170) if size > 100 else "white", stroke_width=10 if size > 100 else 5, stroke_fill="black")
bg.save("build/title.png")
run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", "build/title.png", "-t", str(TITLE), "-r", str(FPS),
     "-vf", f"fade=in:st=0:d=0.5,format=yuv420p", "-c:v", "libx264", "-crf", "16", "build/title.mp4"])
parts.append("build/title.mp4")
open("build/list.txt", "w").write("".join(f"file '{os.path.basename(p)}'\n" for p in parts))
run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "build/list.txt", "-c", "copy", "build/video.mp4"])

# 3) субтитры поверх + звук
inputs, chain, last = ["-i", "build/video.mp4"], [], "0:v"
for k, s in enumerate(SHOTS):
    p = f"build/subs/{s['id']}.png"; sub_png(s["text"], p); inputs += ["-i", p]
    a, b = s["vstart"] - 0.05, min(s["end"], s["vstart"] + s["vdur"] + 0.45)
    chain.append(f"[{last}][{k + 1}:v]overlay=0:0:enable='between(t,{a:.2f},{b:.2f})'[v{k}]"); last = f"v{k}"
inputs += ["-i", "build/audio.wav"]
run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(chain), "-map", f"[{last}]", "-map", f"{len(SHOTS) + 1}:a",
     "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
     "-t", f"{TOTAL:.3f}", "eshche_pyat_minut.mp4"])
print("done", round(dur("eshche_pyat_minut.mp4"), 2), "s")
