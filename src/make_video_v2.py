"""Les Guignols — Le Come-Back, v2 : marionnettes latex (images générées) animées.

- Images : marionnettes latex générées (Canva), une image par plan.
- Animation : mâchoire articulée façon marionnette à gaine (le bas du visage
  descend, l'intérieur de la bouche apparaît), dodelinement de tête, sac qui
  vibre quand le téléphone sonne, léger travelling avant.
- Son : voix caricaturées (voices.py), bruitages et applaudissements.
- Look : 4:3, grain et douceur vidéo des années 90, bandeau rouge du JT.

Usage : python3 src/make_video_v2.py [--preview]
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import audio
import voices
from episode1_v2 import SEGMENTS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
BUILD = os.path.join(ROOT, "build", "v2")
OUT = os.path.join(ROOT, "output")
FPS = 25
W, H = 1440, 1080
SR = audio.SR

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_COND = "/usr/share/fonts/truetype/roboto/unhinted/RobotoCondensed-Bold.ttf"
FONT_BLACK = "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Black.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# Repères dans les images 1456x1088 : bouche (centre x, ligne des lèvres y,
# demi-largeur), bas du menton, boîte de la tête et pivot (cou) pour le dodelinement.
RIGS = {
    "anchor": dict(img="anchor.png", focus=(735, 380), chars={
        "anchor": dict(mouth=(732, 434, 72), chin=500, open=22, head=(555, 25, 935, 525), pivot=(735, 540))}),
    "bardella": dict(img="bardella.png", focus=(720, 340), chars={
        "bardella": dict(mouth=(695, 458, 98), chin=612, open=34, head=(540, 15, 940, 625), pivot=(705, 640))}),
    "marine": dict(img="marine.png", focus=(720, 360), chars={
        "marine": dict(mouth=(728, 456, 90), chin=590, open=30, head=(465, 45, 965, 600), pivot=(720, 620))}),
    "marine_phone": dict(img="marine_phone.png", focus=(720, 400), chars={
        "marine": dict(mouth=(735, 466, 86), chin=588, open=28, head=None, pivot=None)}),
    "duo": dict(img="duo.png", focus=(728, 470), bag=(1112, 668, 1442, 942), phone=(305, 768, 415, 858), chars={
        "bardella": dict(mouth=(370, 447, 68), chin=538, open=22, head=(250, 125, 545, 548), pivot=(390, 560)),
        "marine": dict(mouth=(1003, 459, 60), chin=540, open=20, head=(815, 175, 1180, 548), pivot=(1000, 560))}),
}


def font(path, size):
    return ImageFont.truetype(path, size)


# ====================================================================== audio

def applause(dur=3.0, seed=5):
    """Applaudissements du public : des centaines de claquements aléatoires."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    out = np.zeros(n, np.float32)
    env = np.minimum(1, np.linspace(0, 6, n)) * np.minimum(1, np.linspace(4, 0, n) ** 1.5)
    clap_len = int(0.012 * SR)
    shape = np.exp(-np.linspace(0, 7, clap_len))
    for _ in range(int(dur * 260)):
        i = rng.integers(0, n - clap_len)
        out[i:i + clap_len] += rng.normal(0, 1, clap_len) * shape * rng.uniform(0.2, 1)
    # filtre passe-bande grossier
    out = np.convolve(out, np.ones(4) / 4, mode="same") - np.convolve(out, np.ones(40) / 40, mode="same")
    return (out / (np.abs(out).max() + 1e-6) * 0.6 * env).astype(np.float32)


SFX = dict(audio.SFX, applause=applause)


def build_timeline():
    os.makedirs(BUILD, exist_ok=True)
    t = 0.0
    timeline = []
    for i, seg in enumerate(SEGMENTS):
        seg = dict(seg)
        lines = []
        cursor = seg.get("lead", 0.12)
        for j, (spk, say, sub) in enumerate(seg.get("lines", [])):
            wav = voices.speak(spk, say, os.path.join(BUILD, f"line_{i:02d}_{j}.wav"))
            dur = len(wav) / SR
            lines.append(dict(speaker=spk, sub=sub, start=cursor, dur=dur, wav=wav,
                              env=audio.envelope(wav, FPS)))
            cursor += dur + 0.1
        seg["lines"] = lines
        seg["lines_end"] = cursor
        sfx = list(seg.get("sfx", []))
        sfx += [(name, cursor + at, vol) for name, at, vol in seg.get("sfx_after", [])]
        seg["sfx"] = sfx
        if seg.get("ring_from") is not None and seg.get("sfx_after"):
            seg["ring_from"] = cursor + seg["ring_from"]
        seg["dur"] = max(seg.get("dur", 0), cursor + seg.get("tail", 0.15) + seg.get("extra", 0))
        seg["t0"] = t
        t += seg["dur"]
        timeline.append(seg)
    return timeline, t


def mix_audio(timeline, total, path):
    rng = np.random.default_rng(0)
    out = rng.normal(0, 0.004, int((total + 4) * SR)).astype(np.float32)  # bruit de plateau

    def add(x, at, vol):
        i = int(at * SR)
        n = min(len(x), len(out) - i)
        out[i:i + n] += x[:n] * vol

    for seg in timeline:
        for ln in seg["lines"]:
            add(ln["wav"], seg["t0"] + ln["start"], 0.95)
        for name, at, vol in seg["sfx"]:
            add(SFX[name](), seg["t0"] + at, vol)
    out = out[:int(total * SR)]
    out /= max(1.0, np.abs(out).max() / 0.95)
    audio.save_wav(path, out)


# ====================================================================== animation

def mouth_open(seg, speaker, lt):
    for ln in seg["lines"]:
        if ln["speaker"] == speaker and ln["start"] <= lt < ln["start"] + ln["dur"]:
            k = int((lt - ln["start"]) * FPS)
            e = float(ln["env"][min(k, len(ln["env"]) - 1)])
            return min(1.0, e * 1.2) if e > 0.12 else 0.0
    return 0.0


def jaw(img, cx, ym, hw, chin, d):
    """Mâchoire de marionnette : on découpe le bas du visage et on le fait descendre."""
    if d < 1:
        return
    x0, x1 = int(cx - hw * 1.45), int(cx + hw * 1.45)
    y1 = int(chin + 30)
    region = img.crop((x0, ym, x1, y1))
    w, h = region.size
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).ellipse((w * 0.06, -h * 0.95, w * 0.94, h * 0.88), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(max(4, hw * 0.12)))
    # intérieur de la bouche (lentille sombre) + langue, bords adoucis
    inner = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d_ = ImageDraw.Draw(inner)
    d_.chord((cx - hw * 0.84, ym - d, cx + hw * 0.84, ym + d * 1.05), 0, 180, fill=(38, 8, 12, 255))
    d_.chord((cx - hw * 0.45, ym + d * 0.4, cx + hw * 0.45, ym + d * 1.2), 180, 360, fill=(110, 35, 45, 255))
    img.alpha_composite(inner.filter(ImageFilter.GaussianBlur(1.5)))
    img.paste(region, (x0, int(ym + d)), mask)


def head_move(img, box, pivot, angle, dy):
    """Dodelinement : rotation légère de la tête autour du cou, collée en fondu."""
    if box is None or (abs(angle) < 0.05 and abs(dy) < 0.5):
        return img
    pad = 40
    x0, y0, x1, y1 = box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad
    x0, y0 = max(0, x0), max(0, y0)
    crop = img.crop((x0, y0, x1, y1))
    rot = crop.rotate(angle, resample=Image.BICUBIC, center=(pivot[0] - x0, pivot[1] - y0),
                      translate=(0, dy))
    mask = Image.new("L", crop.size, 0)
    ImageDraw.Draw(mask).ellipse((pad * 0.6, pad * 0.6, crop.width - pad * 0.6, crop.height - pad * 0.2), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(pad * 0.45))
    img.paste(rot, (x0, y0), mask)
    return img


def shake_bag(img, box, t):
    x0, y0, x1, y1 = box
    crop = img.crop(box)
    ang = math.sin(t * 75) * 3.0
    dx = int(math.sin(t * 93) * 7)
    rot = crop.rotate(ang, resample=Image.BICUBIC, translate=(dx, 0))
    mask = Image.new("L", crop.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((8, 8, crop.width - 8, crop.height - 8), 30, fill=255)
    img.paste(rot, (x0, y0), mask.filter(ImageFilter.GaussianBlur(6)))
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2 + 40
    a = int(70 + 50 * math.sin(t * 20))
    g.ellipse((cx - 90, cy - 50, cx + 90, cy + 50), fill=(150, 210, 255, a))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(25)))


class Shot:
    def __init__(self, name):
        rig = RIGS[name]
        self.rig = rig
        self.base = Image.open(os.path.join(ASSETS, rig["img"])).convert("RGBA")

    def render(self, seg, lt, gt):
        img = self.base.copy()
        rig = self.rig
        for k, (name, c) in enumerate(rig["chars"].items()):
            o = mouth_open(seg, name, lt)
            cx, ym, hw = c["mouth"]
            jaw(img, cx, ym, hw, c["chin"], o * c["open"])
            if c.get("head"):
                ph = k * 1.9 + hash(seg.get("shot")) % 7
                ang = math.sin(gt * 6.5 + ph) * 1.6 * o + math.sin(gt * 1.1 + ph) * 0.7
                dy = -o * 5 + math.sin(gt * 1.7 + ph) * 1.5
                img = head_move(img, c["head"], c["pivot"], ang, dy)
        ring = seg.get("ring") is True or (seg.get("ring_from") is not None and lt >= seg["ring_from"])
        if rig.get("bag") and ring:
            shake_bag(img, rig["bag"], gt)
        if rig.get("phone") and any(n == "typing" and at <= lt < at + 1.4 for n, at, _ in seg["sfx"]):
            ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
            px0, py0, px1, py1 = rig["phone"]
            ImageDraw.Draw(ov).rounded_rectangle((px0 + 12, py0 + 6, px1 - 12, py1 - 30), 8,
                                                 fill=(140, 200, 255, 120))
            img.alpha_composite(ov.filter(ImageFilter.GaussianBlur(3)))
        # léger travelling avant vers le visage + caméra « portée »
        p = min(1.0, lt / max(seg["dur"], 0.1))
        z = 1.0 + 0.035 * p
        fx, fy = rig["focus"]
        vw, vh = img.width / z, img.height / z
        cx = img.width / 2 + (fx - img.width / 2) * (1 - 1 / z) + math.sin(gt * 0.8) * 2
        cy = img.height / 2 + (fy - img.height / 2) * (1 - 1 / z) + math.sin(gt * 1.1) * 1.5
        cx = min(max(cx, vw / 2), img.width - vw / 2)
        cy = min(max(cy, vh / 2), img.height - vh / 2)
        return img.resize((W, H), Image.LANCZOS, box=(cx - vw / 2, cy - vh / 2, cx + vw / 2, cy + vh / 2))


# ====================================================================== habillage

def tv_look(img, gt):
    """Douceur, grain et petit décalage chroma d'une diffusion vidéo années 90."""
    img = img.convert("RGB").filter(ImageFilter.GaussianBlur(0.7))
    a = np.asarray(img).astype(np.int16)
    a[..., 0] = np.roll(a[..., 0], 2, axis=1)
    rng = np.random.default_rng(int(gt * FPS))
    a += rng.normal(0, 4, a.shape[:2]).astype(np.int16)[..., None]
    a = (a * 0.97 + 6).clip(0, 255).astype(np.uint8)
    return Image.fromarray(a)


def tag(img, text):
    """Petit bandeau rouge en bas à gauche, comme au JT des Guignols."""
    d = ImageDraw.Draw(img)
    f = font(FONT_COND, 54)
    d.rectangle((70, 735, 150, 790), fill=(205, 25, 30))
    d.text((168, 732), text, font=f, fill=(255, 255, 255), stroke_width=2, stroke_fill=(60, 0, 0))


def wrap_px(d, text, f, maxw):
    rows, cur = [], ""
    for w in text.split():
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=f) <= maxw or not cur:
            cur = trial
        else:
            rows.append(cur)
            cur = w
    rows.append(cur)
    if len(rows) > 1 and len(rows[-1]) <= 2:
        rows[-2] += " " + rows.pop()
    return rows


def subtitles(img, seg, lt):
    d = ImageDraw.Draw(img)
    f = font(FONT_BOLD, 40)
    for ln in seg["lines"]:
        if ln["sub"] and ln["start"] - 0.05 <= lt < ln["start"] + ln["dur"] + 0.25:
            rows = wrap_px(d, ln["sub"], f, W - 160)
            y = H - 40 - 52 * len(rows)
            for r in rows:
                tw = d.textlength(r, font=f)
                d.text((W / 2 - tw / 2, y), r, font=f, fill=(255, 255, 255), stroke_width=5, stroke_fill=(0, 0, 0))
                y += 52


def title_card(lt, gt):
    """Générique : un globe dans les étoiles, comme l'ouverture des Guignols."""
    img = Image.new("RGB", (W, H), (2, 2, 10))
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(3)
    for _ in range(260):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        s = rng.uniform(0.6, 2.6)
        x = (x - gt * 40 * s) % W
        d.ellipse((x - s, y - s, x + s, y + s), fill=(255, 255, 255))
    r = 300
    globe = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0))
    yy, xx = np.mgrid[0:2 * r, 0:2 * r]
    nx, ny = (xx - r) / r, (yy - r) / r
    rr = np.sqrt(nx ** 2 + ny ** 2)
    shade = np.clip(1.1 - np.hypot(nx + 0.35, ny + 0.35) * 0.8, 0.15, 1)
    lat = np.arcsin(np.clip(ny, -1, 1))
    lon = np.arcsin(np.clip(nx / np.sqrt(np.clip(1 - ny ** 2, 1e-3, 1)), -1, 1)) + gt * 0.9
    grid = (np.abs(np.sin(lon * 6)) < 0.06) | (np.abs(np.sin(lat * 6)) < 0.06)
    land = (np.sin(lon * 3 + 1) * np.cos(lat * 4) + 0.4 * np.sin(lon * 7) * np.sin(lat * 5)) > 0.45
    rgb = np.where(land[..., None], np.array([70, 150, 80]), np.array([25, 75, 185])).astype(np.float32)
    rgb = np.where(grid[..., None], rgb * 0.6 + 100, rgb) * shade[..., None]
    alpha = np.clip((1 - rr) * r, 0, 1) * 255
    globe = Image.fromarray(np.dstack([rgb, alpha]).astype(np.uint8), "RGBA")
    zoom = 0.4 + 0.6 * min(1, lt / 1.2)
    g = globe.resize((int(2 * r * zoom), int(2 * r * zoom)))
    img.paste(g, (W // 2 - g.width // 2, H // 2 - g.height // 2 - 40), g)
    if lt > 0.7:
        f = font(FONT_BLACK, 150)
        txt = "LES GUIGNOLS"
        tw = d.textlength(txt, font=f)
        d.text((W / 2 - tw / 2, 650), txt, font=f, fill=(255, 255, 255), stroke_width=8, stroke_fill=(200, 20, 30))
    if lt > 1.3:
        f2 = font(FONT_BLACK, 64)
        txt = "LE COME-BACK"
        tw = d.textlength(txt, font=f2)
        d.rectangle((W / 2 - tw / 2 - 26, 840, W / 2 + tw / 2 + 26, 930), fill=(205, 25, 30))
        d.text((W / 2 - tw / 2, 845), txt, font=f2, fill=(255, 255, 255))
    return img


def end_card(subtitle="« Ce n'est pas mon écriture »"):
    img = Image.new("RGB", (W, H), (8, 10, 28))
    d = ImageDraw.Draw(img)

    def center(txt, y, f, col):
        tw = d.textlength(txt, font=f)
        d.text((W / 2 - tw / 2, y), txt, font=f, fill=col)

    center("LES GUIGNOLS — LE COME-BACK", 170, font(FONT_BLACK, 72), (255, 255, 255))
    center(subtitle, 270, font(FONT_BOLD, 46), (255, 210, 60))
    txt = ("PARODIE. Marionnettes caricaturales, voix de synthèse et répliques entièrement inventées. "
           "Mediapart affirme avoir authentifié des messages de 2013 attribués à Jordan Bardella ; "
           "celui-ci conteste en être l'auteur et a annoncé une plainte pour faux et diffamation.")
    y = 420
    f = font(FONT_REG, 34)
    for row in wrap_px(d, txt, f, W - 260):
        center(row, y, f, (215, 220, 240))
        y += 48
    center("Une idée de Noa · réalisé avec Claude", 880, font(FONT_BOLD, 34), (255, 210, 60))
    return img


# ====================================================================== main

def main():
    preview = "--preview" in sys.argv
    os.makedirs(OUT, exist_ok=True)
    timeline, total = build_timeline()
    print(f"Durée : {total:.1f} s, {len(timeline)} plans", flush=True)
    wav = os.path.join(BUILD, "mix.wav")
    mix_audio(timeline, total, wav)

    shots = {name: Shot(name) for name in RIGS}
    end = end_card()
    out = os.path.join(OUT, "guignols_comeback_ep1_v2.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
                           "-c:v", "libx264", "-preset", "medium", "-crf", "25", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "192k", "-shortest", out], stdin=subprocess.PIPE)
    n = int(total * FPS)
    si = 0
    for f in range(n):
        gt = f / FPS
        while si < len(timeline) - 1 and gt >= timeline[si]["t0"] + timeline[si]["dur"]:
            si += 1
        seg = timeline[si]
        lt = gt - seg["t0"]
        shot = seg["shot"]
        if shot == "title":
            frame = title_card(lt, gt)
        elif shot == "end":
            frame = end.copy()
        else:
            frame = shots[shot].render(seg, lt, gt)
            frame = tv_look(frame, gt)
            if seg.get("tag"):
                tag(frame, seg["tag"])
            subtitles(frame, seg, lt)
        frame = frame.convert("RGB")
        if preview and f % 12 == 0:
            frame.resize((480, 360)).save(os.path.join(BUILD, f"p_{f:05d}.png"))
        ff.stdin.write(frame.tobytes())
        if f % 100 == 0:
            print(f"  {f}/{n}", flush=True)
    ff.stdin.close()
    ff.wait()
    print("OK ->", out)


if __name__ == "__main__":
    main()
