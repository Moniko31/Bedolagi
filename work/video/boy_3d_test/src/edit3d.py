import base64, json, sys
from gradio_client import Client
src, out, prompt = sys.argv[1], sys.argv[2], sys.argv[3]
seed = int(sys.argv[4]) if len(sys.argv) > 4 else 42
b64 = "data:image/png;base64," + base64.b64encode(open(src, "rb").read()).decode()
c = Client("prithivMLmods/Qwen-Image-Edit-2511-LoRAs-Fast", verbose=False)
r = c.predict(images_b64_json=json.dumps([b64]), prompt=prompt, lora_adapter="Pixar-Inspired-3D",
              seed=seed, randomize_seed=False, guidance_scale=1.0, steps=4, api_name="/edit_image")
if r.get("status") != "success":
    sys.exit(f"fail: {r}")
open(out, "wb").write(base64.b64decode(r["image"].split(",", 1)[1]))
print("saved", out, "seed", r.get("seed"))
