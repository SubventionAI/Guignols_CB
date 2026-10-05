"""Les Guignols — Le Come-Back. Épisode 1 : « Mais qui a bien pu écrire ça ? »

Génère la vidéo complète : voix, bruitages, animation des marionnettes, montage.
Usage : python3 src/make_video.py [--preview]
"""
import math
import os
import subprocess
import sys
import textwrap

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import audio
from episode1 import SEGMENTS
from puppets import (HEADS, body_suit, cat, hand, handbag, place_head, smartphone, soft, sweat_drop,
                     blob, head_bardella, head_marine)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
OUT = os.path.join(ROOT, "output")
FPS = 25
W, H = 1280, 720          # sortie
SW, SH = 2560, 1440       # plateau (rendu 2x puis recadré par la « caméra »)

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_BLACK = "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Black.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


# ====================================================================== timeline

def build_timeline():
    """Synthétise les répliques et calcule le minutage de chaque plan."""
    os.makedirs(BUILD, exist_ok=True)
    t = 0.0
    timeline = []
    for i, seg in enumerate(SEGMENTS):
        seg = dict(seg)
        lines = []
        cursor = seg.get("lead", 0.15)
        for j, (spk, say, sub) in enumerate(seg.get("lines", [])):
            wav = audio.tts(spk, say, os.path.join(BUILD, f"line_{i:02d}_{j}.wav"))
            dur = len(wav) / audio.SR
            lines.append(dict(speaker=spk, sub=sub, start=cursor, dur=dur, wav=wav,
                              env=audio.envelope(wav, FPS)))
            cursor += dur + 0.12
        seg["lines"] = lines
        seg["dur"] = max(seg.get("dur", 0), cursor + seg.get("tail", 0.25))
        seg["t0"] = t
        t += seg["dur"]
        timeline.append(seg)
    return timeline, t


def mix_audio(timeline, total, path):
    out = np.zeros(int((total + 1) * audio.SR), np.float32)

    def add(x, at, vol=1.0):
        i = int(at * audio.SR)
        n = min(len(x), len(out) - i)
        out[i:i + n] += x[:n] * vol

    for seg in timeline:
        for ln in seg["lines"]:
            add(ln["wav"], seg["t0"] + ln["start"], 0.95)
        for name, at, *rest in seg.get("sfx", []):
            vol = rest[0] if rest else 1.0
            add(audio.SFX[name](), seg["t0"] + at, vol)
    out = out[:int(total * audio.SR)]
    out /= max(1.0, np.abs(out).max() / 0.95)
    audio.save_wav(path, out)


# ====================================================================== décors (statiques)

def vgrad(w, h, top, bottom):
    a = np.linspace(0, 1, h)[:, None, None]
    g = np.array(top, np.float32) * (1 - a) + np.array(bottom, np.float32) * a
    return Image.fromarray(np.repeat(g, w, axis=1).astype(np.uint8), "RGB").convert("RGBA")


def office_background():
    """Bureau du « parti » : boiseries, fenêtre sur Paris, portrait de chat, drapeau."""
    bg = vgrad(SW, SH, (78, 96, 150), (44, 56, 98))
    d = ImageDraw.Draw(bg)
    d.rectangle((0, 900, SW, SH), fill=(58, 44, 40))                     # lambris
    for x in range(0, SW, 260):
        d.rectangle((x + 20, 930, x + 240, 1400), outline=(78, 60, 52), width=8)
    d.rectangle((0, 885, SW, 905), fill=(95, 72, 58))
    # fenêtre
    wx0, wy0, wx1, wy1 = 1080, 120, 1640, 760
    sky = vgrad(wx1 - wx0, wy1 - wy0, (120, 170, 230), (250, 200, 160))
    bg.alpha_composite(sky, (wx0, wy0))
    d.polygon([(1430, 760), (1470, 430), (1480, 330), (1490, 430), (1530, 760)], fill=(70, 70, 90))  # tour Eiffel
    d.rectangle((1445, 600, 1515, 615), fill=(70, 70, 90))
    d.polygon([(1080, 760), (1080, 650), (1200, 660), (1300, 700), (1640, 690), (1640, 760)], fill=(110, 110, 140))
    d.rectangle((wx0, wy0, wx1, wy1), outline=(235, 235, 240), width=26)
    d.line(((wx0 + wx1) / 2, wy0, (wx0 + wx1) / 2, wy1), fill=(235, 235, 240), width=18)
    d.line((wx0, (wy0 + wy1) / 2, wx1, (wy0 + wy1) / 2), fill=(235, 235, 240), width=18)
    for x in (wx0 - 90, wx1 + 10):                                      # rideaux
        d.rectangle((x, wy0 - 40, x + 80, wy1 + 60), fill=(150, 30, 45))
    # portrait de chat encadré (gag récurrent)
    d.rectangle((160, 180, 560, 640), fill=(190, 150, 60))
    d.rectangle((190, 210, 530, 610), fill=(80, 60, 70))
    cat(bg, 360, 520, t=0)
    d.text((240, 650), "PRÉSIDENT D'HONNEUR", font=font(FONT_BOLD, 26), fill=(220, 200, 140))
    # drapeau tricolore
    d.line((2470, 80, 2470, 1000), fill=(200, 180, 90), width=16)
    for k, col in enumerate([(30, 50, 140), (245, 245, 245), (200, 30, 45)]):
        d.polygon([(2462 - (3 - k) * 110, 110 + k * 8), (2462 - (2 - k) * 110, 110 + (k + 1) * 8),
                   (2462 - (2 - k) * 110, 520 + (k + 1) * 12), (2462 - (3 - k) * 110, 520 + k * 12)], fill=col)
    return bg


def desk_layer():
    lay = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.polygon([(1290, 1050), (2560, 1050), (2560, 1130), (1250, 1130)], fill=(120, 75, 45))
    d.rectangle((1250, 1130, 2560, 1440), fill=(95, 58, 35))
    d.line((1250, 1130, 2560, 1130), fill=(150, 100, 60), width=10)
    for x in (1400, 1900, 2400):
        d.rectangle((x - 120, 1190, x + 120, 1380), outline=(80, 48, 28), width=8)
    # dossiers « confidentiels » sur le bureau
    d.polygon([(1950, 1060), (2180, 1055), (2200, 1100), (1960, 1108)], fill=(230, 215, 170))
    d.text((1985, 1066), "COMPLOTS", font=font(FONT_BOLD, 22), fill=(170, 30, 30))
    return lay


def anchor_background():
    bg = vgrad(SW, SH, (20, 40, 110), (5, 12, 45))
    d = ImageDraw.Draw(bg)
    gl = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    g = ImageDraw.Draw(gl)
    cx, cy, r = 700, 600, 560
    for k in range(-4, 5):
        rx = abs(r * math.cos(k * math.pi / 10))
        g.ellipse((cx - rx, cy - r, cx + rx, cy + r), outline=(90, 150, 255, 70), width=6)
        ry = r * math.sin(k * math.pi / 10)
        hw = math.sqrt(max(r * r - ry * ry, 0))
        g.line((cx - hw, cy + ry, cx + hw, cy + ry), fill=(90, 150, 255, 70), width=6)
    bg.alpha_composite(gl)
    for x in range(0, SW, 160):
        d.line((x, 0, x, SH), fill=(255, 255, 255, 10), width=2)
    # encart incrusté (comme au JT)
    ix0, iy0, ix1, iy1 = 1480, 170, 2380, 760
    d.rectangle((ix0 - 10, iy0 - 10, ix1 + 10, iy1 + 10), fill=(240, 240, 240))
    inset = vgrad(ix1 - ix0, iy1 - iy0, (60, 80, 150), (20, 30, 70))
    place_head(inset, head_bardella(0.0, gaze=(-0.4, 0), mood="smile", t=1.0), 450, 640, 0.68)
    di = ImageDraw.Draw(inset)
    di.rectangle((0, iy1 - iy0 - 120, ix1 - ix0, iy1 - iy0), fill=(200, 20, 35))
    di.text((40, iy1 - iy0 - 102), "AFFAIRE BARDELLA", font=font(FONT_BLACK, 76), fill=(255, 255, 255))
    bg.alpha_composite(inset, (ix0, iy0))
    d.text((70, 60), "LES GUIGNOLS", font=font(FONT_BLACK, 60), fill=(255, 210, 40))
    d.text((70, 128), "LE COME-BACK", font=font(FONT_BLACK, 34), fill=(255, 255, 255))
    return bg


def anchor_desk():
    lay = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.polygon([(0, 1080), (SW, 1080), (SW, SH), (0, SH)], fill=(200, 205, 220))
    d.rectangle((0, 1080, SW, 1110), fill=(250, 250, 255))
    d.rectangle((0, 1180, SW, 1300), fill=(200, 20, 35))
    d.rectangle((0, 1180, 380, 1300), fill=(255, 210, 40))
    d.text((40, 1203), "DIRECT", font=font(FONT_BLACK, 66), fill=(20, 20, 30))
    d.text((420, 1206), "MEDIAPART AUTHENTIFIE DES MESSAGES DE 2013 · BARDELLA DÉMENT",
           font=font(FONT_BLACK, 60), fill=(255, 255, 255))
    return lay


# ====================================================================== rendu des plans

def speaking(seg, speaker, lt):
    """Ouverture de bouche (0..1) d'un personnage à l'instant lt du plan."""
    for ln in seg["lines"]:
        if ln["speaker"] == speaker and ln["start"] <= lt < ln["start"] + ln["dur"]:
            k = int((lt - ln["start"]) * FPS)
            e = ln["env"][min(k, len(ln["env"]) - 1)]
            return float(min(1.0, e * 1.15)) if e > 0.08 else 0.0
    return 0.0


def blinking(t, phase):
    return ((t + phase) % 3.6) < 0.13


def puppet_motion(t, amp, phase):
    """Dodelinement de marionnette : la tête « mâche » le texte."""
    ang = math.sin(t * 7.3 + phase) * 4.5 * amp + math.sin(t * 1.2 + phase) * 1.6
    dy = -amp * 22 + math.sin(t * 2.1 + phase) * 3
    dx = math.sin(t * 3.3 + phase) * 6 * amp
    return ang, dx, dy


def ringing(seg, lt):
    r = seg.get("ring")
    if r is None:
        return 0.0
    if r is True:
        return 1.0
    return 1.0 if r[0] <= lt < r[1] else 0.0


CAMERAS = {
    "wide": (1280, 720, 1.05),
    "cu_b": (800, 560, 1.75),
    "cu_m": (1880, 610, 1.75),
}


def render_office(seg, lt, gt, bg, desk):
    canvas = bg.copy()
    bcfg, mcfg = seg.get("b", {}), seg.get("m", {})
    ring = ringing(seg, lt)
    # --- Bardella (debout, à gauche)
    a = speaking(seg, "bardella", lt)
    ang, dx, dy = puppet_motion(gt, a, 0.0)
    body_suit(canvas, 780 + dx * .3, 800 + dy * .3, 640, (28, 36, 70))
    head = head_bardella(a, blinking(gt, 0.4), bcfg.get("gaze", (0.6, 0)), bcfg.get("mood", "smile"), gt)
    place_head(canvas, head, 780 + dx, 820 + dy, 0.95, ang)
    hand(canvas, 1120, 1130, 70, (226, 168, 128))
    smartphone(canvas, 1150, 1040, angle=-15, glow=seg.get("phone_glow", False))
    hand(canvas, 1175, 1110, 62, (226, 168, 128))
    # --- Marine (assise derrière le bureau, à droite)
    a = speaking(seg, "marine", lt)
    shake = ring * (1 if mcfg.get("mood") == "nervous" else 0.3)
    ang, dx, dy = puppet_motion(gt, max(a, shake * 0.5), 1.7)
    body_suit(canvas, 1880 + dx * .3, 830 + dy * .3, 700, (25, 25, 45), shirt=(240, 240, 245), tie=None)
    head = head_marine(a, blinking(gt, 1.9), mcfg.get("gaze", (-0.6, 0)), mcfg.get("mood", "sly"), gt)
    place_head(canvas, head, 1880 + dx, 850 + dy, 0.95, ang)
    canvas.alpha_composite(desk)
    hand(canvas, 1700, 1090, 70, (242, 198, 176))
    hand(canvas, 2060, 1090, 70, (242, 198, 176))
    handbag(canvas, 1470, 960, shake=ring, t=gt)
    c = speaking(seg, "cat", lt)
    cat(canvas, 2330, 1000, mouth=c, surprised=ring > 0 or c > 0, t=gt)
    if mcfg.get("sweat") and ring:
        sweat_drop(canvas, 2120, 300 + (gt * 120 % 120), 1.6)
    # --- caméra
    cx, cy, z = CAMERAS[seg["cam"]]
    cx += math.sin(gt * 0.7) * 10
    cy += math.sin(gt * 0.9 + 1) * 6
    if ring and seg["cam"] == "wide":
        z *= 1 + 0.02 * math.sin(gt * 40)
    vw, vh = SW / z, SH / z
    cx = min(max(cx, vw / 2), SW - vw / 2)
    cy = min(max(cy, vh / 2), SH - vh / 2)
    box = (cx - vw / 2, cy - vh / 2, cx + vw / 2, cy + vh / 2)
    return canvas.resize((W, H), Image.BICUBIC, box=box).convert("RGB")


def render_anchor(seg, lt, gt, bg, desk):
    canvas = bg.copy()
    a = speaking(seg, "anchor", lt)
    ang, dx, dy = puppet_motion(gt, a * 0.6, 0.9)
    body_suit(canvas, 760, 860, 700, (40, 40, 50), tie=(150, 20, 30))
    place_head(canvas, HEADS["anchor"](a, blinking(gt, 0.2), (0, 0), None, gt), 760 + dx, 880 + dy, 0.95, ang)
    canvas.alpha_composite(desk)
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle((520, 1010, 820, 1090), 10, fill=(240, 240, 245))  # feuilles
    return canvas.resize((W, H), Image.LANCZOS).convert("RGB")


def render_phone(seg, lt, gt, office_bg):
    base = office_bg.resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(12)).convert("RGB")
    base = Image.eval(base, lambda v: int(v * 0.55)).convert("RGBA")
    d = ImageDraw.Draw(base)
    # main + téléphone géant
    blob(base, (410, 470, 870, 900), (226, 168, 128))
    px0, py0, px1, py1 = 470, 30, 810, 760
    d.rounded_rectangle((px0, py0, px1, py1), 40, fill=(20, 20, 25))
    sx0, sy0, sx1, sy1 = px0 + 16, py0 + 40, px1 - 16, py1 - 20
    d.rounded_rectangle((sx0, sy0, sx1, sy1), 22, fill=(250, 250, 252))
    d.rectangle((sx0, sy0 + 10, sx1, sy0 + 80), fill=(235, 238, 245))
    d.ellipse((sx0 + 16, sy0 + 20, sx0 + 66, sy0 + 70), fill=(170, 170, 180))
    d.text((sx0 + 80, sy0 + 22), "Destinataire", font=font(FONT_BOLD, 22), fill=(20, 20, 30))
    d.text((sx0 + 80, sy0 + 50), "conversation de 2013", font=font(FONT_REG, 15), fill=(120, 120, 130))
    # anciens messages floutés (on ne les montre pas)
    for k, (x0, w) in enumerate([(12, 210), (100, 180), (12, 240)]):
        y = sy0 + 110 + k * 62
        d.rounded_rectangle((sx0 + x0, y, sx0 + x0 + w, y + 46), 20, fill=(215, 215, 222))
        d.text((sx0 + x0 + 14, y + 13), "▒▒▒▒▒▒▒▒▒▒▒▒", font=font(FONT_REG, 16), fill=(185, 185, 195))
    d.text((sx0 + 70, sy0 + 300), "— Aujourd'hui —", font=font(FONT_REG, 16), fill=(140, 140, 150))
    text = seg["text"]
    type_end = seg.get("type_end", 1.5)
    n = len(text) if lt >= type_end else int(len(text) * max(0, lt - 0.1) / (type_end - 0.1))
    shown = text[:n]
    sent = lt >= seg.get("send_at", 1.7)
    if sent:
        fnt = font(FONT_BOLD, 26)
        tw = d.textlength(text, font=fnt)
        y = sy0 + 340
        d.rounded_rectangle((sx1 - tw - 50, y, sx1 - 12, y + 56), 26, fill=(40, 120, 255))
        d.text((sx1 - tw - 30, y + 13), text, font=fnt, fill=(255, 255, 255))
        d.text((sx1 - 110, y + 64), "Distribué ✓", font=font(FONT_REG, 15), fill=(120, 120, 130))
    # zone de saisie + clavier
    ky = sy1 - 250
    d.rectangle((sx0, ky - 70, sx1, sy1), fill=(225, 228, 235))
    d.rounded_rectangle((sx0 + 12, ky - 60, sx1 - 12, ky - 10), 24, fill=(255, 255, 255))
    cursor = "|" if (gt * 2) % 1 < 0.5 else ""
    d.text((sx0 + 30, ky - 50), (shown if not sent else "") + cursor, font=font(FONT_REG, 24), fill=(20, 20, 30))
    for r in range(4):
        for c in range(10 - (r == 3) * 6):
            kx = sx0 + 12 + c * 29 + (r == 3) * 60
            kw = 25 if r < 3 else 150
            d.rounded_rectangle((kx, ky + r * 58, kx + kw, ky + r * 58 + 48), 6, fill=(255, 255, 255))
    blob(base, (680, 560, 900, 760), (226, 168, 128))  # pouce
    return base.convert("RGB")


def render_title(seg, lt, gt):
    img = vgrad(W, H, (130, 10, 20), (20, 0, 5))
    d = ImageDraw.Draw(img)
    for k in range(14):  # rayons de projecteurs
        ang = k * math.tau / 14 + gt * 0.6
        d.polygon([(640, 360), (640 + 1400 * math.cos(ang), 360 + 1400 * math.sin(ang)),
                   (640 + 1400 * math.cos(ang + 0.12), 360 + 1400 * math.sin(ang + 0.12))], fill=(160, 25, 35))
    pop = min(1.0, lt / 0.6)
    ease = 1 - (1 - pop) ** 3
    for fn, x, mood, ph in [(head_bardella, 250, "smile", 0), (head_marine, 1030, "sly", 1)]:
        h = fn(0.0, False, (0.5 if x < 640 else -0.5, 0), mood, gt)
        ang, _, _ = puppet_motion(gt, 0.6, ph)
        place_head(img, h, x, 760 + (1 - ease) * 420, 0.55, ang)
    s = min(1.0, max(0.0, (lt - 0.2) / 0.4))
    f1 = font(FONT_BLACK, int(150 * (0.6 + 0.4 * s)))
    txt = "LES GUIGNOLS"
    tw = d.textlength(txt, font=f1)
    d.text((640 - tw / 2, 170), txt, font=f1, fill=(255, 215, 40), stroke_width=10, stroke_fill=(20, 10, 10))
    if lt > 0.9:
        f2 = font(FONT_BLACK, 70)
        txt2 = "LE COME-BACK"
        tw2 = d.textlength(txt2, font=f2)
        d.rectangle((640 - tw2 / 2 - 30, 380, 640 + tw2 / 2 + 30, 470), fill=(255, 255, 255))
        d.text((640 - tw2 / 2, 385), txt2, font=f2, fill=(200, 20, 35))
    d.text((20, H - 34), "Parodie satirique — marionnettes et voix fictives", font=font(FONT_REG, 20),
           fill=(255, 220, 220))
    return img.convert("RGB")


def render_end(seg, lt, gt):
    img = vgrad(W, H, (15, 25, 70), (5, 8, 25))
    d = ImageDraw.Draw(img)
    f1 = font(FONT_BLACK, 74)
    for txt, y, f, col in [("LES GUIGNOLS", 70, f1, (255, 215, 40)),
                           ("LE COME-BACK · Épisode 1", 160, font(FONT_BLACK, 40), (255, 255, 255)),
                           ("« Mais qui a bien pu écrire ça ? »", 220, font(FONT_BOLD, 34), (200, 210, 255))]:
        tw = d.textlength(txt, font=f)
        d.text((640 - tw / 2, y), txt, font=f, fill=col, stroke_width=4 if f is f1 else 0, stroke_fill=(0, 0, 0))
    disclaimer = ("PARODIE. Les personnages sont des marionnettes caricaturales et toutes les répliques sont "
                  "inventées. Mediapart affirme avoir authentifié des messages de 2013 attribués à Jordan "
                  "Bardella ; celui-ci conteste en être l'auteur et a annoncé une plainte pour faux et diffamation.")
    y = 330
    for line in textwrap.wrap(disclaimer, 78):
        tw = d.textlength(line, font=font(FONT_REG, 24))
        d.text((640 - tw / 2, y), line, font=font(FONT_REG, 24), fill=(220, 225, 240))
        y += 34
    credit = "Une idée de Noa · marionnettes, voix et montage : Claude (IA)"
    tw = d.textlength(credit, font=font(FONT_BOLD, 24))
    d.text((640 - tw / 2, 600), credit, font=font(FONT_BOLD, 24), fill=(255, 215, 40))
    if seg.get("ring") and ringing(seg, lt):  # le sac sonne encore...
        hb = Image.new("RGBA", (800, 640), (0, 0, 0, 0))
        handbag(hb, 400, 340, shake=1, t=gt)
        img.alpha_composite(hb.resize((hb.width // 4, hb.height // 4)), (1060, 530))
    return img.convert("RGB")


def wrap_px(d, text, f, maxw):
    words, rows, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=f) <= maxw or not cur:
            cur = trial
        else:
            rows.append(cur)
            cur = w
    rows.append(cur)
    # pas de ponctuation orpheline en fin de sous-titre
    if len(rows) > 1 and len(rows[-1]) <= 2:
        rows[-2] += " " + rows.pop()
    return rows


def subtitles(frame, seg, lt):
    """Sous-titres incrustés (indispensables pour les réseaux sociaux)."""
    bottom = H - 150 if seg["kind"] == "anchor" else H - 26  # au-dessus du bandeau du JT
    for ln in seg["lines"]:
        if ln["sub"] and ln["start"] - 0.05 <= lt < ln["start"] + ln["dur"] + 0.25:
            d = ImageDraw.Draw(frame)
            f = font(FONT_BOLD, 34)
            rows = wrap_px(d, ln["sub"], f, W - 140)
            y = bottom - 44 * len(rows)
            for r in rows:
                tw = d.textlength(r, font=f)
                d.text((W / 2 - tw / 2, y), r, font=f, fill=(255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0))
                y += 44
    return frame


# ====================================================================== main

def main():
    preview = "--preview" in sys.argv
    os.makedirs(OUT, exist_ok=True)
    timeline, total = build_timeline()
    print(f"Durée totale : {total:.1f} s, {len(timeline)} plans")
    wav_path = os.path.join(BUILD, "mix.wav")
    mix_audio(timeline, total, wav_path)

    office_bg, desk = office_background(), desk_layer()
    a_bg, a_desk = anchor_background(), anchor_desk()

    out_path = os.path.join(OUT, "guignols_comeback_ep1.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav_path,
                           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "160k", "-shortest", out_path], stdin=subprocess.PIPE)
    nframes = int(total * FPS)
    seg_i = 0
    for f in range(nframes):
        gt = f / FPS
        while seg_i < len(timeline) - 1 and gt >= timeline[seg_i]["t0"] + timeline[seg_i]["dur"]:
            seg_i += 1
        seg = timeline[seg_i]
        lt = gt - seg["t0"]
        kind = seg["kind"]
        if kind == "office":
            frame = render_office(seg, lt, gt, office_bg, desk)
        elif kind == "anchor":
            frame = render_anchor(seg, lt, gt, a_bg, a_desk)
        elif kind == "phone":
            frame = render_phone(seg, lt, gt, office_bg)
        elif kind == "title":
            frame = render_title(seg, lt, gt)
        else:
            frame = render_end(seg, lt, gt)
        frame = subtitles(frame, seg, lt)
        if preview and f % FPS == 0:
            frame.save(os.path.join(BUILD, f"preview_{f // FPS:03d}.png"))
        ff.stdin.write(frame.tobytes())
        if f % 100 == 0:
            print(f"  image {f}/{nframes}", flush=True)
    ff.stdin.close()
    ff.wait()
    print("OK ->", out_path)


if __name__ == "__main__":
    main()
