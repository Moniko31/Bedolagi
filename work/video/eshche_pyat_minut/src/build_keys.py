import json, base64
from script import LINES
# какие кадры делаем img2img от готового 3D-кадра спальни (сила изменения)
BED = {"s01": 0.45, "s06": 0.55, "s15": 0.55}
IP = {"s02": 0.25}   # крупный план руки — лицо почти не нужно
shots = []
for L in LINES:
    d = dict(id=L["id"], img=L["shot"])
    if L["id"] in BED: d["bed"] = BED[L["id"]]
    if L["id"] in IP: d["ip"] = IP[L["id"]]
    shots.append(d)
refs = {k: base64.b64encode(open(f"keys/{k}_ref.jpg", "rb").read()).decode() for k in ("face", "bed")}
t = open("kaggle_keys_template.py").read().replace("__SHOTS__", json.dumps(shots, ensure_ascii=False)).replace("__REFS__", json.dumps(refs))
open("../kaggle/pm_keys/gen.py", "w").write(t)
json.dump({"id": "johnsmith6769228/pm-keys", "title": "pm-keys", "code_file": "gen.py", "language": "python",
           "kernel_type": "script", "is_private": True, "enable_gpu": True, "enable_internet": True,
           "machine_shape": "NvidiaTeslaT4", "dataset_sources": [], "competition_sources": [], "kernel_sources": []},
          open("../kaggle/pm_keys/kernel-metadata.json", "w"))
print(len(t), "bytes")
