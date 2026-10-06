"""Anime une liste de plans avec SadTalker en ne chargeant les modèles qu'une fois.

À lancer avec l'environnement SadTalker (dépendances anciennes, séparé) :
  cd /home/user/SadTalker && /home/user/st-venv/bin/python <repo>/src/sadtalker_batch.py jobs.json

jobs.json : [{"image": ..., "audio": ..., "out": ..., "pose_style": 0, "expression_scale": 1.3}, ...]
Chaque sortie est une vidéo à la taille de l'image source (visage animé recollé).
"""
import json
import os
import shutil
import sys
import tempfile

import torch

sys.path.insert(0, os.getcwd())
from src.utils.preprocess import CropAndExtract  # noqa: E402
from src.test_audio2coeff import Audio2Coeff  # noqa: E402
from src.facerender.animate import AnimateFromCoeff  # noqa: E402
from src.generate_batch import get_data  # noqa: E402
from src.generate_facerender_batch import get_facerender_data  # noqa: E402
from src.utils.init_path import init_path  # noqa: E402

torch.set_num_threads(4)
DEVICE = "cpu"
SIZE = 256
PREPROCESS = "full"


def main(jobs_path):
    jobs = json.load(open(jobs_path))
    paths = init_path("./checkpoints", "./src/config", SIZE, False, PREPROCESS)
    pre = CropAndExtract(paths, DEVICE)
    a2c = Audio2Coeff(paths, DEVICE)
    render = AnimateFromCoeff(paths, DEVICE)
    cache = {}
    for k, job in enumerate(jobs):
        if os.path.exists(job["out"]):
            print(f"[{k + 1}/{len(jobs)}] déjà fait : {job['out']}", flush=True)
            continue
        print(f"[{k + 1}/{len(jobs)}] {os.path.basename(job['image'])} <- {os.path.basename(job['audio'])}", flush=True)
        work = tempfile.mkdtemp(prefix="st_")
        img = job["image"]
        if img not in cache:
            ff = os.path.join(work, "first")
            os.makedirs(ff, exist_ok=True)
            coeff, crop_pic, crop_info = pre.generate(img, ff, PREPROCESS, source_image_flag=True, pic_size=SIZE)
            keep = tempfile.mkdtemp(prefix="stsrc_")
            for f in os.listdir(ff):
                shutil.copy(os.path.join(ff, f), keep)
            cache[img] = (os.path.join(keep, os.path.basename(coeff)),
                          os.path.join(keep, os.path.basename(crop_pic)), crop_info)
        coeff, crop_pic, crop_info = cache[img]
        batch = get_data(coeff, job["audio"], DEVICE, None, still=job.get("still", False))
        coeff_path = a2c.generate(batch, work, job.get("pose_style", 0), None)
        data = get_facerender_data(coeff_path, crop_pic, coeff, job["audio"], 2, None, None, None,
                                   expression_scale=job.get("expression_scale", 1.0),
                                   still_mode=job.get("still", False), preprocess=PREPROCESS, size=SIZE)
        result = render.generate(data, work, img, crop_info, enhancer=None, background_enhancer=None,
                                 preprocess=PREPROCESS, img_size=SIZE)
        os.makedirs(os.path.dirname(job["out"]), exist_ok=True)
        shutil.move(result, job["out"])
        shutil.rmtree(work, ignore_errors=True)
        print(f"    -> {job['out']}", flush=True)
    print("TERMINE", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
