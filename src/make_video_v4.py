"""Les Guignols — Le Come-Back, v4 : personnages 3D caricaturaux animés par IA.

Pipeline :
  1. prepare  : minutage (voix XTTS de la v3), piste audio par personnage et par
                plan, liste des animations à calculer (jobs.json).
  2. SadTalker (environnement séparé, src/sadtalker_batch.py) : visage animé par
                la voix (lèvres, mâchoire, joues, mouvements de tête, clignements).
  3. enhance  : netteté « dessin animé » du visage (Real-ESRGAN anime, src/enhance_faces.py).
  4. render   : montage final (plans, plan à deux, sac qui vibre, légendes,
                sous-titres, son, générique).

Usage : python3 src/make_video_v4.py prepare|render [--preview]
"""
import json
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import audio
from make_video_v2 import FPS, SFX, end_card, shake_bag, subtitles, tag, title_card
from make_video_v3 import build_timeline, caption, mix_audio

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets", "v4")
BUILD = os.path.join(ROOT, "build", "v4")
ANIM = os.path.join(BUILD, "anim")
OUT = os.path.join(ROOT, "output")
W, H = 1440, 1080
SR = audio.SR
IMG_W, IMG_H = 1456, 1088

# Pour chaque plan : image, et pour chaque personnage la zone de l'image qu'il occupe
# (le plan à deux est découpé en deux moitiés animées séparément).
SHOTS = {
    "praud": dict(img="praud.png", chars={"praud": (0, 0, IMG_W, IMG_H)}, focus=(700, 380)),
    "bardella": dict(img="bardella.png", chars={"bardella": (0, 0, IMG_W, IMG_H)}, focus=(728, 360)),
    "marine": dict(img="marine.png", chars={"marine": (0, 0, IMG_W, IMG_H)}, focus=(728, 380)),
    "marine_phone": dict(img="marine_phone.png", chars={"marine": (0, 0, IMG_W, IMG_H)}, focus=(728, 420)),
    "duo": dict(img="duo.png", chars={"bardella": (0, 0, 728, IMG_H), "marine": (728, 0, IMG_W, IMG_H)},
                focus=(728, 480), bag=(1215, 730, 1440, 900), phone=(395, 740, 485, 800)),
}
# Personnalité du mouvement : style de pose SadTalker et exagération des expressions
STYLE = {"praud": (12, 1.45), "bardella": (3, 1.25), "marine": (27, 1.25)}


def seg_audio_for(seg, char):
    """Piste de la durée du plan : les répliques de `char` à leur place, silence ailleurs."""
    n = int(round(seg["dur"] * FPS)) * (SR // FPS)
    out = np.zeros(n, np.float32)
    for ln in seg["lines"]:
        if ln["speaker"] == char:
            i = int(ln["start"] * SR)
            m = min(len(ln["wav"]), n - i)
            out[i:i + m] += ln["wav"][:m]
    return out


def prepare():
    os.makedirs(ANIM, exist_ok=True)
    timeline, total = build_timeline()
    print(f"Durée : {total:.1f} s", flush=True)
    crops = {}
    jobs = []
    for i, seg in enumerate(timeline):
        if seg["shot"] in ("title", "end"):
            continue
        shot = SHOTS[seg["shot"]]
        src = Image.open(os.path.join(ASSETS, shot["img"])).convert("RGB")
        for char, box in shot["chars"].items():
            key = (seg["shot"], char)
            if key not in crops:
                p = os.path.join(ANIM, f"src_{seg['shot']}_{char}.png")
                src.crop(box).save(p)
                crops[key] = p
            wav = os.path.join(ANIM, f"seg{i:02d}_{char}.wav")
            y = seg_audio_for(seg, char)
            y16 = audio_resample(y)
            audio.save_wav(wav + ".44k.wav", y)
            save16(wav, y16)
            pose, expr = STYLE[char]
            jobs.append(dict(image=crops[key], audio=wav, out=os.path.join(ANIM, f"seg{i:02d}_{char}.mp4"),
                             pose_style=pose, expression_scale=expr))
    json.dump(jobs, open(os.path.join(ANIM, "jobs.json"), "w"), indent=1)
    print(f"{len(jobs)} animations à calculer -> {ANIM}/jobs.json")


def audio_resample(y):
    import librosa
    return librosa.resample(y, orig_sr=SR, target_sr=16000)


def save16(path, y):
    import wave
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())


# ====================================================================== rendu final

class Clip:
    """Lecture séquentielle d'une animation (version nette si disponible)."""

    def __init__(self, path):
        enh = path.replace(".mp4", "_hd.mp4")
        self.cap = cv2.VideoCapture(enh if os.path.exists(enh) else path)
        self.last = None

    def next(self):
        ok, fr = self.cap.read()
        if ok:
            self.last = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
        return self.last


def soft_look(img):
    """Rendu propre et doux (pas de grain VHS) : léger contraste + vignette."""
    a = np.asarray(img.convert("RGB")).astype(np.float32)
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    vig = 1 - 0.18 * (((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    a = a * vig[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def render(preview=False):
    timeline, total = build_timeline()
    wav = os.path.join(BUILD, "mix.wav")
    mix_audio(timeline, total, wav)
    end = end_card("« C'est fou ce que les gens se ressemblent »")
    out = os.path.join(OUT, "guignols_comeback_ep1_v4.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
                           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "192k", "-shortest", out], stdin=subprocess.PIPE)
    n = int(total * FPS)
    si, clips = -1, {}
    for f in range(n):
        gt = f / FPS
        new_si = si
        while new_si < len(timeline) - 1 and gt >= timeline[max(new_si, 0)]["t0"] + timeline[max(new_si, 0)]["dur"]:
            new_si += 1
        new_si = max(new_si, 0)
        if new_si != si:
            si = new_si
            seg = timeline[si]
            clips = {}
            if seg["shot"] not in ("title", "end"):
                for char in SHOTS[seg["shot"]]["chars"]:
                    clips[char] = Clip(os.path.join(ANIM, f"seg{si:02d}_{char}.mp4"))
                base = Image.open(os.path.join(ASSETS, SHOTS[seg["shot"]]["img"])).convert("RGB")
        seg = timeline[si]
        lt = gt - seg["t0"]
        if seg["shot"] == "title":
            frame = title_card(lt, gt)
        elif seg["shot"] == "end":
            frame = end.copy()
        else:
            cfg = SHOTS[seg["shot"]]
            img = base.copy()
            for char, box in cfg["chars"].items():
                fr = clips[char].next()
                if fr is not None:
                    img.paste(fr.resize((box[2] - box[0], box[3] - box[1])), box[:2])
            img = img.convert("RGBA")
            ring = seg.get("ring") is True or (seg.get("ring_from") is not None and lt >= seg["ring_from"])
            if cfg.get("bag") and ring:
                shake_bag(img, cfg["bag"], gt)
            if cfg.get("phone") and any(nm == "typing" and at <= lt < at + 1.4 for nm, at, _ in seg["sfx"]):
                ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
                ImageDraw.Draw(ov).rounded_rectangle(cfg["phone"], 6, fill=(150, 205, 255, 110))
                img.alpha_composite(ov.filter(ImageFilter.GaussianBlur(3)))
            # travelling avant lent et doux
            p = min(1.0, lt / max(seg["dur"], 0.1))
            z = 1.0 + 0.04 * (0.5 - 0.5 * math.cos(math.pi * p))
            fx, fy = cfg["focus"]
            vw, vh = img.width / z, img.height / z
            cx = img.width / 2 + (fx - img.width / 2) * (1 - 1 / z)
            cy = img.height / 2 + (fy - img.height / 2) * (1 - 1 / z)
            frame = img.resize((W, H), Image.LANCZOS, box=(cx - vw / 2, cy - vh / 2, cx + vw / 2, cy + vh / 2))
            frame = soft_look(frame)
            if seg.get("tag"):
                tag(frame, seg["tag"])
            if seg.get("caption") and lt < 3.2:
                caption(frame, *seg["caption"])
            subtitles(frame, seg, lt)
        frame = frame.convert("RGB")
        if preview and f % 6 == 0:
            frame.resize((480, 360)).save(os.path.join(BUILD, f"p_{f:05d}.png"))
        ff.stdin.write(frame.tobytes())
        if f % 250 == 0:
            print(f"  {f}/{n}", flush=True)
    ff.stdin.close()
    ff.wait()
    print("OK ->", out)


if __name__ == "__main__":
    if sys.argv[1] == "prepare":
        prepare()
    else:
        render("--preview" in sys.argv)
