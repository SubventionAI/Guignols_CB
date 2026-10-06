"""Netteté « dessin animé » sur les visages animés par SadTalker (Real-ESRGAN anime).

SadTalker rend le visage en 256 px puis le recolle dans l'image : le visage est
un peu flou. On repère la zone animée (différence avec l'image source), on la
réduit de moitié puis on la repasse en x2 avec le modèle realesr-animevideov3,
qui restitue des contours nets sans « réalisme photo ».

À lancer avec l'environnement SadTalker :
  /home/user/st-venv/bin/python src/enhance_faces.py build/v4/anim
"""
import glob
import os
import subprocess
import sys

import cv2
import numpy as np
import torch
from realesrgan import RealESRGANer
from realesrgan.archs.srvgg_arch import SRVGGNetCompact

torch.set_num_threads(4)
MODEL = "/home/user/SadTalker/esr/realesr-animevideov3.pth"


def load_upsampler():
    net = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=16, upscale=4, act_type="prelu")
    return RealESRGANer(scale=4, model_path=MODEL, model=net, half=False, device="cpu")


def face_box(frames, src):
    acc = np.zeros(src.shape[:2], np.float32)
    for fr in frames:
        acc = np.maximum(acc, np.abs(fr.astype(np.float32) - src.astype(np.float32)).mean(2))
    mask = cv2.GaussianBlur(acc, (0, 0), 5) > 12
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    pad = 30
    x0, y0 = max(0, xs.min() - pad), max(0, ys.min() - pad)
    x1, y1 = min(src.shape[1], xs.max() + pad), min(src.shape[0], ys.max() + pad)
    # dimensions paires pour la réduction x0.5
    return x0, y0, x0 + ((x1 - x0) // 2) * 2, y0 + ((y1 - y0) // 2) * 2


def enhance(video, src_path, up):
    out_path = video.replace(".mp4", "_hd.mp4")
    if os.path.exists(out_path):
        return
    src = cv2.imread(src_path)
    cap = cv2.VideoCapture(video)
    frames = []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        frames.append(cv2.resize(fr, (src.shape[1], src.shape[0])) if fr.shape[:2] != src.shape[:2] else fr)
    box = face_box(frames[::5], src)
    h, w = src.shape[:2]
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
                           "-s", f"{w}x{h}", "-r", "25", "-i", "-", "-c:v", "libx264", "-crf", "14",
                           "-pix_fmt", "yuv420p", out_path], stdin=subprocess.PIPE)
    if box is not None:
        x0, y0, x1, y1 = box
        bw, bh = x1 - x0, y1 - y0
        m = np.zeros((bh, bw), np.float32)
        cv2.ellipse(m, (bw // 2, bh // 2), (int(bw * 0.47), int(bh * 0.47)), 0, 0, 360, 1.0, -1)
        m = cv2.GaussianBlur(m, (0, 0), max(bw, bh) * 0.04)[..., None]
    for fr in frames:
        if box is not None:
            crop = fr[y0:y1, x0:x1]
            small = cv2.resize(crop, (bw // 2, bh // 2), interpolation=cv2.INTER_AREA)
            hd, _ = up.enhance(small, outscale=2)
            hd = cv2.resize(hd, (bw, bh))
            fr = fr.copy()
            fr[y0:y1, x0:x1] = (hd * m + crop * (1 - m)).astype(np.uint8)
        ff.stdin.write(fr.tobytes())
    ff.stdin.close()
    ff.wait()
    print("  HD :", os.path.basename(out_path), "zone", box, flush=True)


def main(anim_dir):
    up = load_upsampler()
    for v in sorted(glob.glob(os.path.join(anim_dir, "seg*_*.mp4"))):
        if v.endswith("_hd.mp4"):
            continue
        name = os.path.basename(v)[:-4]           # seg05_praud
        seg, char = name.split("_", 1)
        # retrouve l'image source de ce plan via jobs.json
        import json
        jobs = json.load(open(os.path.join(anim_dir, "jobs.json")))
        src = next(j["image"] for j in jobs if j["out"] == v)
        enhance(v, src, up)
    print("TERMINE", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
