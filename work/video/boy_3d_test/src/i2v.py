import base64, sys, shutil
from gradio_client import Client
src, out, prompt = sys.argv[1], sys.argv[2], sys.argv[3]
dur = float(sys.argv[4]) if len(sys.argv) > 4 else 3.5
b64 = "data:image/png;base64," + base64.b64encode(open(src, "rb").read()).decode()
neg = "text, subtitles, watermark, static, blurry, low quality, deformed face, extra fingers, distorted hands, morphing"
c = Client("prithivMLmods/Wan2.2-Fast", verbose=False)
r = c.predict(image_b64=b64, prompt=prompt, steps=6, negative_prompt=neg, duration_seconds=dur,
              guidance_scale=1.0, guidance_scale_2=1.0, seed=42, randomize_seed=False, api_name="/generate_video")
print({k: (v[:80] if isinstance(v, str) else v) for k, v in r.items()})
v = r.get("video") or r.get("video_b64") or r.get("path")
if isinstance(v, dict): v = v.get("path") or v.get("url")
if v and v.startswith("data:"):
    open(out, "wb").write(base64.b64decode(v.split(",", 1)[1]))
elif v and v.startswith("http"):
    import urllib.request; urllib.request.urlretrieve(v, out)
elif v:
    shutil.copy(v, out)
print("saved", out)
