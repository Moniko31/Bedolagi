# «Ещё пять минут»: ключевые кадры 3D (SDXL DreamShaper + IP-Adapter face / img2img от 3D-кадра), 2×T4.
import os, sys, json, time, subprocess, base64, io
T0 = time.time()
OUT = "/kaggle/working/out"; os.makedirs(OUT, exist_ok=True)
os.environ["HF_HOME"] = "/tmp/hf"; os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
def log(*a): print(f"[{(time.time()-T0)/60:6.1f}m]", *a, flush=True)
def sh(c): log("$", c); subprocess.run(c, shell=True, check=True)
SHOTS = json.loads(r'''__SHOTS__''')
REFS = json.loads(r'''__REFS__''')
STYLE = ("3D animated Pixar-style film still, stylized cartoon character, big expressive eyes, soft cinematic lighting, "
         "subsurface scattering, smooth shading, highly detailed, vertical composition")
BOY = "a 10 year old cartoon boy with spiky messy brown hair, big brown eyes, small nose, wearing a green long-sleeve shirt"
NEG = ("photo, photorealistic, realistic skin, anime, 2d, flat illustration, sketch, painting, text, letters, numbers, subtitles, "
       "watermark, logo, deformed, disfigured, extra fingers, extra limbs, bad hands, ugly, blurry, lowres, adult, girl")
W, H = 768, 1344

def run(rank, nw):
    import torch
    from PIL import Image
    from diffusers import StableDiffusionXLPipeline, StableDiffusionXLImg2ImgPipeline, DPMSolverMultistepScheduler
    from transformers import CLIPVisionModelWithProjection
    dec = lambda s: Image.open(io.BytesIO(base64.b64decode(s))).convert("RGB")
    face, bed = dec(REFS["face"]), dec(REFS["bed"]).resize((W, H), Image.LANCZOS)
    enc = CLIPVisionModelWithProjection.from_pretrained("h94/IP-Adapter", subfolder="models/image_encoder", torch_dtype=torch.float16)
    pipe = StableDiffusionXLPipeline.from_pretrained("Lykon/dreamshaper-xl-1-0", image_encoder=enc, torch_dtype=torch.float16,
                                                     variant="fp16").to("cuda")
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config, use_karras_sigmas=True)
    pipe.load_ip_adapter("h94/IP-Adapter", subfolder="sdxl_models", weight_name="ip-adapter-plus-face_sdxl_vit-h.safetensors")
    i2i = StableDiffusionXLImg2ImgPipeline.from_pipe(pipe)
    log(rank, "loaded")
    for i, s in enumerate(SHOTS):
        if i % nw != rank: continue
        for v in range(2):
            g = torch.Generator("cuda").manual_seed(1000 * i + 17 * v + 3)
            p = f"{STYLE}, {s['img'].replace('the boy', BOY, 1)}"
            if s.get("bed"):
                pipe.set_ip_adapter_scale(0.4)
                im = i2i(prompt=p, negative_prompt=NEG, image=bed, ip_adapter_image=face, strength=s["bed"],
                         num_inference_steps=36, guidance_scale=6.0, generator=g).images[0]
            else:
                pipe.set_ip_adapter_scale(s.get("ip", 0.55))
                im = pipe(prompt=p, negative_prompt=NEG, ip_adapter_image=face, width=W, height=H,
                          num_inference_steps=32, guidance_scale=6.0, generator=g).images[0]
            im.save(f"{OUT}/{s['id']}_{v}.jpg", quality=93); log(rank, s["id"], v)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run(int(sys.argv[1]), int(sys.argv[2])); sys.exit()
    sh("nvidia-smi --query-gpu=name,memory.total --format=csv")
    sh("pip install -q -U 'diffusers>=0.35' 'transformers>=4.53' accelerate hf_transfer sentencepiece 2>&1 | tail -2")
    import torch; n = max(1, torch.cuda.device_count()); me = os.path.abspath(__file__)
    ps = [subprocess.Popen(f"CUDA_VISIBLE_DEVICES={r} python {me} {r} {n}", shell=True) for r in range(n)]
    for p in ps: p.wait()
    log("ALL DONE", sorted(os.listdir(OUT)))
