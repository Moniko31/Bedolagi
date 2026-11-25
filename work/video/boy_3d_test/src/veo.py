#!/usr/bin/env python3
"""Generate a video with Google Veo via the Gemini API.

Usage:
  veo_env/bin/python veo.py --list
  veo_env/bin/python veo.py "prompt" -o out.mp4 [--image frame.png] [--model ...] [--aspect 9:16]

Needs GEMINI_API_KEY in the environment (billing enabled on the Google project).
"""
import argparse
import os
import sys
import time

from google import genai
from google.genai import types

DEFAULT_MODEL = "veo-3.0-fast-generate-001"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("prompt", nargs="?")
    p.add_argument("-o", "--out", default="veo_out.mp4")
    p.add_argument("--image", help="first frame (image-to-video)")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--aspect", default="9:16", choices=["9:16", "16:9"])
    p.add_argument("--negative", help="negative prompt")
    p.add_argument("--list", action="store_true", help="list available Veo models")
    a = p.parse_args()

    if not os.environ.get("GEMINI_API_KEY"):
        sys.exit("GEMINI_API_KEY is not set")
    client = genai.Client()

    if a.list:
        for m in client.models.list():
            if "veo" in m.name:
                print(m.name)
        return
    if not a.prompt:
        p.error("prompt is required")

    kwargs = dict(
        model=a.model,
        prompt=a.prompt,
        config=types.GenerateVideosConfig(
            aspect_ratio=a.aspect,
            negative_prompt=a.negative,
        ),
    )
    if a.image:
        kwargs["image"] = types.Image.from_file(location=a.image)

    op = client.models.generate_videos(**kwargs)
    t0 = time.time()
    while not op.done:
        time.sleep(10)
        op = client.operations.get(op)
        print(f"  ...{int(time.time() - t0)}s", flush=True)

    if op.error:
        sys.exit(f"error: {op.error}")
    vids = op.response.generated_videos if op.response else None
    if not vids:
        sys.exit(f"no video returned (maybe filtered): {op.response}")
    v = vids[0].video
    client.files.download(file=v)
    v.save(a.out)
    print("saved", a.out)


if __name__ == "__main__":
    main()
