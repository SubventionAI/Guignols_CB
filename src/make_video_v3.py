"""Les Guignols — Le Come-Back, v3 : vraie synchro labiale par variantes.

Pour chaque plan, on dispose de l'image de base (bouche fermée) et de variantes
générées à composition identique : bouche entrouverte, grande ouverte, en « O »,
yeux fermés. À chaque image vidéo, on choisit la forme de bouche d'après la voix
(volume -> ouverture ; formants F1/F2 -> voyelle arrondie « o/ou ») et on colle
uniquement la zone de la bouche (ou des yeux) de la bonne variante, en fondu.
S'y ajoutent clignements d'yeux aléatoires, dodelinement de tête, sac qui vibre.

Usage : python3 src/make_video_v3.py [--preview]
"""
import math
import os
import random
import subprocess
import sys

import numpy as np
import parselmouth
from PIL import Image, ImageDraw, ImageFilter

import audio
from make_video_v2 import (SFX, FPS, W, H, SR, end_card, head_move, shake_bag, subtitles, tag,
                           title_card, tv_look)
from episode1_v3 import SEGMENTS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets", "v3")
BUILD = os.path.join(ROOT, "build", "v3")
VOICES = os.path.join(BUILD, "voices")
OUT = os.path.join(ROOT, "output")

# Zones (coordonnées des images 1456x1088) : ellipse bouche (cx, cy, rx, ry),
# ellipse yeux, boîte tête + pivot pour le dodelinement.
SHOTS = {
    "praud": dict(variants=dict(mid="praud_mid", wide="praud_wide", o="praud_o", blink="praud_blink"),
                  focus=(730, 400), chars={"praud": dict(
                      mouth=(728, 472, 130, 92), eyes=(735, 318, 150, 50),
                      head=(560, 150, 900, 620), pivot=(730, 640))}),
    "bardella": dict(variants=dict(mid="bardella_mid", wide="bardella_wide", blink="bardella_blink"),
                     focus=(720, 340), chars={"bardella": dict(
                         mouth=(695, 478, 145, 115), eyes=(705, 312, 130, 48),
                         head=(540, 15, 940, 625), pivot=(705, 640))}),
    "marine": dict(variants=dict(mid="marine_mid", wide="marine_wide", o="marine_o", blink="marine_blink"),
                   focus=(720, 360), chars={"marine": dict(
                       mouth=(728, 476, 130, 100), eyes=(730, 346, 135, 42),
                       head=(465, 45, 965, 600), pivot=(720, 620))}),
    "marine_phone": dict(variants=dict(mid="marine_phone_mid", wide="marine_phone_wide", blink="marine_phone_blink"),
                         focus=(720, 400), chars={"marine": dict(
                             mouth=(735, 488, 118, 100), eyes=(735, 356, 125, 42), head=None, pivot=None)}),
    "duo": dict(variants=dict(mid="duo_mid", wide="duo_wide", blink="duo_blink"),
                focus=(728, 470), bag=(1112, 668, 1442, 942), phone=(305, 768, 415, 858), chars={
                    "bardella": dict(mouth=(370, 458, 92, 72), eyes=(388, 332, 92, 32),
                                     head=(250, 125, 545, 548), pivot=(390, 560)),
                    "marine": dict(mouth=(1003, 468, 82, 62), eyes=(1002, 382, 88, 30),
                                   head=(815, 175, 1180, 548), pivot=(1000, 560))}),
}


# ====================================================================== analyse de la voix

def visemes(wav):
    """Par image vidéo : ouverture (0..1) et voyelle arrondie (o/ou) détectée par les formants."""
    hop = SR // FPS
    n = int(np.ceil(len(wav) / hop))
    rms = np.array([np.sqrt(np.mean(wav[i * hop:(i + 1) * hop] ** 2) + 1e-9) for i in range(n)])
    rms = rms / (np.percentile(rms, 92) + 1e-6)
    snd = parselmouth.Sound(wav.astype(np.float64), SR)
    fm = snd.to_formant_burg(time_step=1 / FPS, max_number_of_formants=5, maximum_formant=5000)
    pitch = snd.to_pitch(time_step=1 / FPS)
    rounded = np.zeros(n, bool)
    for i in range(n):
        t = (i + 0.5) / FPS
        f1, f2 = fm.get_value_at_time(1, t), fm.get_value_at_time(2, t)
        voiced = pitch.get_value_at_time(t) == pitch.get_value_at_time(t)  # pas NaN
        rounded[i] = bool(voiced and f2 == f2 and f2 < 1150 and f1 == f1 and f1 < 520)
    states = []
    for i in range(n):
        o = rms[i]
        if o < 0.18:
            s = "closed"
        elif rounded[i] and o < 0.85:
            s = "o"
        elif o < 0.62:
            s = "mid"
        else:
            s = "wide"
        states.append(s)
    # pas de saut fermé <-> grand ouvert : on passe par l'entrouvert
    for i in range(1, n):
        if {states[i - 1], states[i]} == {"closed", "wide"}:
            states[i] = "mid"
    # pas de clignotement : une forme tient au moins 2 images
    for i in range(1, n - 1):
        if states[i] != states[i - 1] and states[i] != states[i + 1] and states[i - 1] == states[i + 1]:
            states[i] = states[i - 1]
    return states, np.clip(rms, 0, 1)


# ====================================================================== rendu

def color_match(var, base):
    """Corrige la teinte d'une variante pour qu'elle colle à l'image de base (pas d'auréole)."""
    a = np.asarray(var).astype(np.float32)
    b = np.asarray(base).astype(np.float32)
    same = np.abs(a - b).mean(2) < 20  # zones inchangées
    out = a.copy()
    for ch in range(3):
        x, y = a[..., ch][same], b[..., ch][same]
        k, c = np.polyfit(x, y, 1)
        out[..., ch] = a[..., ch] * k + c
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def ellipse_mask(size, e, feather):
    cx, cy, rx, ry = e
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
    return m.filter(ImageFilter.GaussianBlur(feather))


class Shot:
    def __init__(self, name):
        self.cfg = SHOTS[name]
        self.base = Image.open(os.path.join(ASSETS, name + ".png")).convert("RGB")
        self.var = {k: color_match(Image.open(os.path.join(ASSETS, v + ".png")).convert("RGB").resize(self.base.size),
                                   self.base)
                    for k, v in self.cfg["variants"].items()}
        self.masks = {}
        for cname, c in self.cfg["chars"].items():
            self.masks[cname] = dict(mouth=ellipse_mask(self.base.size, c["mouth"], 14),
                                     eyes=ellipse_mask(self.base.size, c["eyes"], 10))

    def state_img(self, s):
        if s == "closed":
            return self.base
        if s == "o" and "o" not in self.var:
            s = "mid"
        return self.var[s]

    def render(self, seg, lt, gt, blinkers):
        img = self.base.copy()
        for k, (cname, c) in enumerate(self.cfg["chars"].items()):
            s, amp = current_viseme(seg, cname, lt)
            if s != "closed":
                img.paste(self.state_img(s), (0, 0), self.masks[cname]["mouth"])
            if blinkers.get(cname, False) and "blink" in self.var:
                img.paste(self.var["blink"], (0, 0), self.masks[cname]["eyes"])
            c_head = c.get("head")
            if c_head:
                ph = k * 1.9 + len(seg["shot"])
                ang = math.sin(gt * 6.3 + ph) * 1.4 * amp + math.sin(gt * 1.1 + ph) * 0.6
                dy = -amp * 4 + math.sin(gt * 1.7 + ph) * 1.2
                img = head_move(img.convert("RGBA"), c_head, c["pivot"], ang, dy).convert("RGB")
        img = img.convert("RGBA")
        ring = seg.get("ring") is True or (seg.get("ring_from") is not None and lt >= seg["ring_from"])
        if self.cfg.get("bag") and ring:
            shake_bag(img, self.cfg["bag"], gt)
        if self.cfg.get("phone") and any(n == "typing" and at <= lt < at + 1.4 for n, at, _ in seg["sfx"]):
            ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
            px0, py0, px1, py1 = self.cfg["phone"]
            ImageDraw.Draw(ov).rounded_rectangle((px0 + 12, py0 + 6, px1 - 12, py1 - 30), 8,
                                                 fill=(140, 200, 255, 120))
            img.alpha_composite(ov.filter(ImageFilter.GaussianBlur(3)))
        # léger travelling avant + caméra « portée »
        p = min(1.0, lt / max(seg["dur"], 0.1))
        z = 1.0 + 0.03 * p
        fx, fy = self.cfg["focus"]
        vw, vh = img.width / z, img.height / z
        cx = img.width / 2 + (fx - img.width / 2) * (1 - 1 / z) + math.sin(gt * 0.8) * 2
        cy = img.height / 2 + (fy - img.height / 2) * (1 - 1 / z) + math.sin(gt * 1.1) * 1.5
        cx = min(max(cx, vw / 2), img.width - vw / 2)
        cy = min(max(cy, vh / 2), img.height - vh / 2)
        return img.resize((W, H), Image.LANCZOS, box=(cx - vw / 2, cy - vh / 2, cx + vw / 2, cy + vh / 2))


def current_viseme(seg, speaker, lt):
    for ln in seg["lines"]:
        if ln["speaker"] == speaker and ln["start"] <= lt < ln["start"] + ln["dur"]:
            k = min(int((lt - ln["start"]) * FPS), len(ln["states"]) - 1)
            return ln["states"][k], float(ln["amp"][k])
    return "closed", 0.0


def caption(img, name, title):
    """Légende ironique façon Guignols (nom + « fonction »)."""
    from make_video_v2 import font, FONT_COND
    d = ImageDraw.Draw(img)
    f1, f2 = font(FONT_COND, 50), font(FONT_COND, 40)
    x, y = 70, 70
    w = max(d.textlength(name, font=f1), d.textlength(title, font=f2)) + 40
    d.rectangle((x - 20, y - 10, x - 20 + w, y + 110), fill=(10, 10, 20))
    d.text((x, y), name, font=f1, fill=(255, 255, 255))
    d.text((x, y + 58), title, font=f2, fill=(255, 210, 60))


# ====================================================================== montage

def load_wav(path):
    import librosa
    y, _ = librosa.load(path, sr=SR)
    return y.astype(np.float32)


TEMPO = {"praud": 1.12, "bardella": 1.08, "marine": 1.08}


def tighten(wav, last_pause=0.15, tempo=1.0, max_gap=0.15):
    """Rythme Guignols : pauses internes ramenées à max_gap (la dernière peut rester plus longue),
    silences de début/fin coupés, puis accélération sans changer la hauteur (sox tempo)."""
    import librosa
    iv = librosa.effects.split(wav, top_db=35, frame_length=1024, hop_length=256)
    if len(iv) == 0:
        return wav
    parts = []
    for k, (a, b) in enumerate(iv):
        parts.append(wav[max(0, a - 300):b + 300])
        if k < len(iv) - 1:
            gap = (iv[k + 1][0] - b) / SR
            g = min(gap, last_pause if k == len(iv) - 2 else max_gap)
            parts.append(np.zeros(int(g * SR), np.float32))
    out = np.concatenate(parts)
    if abs(tempo - 1.0) > 0.01:
        tmp_in, tmp_out = os.path.join(BUILD, "_t_in.wav"), os.path.join(BUILD, "_t_out.wav")
        audio.save_wav(tmp_in, out)
        subprocess.run(["sox", tmp_in, tmp_out, "tempo", "-s", str(tempo)], check=True)
        out = load_wav(tmp_out)
    return out


def build_timeline():
    t = 0.0
    timeline = []
    for i, seg in enumerate(SEGMENTS):
        seg = dict(seg)
        lines = []
        cursor = seg.get("lead", 0.1)
        for j, (spk, say, sub) in enumerate(seg.get("lines", [])):
            wav = tighten(load_wav(os.path.join(VOICES, f"line_{i:02d}_{j}.wav")),
                          seg.get("keep_last_pause", 0.15), TEMPO.get(spk, 1.0))
            states, amp = visemes(wav)
            lines.append(dict(speaker=spk, sub=sub, start=cursor, dur=len(wav) / SR, wav=wav,
                              states=states, amp=amp))
            cursor += len(wav) / SR + 0.08
        seg["lines"] = lines
        sfx = list(seg.get("sfx", []))
        sfx += [(name, cursor + at, vol) for name, at, vol in seg.get("sfx_after", [])]
        seg["sfx"] = sfx
        if seg.get("ring_from") is not None and seg.get("sfx_after"):
            seg["ring_from"] = cursor + seg["ring_from"]
        seg["dur"] = max(seg.get("dur", 0), cursor + seg.get("tail", 0.1) + seg.get("extra", 0))
        seg["t0"] = t
        t += seg["dur"]
        timeline.append(seg)
    return timeline, t


def mix_audio(timeline, total, path):
    rng = np.random.default_rng(0)
    out = rng.normal(0, 0.003, int((total + 4) * SR)).astype(np.float32)

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


def main():
    preview = "--preview" in sys.argv
    os.makedirs(OUT, exist_ok=True)
    timeline, total = build_timeline()
    print(f"Durée : {total:.1f} s, {len(timeline)} plans", flush=True)
    wav = os.path.join(BUILD, "mix.wav")
    mix_audio(timeline, total, wav)
    shots = {name: Shot(name) for name in SHOTS}
    end = end_card("« C'est fou ce que les gens se ressemblent »")
    out = os.path.join(OUT, "guignols_comeback_ep1_v3.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
                           "-c:v", "libx264", "-preset", "medium", "-crf", "24", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "192k", "-shortest", out], stdin=subprocess.PIPE)
    rnd = random.Random(7)
    next_blink = {}
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
            blinkers = {}
            for cname in SHOTS[shot]["chars"]:
                nb = next_blink.setdefault(cname, gt + rnd.uniform(0.5, 2.5))
                if gt >= nb:
                    blinkers[cname] = True
                    if gt >= nb + 0.12:
                        next_blink[cname] = gt + rnd.uniform(2.0, 4.5)
            frame = shots[shot].render(seg, lt, gt, blinkers)
            frame = tv_look(frame, gt)
            if seg.get("tag"):
                tag(frame, seg["tag"])
            if seg.get("caption") and lt < 3.2:
                caption(frame, *seg["caption"])
            subtitles(frame, seg, lt)
        frame = frame.convert("RGB")
        if preview and f % 6 == 0:
            frame.resize((480, 360)).save(os.path.join(BUILD, f"p_{f:05d}.png"))
        ff.stdin.write(frame.tobytes())
        if f % 200 == 0:
            print(f"  {f}/{n}", flush=True)
    ff.stdin.close()
    ff.wait()
    print("OK ->", out)


if __name__ == "__main__":
    main()
