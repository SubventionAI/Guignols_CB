"""Marionnettes en latex « façon Guignols » dessinées avec Pillow.

Chaque tête est rendue dans un calque RGBA 800x900 (pivot au cou), puis
tournée / décalée pour imiter le dodelinement des marionnettes à gaine.
"""
import math
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HEAD_W, HEAD_H = 800, 900
PIVOT = (400, 820)


@lru_cache(maxsize=256)
def _shaded(w, h, color, light=(0.38, 0.30), gloss=0.0):
    """Ellipse ombrée (aspect latex) : dégradé radial + assombrissement des bords."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    nx, ny = (xx + .5) / w * 2 - 1, (yy + .5) / h * 2 - 1
    r = np.sqrt(nx ** 2 + ny ** 2)
    lx, ly = light[0] * 2 - 1, light[1] * 2 - 1
    d = np.sqrt((nx - lx) ** 2 + (ny - ly) ** 2)
    shade = 1.12 - 0.32 * d - 0.30 * np.clip(r, 0, 1) ** 5
    rgb = np.clip(np.array(color, np.float32)[None, None, :] * shade[..., None], 0, 255)
    if gloss:
        spec = np.exp(-((d / 0.28) ** 2)) * gloss * 255
        rgb = np.clip(rgb + spec[..., None], 0, 255)
    alpha = np.clip((1 - r) * min(w, h) / 2, 0, 1) * 255
    return Image.fromarray(np.dstack([rgb, alpha]).astype(np.uint8), "RGBA")


def blob(img, box, color, light=(0.38, 0.30), gloss=0.0):
    x0, y0, x1, y1 = [int(v) for v in box]
    img.alpha_composite(_shaded(x1 - x0, y1 - y0, tuple(color), light, gloss), (x0, y0))


def blob_union(img, boxes, color, light=(0.38, 0.30)):
    """Plusieurs ellipses fusionnées en une seule pièce de latex (visage + mâchoire)."""
    x0 = int(min(b[0] for b in boxes)); y0 = int(min(b[1] for b in boxes))
    x1 = int(max(b[2] for b in boxes)); y1 = int(max(b[3] for b in boxes))
    w, h = x1 - x0, y1 - y0
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    inside = np.zeros((h, w), np.float32)
    for b in boxes:
        cx, cy = (b[0] + b[2]) / 2 - x0, (b[1] + b[3]) / 2 - y0
        rx, ry = (b[2] - b[0]) / 2, (b[3] - b[1]) / 2
        r = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
        inside = np.maximum(inside, np.clip((1 - r) * min(rx, ry), 0, 1))
    shade_img = np.array(_shaded(w, h, tuple(color), light))[..., :3].astype(np.float32)
    # bords assombris calculés sur la forme fusionnée
    from PIL import ImageFilter as _F
    edge = np.array(Image.fromarray((inside * 255).astype(np.uint8)).filter(_F.GaussianBlur(min(w, h) / 9)),
                    np.float32) / 255
    rgb = np.array(color, np.float32) * (1.08 - 0.25 * np.hypot((xx / w) - light[0], (yy / h) - light[1]) * 2)[..., None]
    rgb *= (0.72 + 0.28 * edge)[..., None]
    out = np.dstack([np.clip(rgb, 0, 255), inside * 255]).astype(np.uint8)
    img.alpha_composite(Image.fromarray(out, "RGBA"), (x0, y0))


def overlay(img, fn):
    """Dessine en semi-transparence (joues, ombres, reflets)."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fn(ImageDraw.Draw(layer))
    img.alpha_composite(layer)


# ------------------------------------------------------------------ éléments

def eye(d, img, box, iris, gaze, lid, lid_color, lash=True, lower_lid=0.0):
    """Œil avec iris, reflet et paupière supérieure (lid 0=ouvert, 1=fermé)."""
    x0, y0, x1, y1 = [int(v) for v in box]
    cx, cy, rw, rh = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    blob(img, box, (250, 250, 245), light=(0.4, 0.3))
    gx, gy = gaze
    ix, iy = cx + gx * rw * 0.45, cy + gy * rh * 0.35
    ir = rh * 0.62
    d.ellipse((ix - ir, iy - ir, ix + ir, iy + ir), fill=iris)
    d.ellipse((ix - ir * .45, iy - ir * .45, ix + ir * .45, iy + ir * .45), fill=(15, 10, 10))
    d.ellipse((ix - ir * .55, iy - ir * .7, ix - ir * .15, iy - ir * .3), fill=(255, 255, 255))
    # le blanc de l'œil ne déborde pas : on recoupe l'iris avec un masque elliptique
    pad = 8
    region = (x0 - pad, y0 - pad, x1 + pad, y1 + pad)
    crop = img.crop(region)
    mask = Image.new("L", crop.size, 0)
    ImageDraw.Draw(mask).ellipse((pad, pad, pad + x1 - x0, pad + y1 - y0), fill=255)
    lid = min(max(lid, 0.0), 1.0)
    ly = pad + (y1 - y0) * lid
    md = ImageDraw.Draw(mask)
    if lid > 0:
        md.rectangle((0, 0, crop.width, ly), fill=0)
    if lower_lid > 0:
        md.rectangle((0, pad + (y1 - y0) * (1 - lower_lid), crop.width, crop.height), fill=0)
    skin = Image.new("RGBA", crop.size, lid_color + (255,))
    fill = Image.new("L", crop.size, 0)
    ImageDraw.Draw(fill).ellipse((0, 0, crop.width - 1, crop.height - 1), fill=255)
    eyepart = Image.composite(crop, skin, mask)
    base = img.crop(region)
    base.paste(eyepart, (0, 0), fill)
    img.paste(base, region[:2])
    d.ellipse(box, outline=(60, 40, 40), width=3)
    if lash:
        top = y0 + (y1 - y0) * lid
        d.line((x0 - 6, top, x1 + 6, top), fill=(25, 15, 15), width=7)
        if lid < 0.2:
            d.arc((x0 - 4, y0 - 2, x1 + 4, y1), 195, 345, fill=(25, 15, 15), width=7)


def brow(d, x0, y0, x1, y1, color, width=12):
    d.line((x0, y0, (x0 + x1) / 2, min(y0, y1) - 10, x1, y1), fill=color, width=width, joint="curve")


def sparkle(d, x, y, r, color=(255, 255, 255)):
    d.polygon([(x, y - r), (x + r * .22, y - r * .22), (x + r, y), (x + r * .22, y + r * .22),
               (x, y + r), (x - r * .22, y + r * .22), (x - r, y), (x - r * .22, y - r * .22)], fill=color)


# ------------------------------------------------------------------ Bardella

SKIN_B = (226, 168, 128)


def head_bardella(mouth=0.0, blink=False, gaze=(0, 0), mood="smile", t=0.0):
    """Jordan Bardella : brushing gominé indestructible, sourire « dentifrice »."""
    img = Image.new("RGBA", (HEAD_W, HEAD_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    hair = (28, 22, 22)
    blob(img, (170, 30, 630, 430), hair, gloss=0.35)                      # casque de gel
    blob(img, (140, 390, 235, 545), SKIN_B)                               # oreilles
    blob(img, (565, 390, 660, 545), SKIN_B)
    blob_union(img, [(185, 150, 615, 770), (225, 520, 575, 870)], SKIN_B)  # visage + menton de jeune premier
    d.arc((370, 800, 430, 850), 200, 340, fill=(170, 110, 85), width=5)   # fossette
    # mèche gominée
    d.polygon([(178, 345), (185, 200), (270, 95), (420, 55), (580, 95), (640, 220), (630, 345),
               (590, 250), (500, 205), (395, 222), (300, 262), (225, 330)], fill=hair)
    for box, a0, a1 in [((240, 85, 600, 330), 205, 290), ((300, 120, 640, 360), 220, 280),
                        ((200, 140, 420, 420), 200, 250)]:
        d.arc(box, a0, a1, fill=(215, 215, 235), width=13)               # reflets de gel
    overlay(img, lambda o: (o.ellipse((215, 520, 330, 600), fill=(240, 110, 110, 70)),
                            o.ellipse((470, 520, 585, 600), fill=(240, 110, 110, 70))))
    # sourcils épilés au cordeau
    bc = (35, 25, 22)
    if mood == "angry":
        brow(d, 262, 330, 380, 368, bc); brow(d, 420, 368, 538, 330, bc)
    elif mood == "idea":
        brow(d, 262, 318, 380, 300, bc); brow(d, 420, 300, 538, 318, bc)
    elif mood == "suspicious":
        brow(d, 262, 352, 380, 352, bc); brow(d, 420, 300, 538, 330, bc)
    else:
        brow(d, 262, 345, 380, 332, bc); brow(d, 420, 332, 538, 345, bc)
    lid = 1.0 if blink else (0.42 if mood == "suspicious" else 0.08)
    eye(d, img, (262, 372, 378, 452), (95, 60, 35), gaze, lid, SKIN_B)
    eye(d, img, (422, 372, 538, 452), (95, 60, 35), gaze, 1.0 if blink else 0.08, SKIN_B)
    blob(img, (362, 445, 438, 565), (214, 152, 115), light=(0.45, 0.25))  # nez
    d.ellipse((375, 540, 393, 552), fill=(120, 70, 55)); d.ellipse((407, 540, 425, 552), fill=(120, 70, 55))
    _mouth_grin(d, img, 400, 625, 270, mouth, t)
    return img


def _mouth_grin(d, img, cx, y0, w, o, t):
    """Sourire Colgate : quand la bouche est fermée, on voit TOUTES les dents."""
    h = 70 + 130 * o
    x0, x1 = cx - w / 2, cx + w / 2
    d.chord((x0, y0 - h, x1, y0 + h), 0, 180, fill=(85, 18, 25))
    if o > 0.25:
        d.ellipse((cx - w * .22, y0 + h * .5, cx + w * .22, y0 + h * .97), fill=(205, 85, 95))  # langue
    d.chord((x0 + 10, y0 - 48, x1 - 10, y0 + 48), 0, 180, fill=(255, 255, 250))
    for i in range(1, 8):
        x = x0 + 10 + i * (w - 20) / 8
        d.line((x, y0 + 2, x, y0 + 36 - abs(i - 4) * 6), fill=(200, 200, 205), width=2)
    if o < 0.35:  # dents du bas
        d.chord((x0 + 35, y0 + h - 34, x1 - 35, y0 + h + 34), 180, 360, fill=(245, 245, 240))
    d.arc((x0, y0 - h, x1, y0 + h), 0, 180, fill=(160, 80, 75), width=10)
    d.line((x0 - 4, y0, x1 + 4, y0), fill=(160, 80, 75), width=8)
    d.arc((x0 - 34, y0 - 50, x0 + 6, y0 + 25), 90, 250, fill=(175, 108, 88), width=6)
    d.arc((x1 - 6, y0 - 50, x1 + 34, y0 + 25), 290, 90, fill=(175, 108, 88), width=6)
    if (t % 3.1) < 0.35:  # étincelle de dentifrice
        sparkle(d, cx + w * .3, y0 + 18, 34)


# ------------------------------------------------------------------ Marine

SKIN_M = (242, 198, 176)
BLOND = (232, 196, 118)


def head_marine(mouth=0.0, blink=False, gaze=(0, 0), mood="sly", t=0.0):
    """Marine Le Pen : casque blond, mâchoire puissante, paupières de féline."""
    img = Image.new("RGBA", (HEAD_W, HEAD_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    blob(img, (120, 55, 680, 700), BLOND, gloss=0.15)
    blob(img, (105, 420, 310, 790), BLOND)
    blob(img, (490, 420, 695, 790), BLOND)
    blob_union(img, [(190, 165, 610, 790), (180, 470, 620, 865)], SKIN_M)  # visage + mâchoire
    d.polygon([(190, 430), (188, 255), (255, 140), (400, 95), (565, 125), (632, 240), (628, 430),
               (590, 300), (520, 235), (430, 212), (330, 238), (255, 305)], fill=BLOND)
    for box, a0, a1 in [((230, 100, 600, 360), 210, 300), ((150, 160, 420, 520), 190, 240)]:
        d.arc(box, a0, a1, fill=(252, 232, 175), width=14)
    overlay(img, lambda o: (o.ellipse((215, 540, 340, 630), fill=(235, 120, 130, 80)),
                            o.ellipse((460, 540, 585, 630), fill=(235, 120, 130, 80))))
    bc = (150, 115, 70)
    if mood == "nervous":
        brow(d, 262, 330, 382, 312, bc, 14); brow(d, 418, 312, 538, 330, bc, 14)
    elif mood == "proud":
        brow(d, 262, 318, 382, 328, bc, 14); brow(d, 418, 328, 538, 318, bc, 14)
    else:  # sly
        brow(d, 262, 345, 382, 325, bc, 14); brow(d, 418, 312, 538, 340, bc, 14)
    shadow = (175, 140, 165)
    base_lid = {"sly": 0.45, "proud": 0.38, "nervous": 0.12}.get(mood, 0.4)
    lid = 1.0 if blink else base_lid
    eye(d, img, (265, 380, 382, 455), (60, 115, 185), gaze, lid, shadow, lower_lid=0.1)
    eye(d, img, (418, 380, 535, 455), (60, 115, 185), gaze, 1.0 if blink else (0.6 if mood == "sly" and (t % 4) < 0.6 else base_lid),
        shadow, lower_lid=0.1)
    blob(img, (352, 450, 448, 585), (230, 182, 160), light=(0.45, 0.25))
    d.ellipse((370, 560, 392, 574), fill=(140, 85, 75)); d.ellipse((408, 560, 430, 574), fill=(140, 85, 75))
    # boucles d'oreille perles
    for x in (198, 602):
        blob(img, (x - 18, 560, x + 18, 596), (245, 245, 240), gloss=0.6)
    # bouche (y0 = commissure / lèvre supérieure)
    cx, y0, w = 400, 670, 240
    h = 22 + 120 * mouth
    lip = (195, 70, 90)
    if mood == "nervous" and mouth < 0.15:
        d.line((cx - w / 2, y0, cx - w / 4, y0 - 14, cx, y0 + 6, cx + w / 4, y0 - 14, cx + w / 2, y0),
               fill=lip, width=16, joint="curve")
    else:
        d.chord((cx - w / 2, y0 - h, cx + w / 2, y0 + h), 0, 180, fill=(80, 15, 25))
        if mouth > 0.2:
            d.chord((cx - w / 2 + 25, y0 - 28, cx + w / 2 - 25, y0 + 28), 0, 180, fill=(250, 248, 240))
        d.arc((cx - w / 2, y0 - h, cx + w / 2, y0 + h), 0, 180, fill=lip, width=18)
        d.line((cx - w / 2, y0, cx - w / 4, y0 - 8, cx, y0 - 2, cx + w / 4, y0 - 8, cx + w / 2, y0),
               fill=lip, width=16, joint="curve")
        if mood == "sly":  # rictus en coin
            d.arc((cx + w / 2 - 20, y0 - 50, cx + w / 2 + 30, y0 + 10), 300, 100, fill=(200, 140, 125), width=7)
    return img


# ------------------------------------------------------------------ présentateur

def head_anchor(mouth=0.0, blink=False, gaze=(0, 0), mood=None, t=0.0):
    """Présentateur générique du JT (pas un vrai journaliste)."""
    skin = (236, 190, 160)
    img = Image.new("RGBA", (HEAD_W, HEAD_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    blob(img, (175, 80, 625, 470), (150, 150, 155), gloss=0.2)
    blob(img, (150, 400, 235, 540), skin); blob(img, (565, 400, 650, 540), skin)
    blob_union(img, [(190, 160, 610, 800)], skin)
    d.polygon([(195, 360), (210, 210), (330, 130), (480, 135), (590, 210), (605, 360), (560, 250), (420, 205),
               (290, 230)], fill=(150, 150, 155))
    brow(d, 265, 345, 382, 340, (120, 120, 125), 14); brow(d, 418, 340, 535, 345, (120, 120, 125), 14)
    eye(d, img, (270, 380, 380, 450), (70, 90, 70), gaze, 1.0 if blink else 0.2, skin)
    eye(d, img, (420, 380, 530, 450), (70, 90, 70), gaze, 1.0 if blink else 0.2, skin)
    d.ellipse((250, 362, 398, 470), outline=(40, 40, 45), width=9)    # lunettes
    d.ellipse((402, 362, 550, 470), outline=(40, 40, 45), width=9)
    d.line((398, 410, 402, 410), fill=(40, 40, 45), width=9)
    blob(img, (350, 450, 450, 600), (225, 172, 140))
    h = 14 + 100 * mouth
    d.chord((320, 660 - h, 480, 660 + h), 0, 180, fill=(90, 25, 30))
    d.arc((320, 660 - h, 480, 660 + h), 0, 180, fill=(170, 90, 85), width=8)
    d.line((315, 660, 485, 660), fill=(170, 90, 85), width=8)
    return img


HEADS = {"bardella": head_bardella, "marine": head_marine, "anchor": head_anchor}


def place_head(canvas, head, cx, cy, scale=1.0, angle=0.0):
    """Colle la tête (pivot au cou) avec rotation façon marionnette."""
    if angle:
        head = head.rotate(angle, resample=Image.BICUBIC, center=PIVOT)
    if scale != 1.0:
        head = head.resize((int(HEAD_W * scale), int(HEAD_H * scale)), Image.LANCZOS)
    canvas.alpha_composite(head, (int(cx - PIVOT[0] * scale), int(cy - PIVOT[1] * scale)))


# ------------------------------------------------------------------ corps & accessoires

def body_suit(canvas, cx, top, width, color, shirt=(245, 245, 250), tie=(30, 40, 90), bottom=1440):
    d = ImageDraw.Draw(canvas)
    w = width / 2
    d.polygon([(cx - w * .62, top), (cx + w * .62, top), (cx + w, top + 140), (cx + w * 1.05, bottom),
               (cx - w * 1.05, bottom), (cx - w, top + 140)], fill=color)
    blob(canvas, (cx - w * 1.02, top - 10, cx - w * .2, top + 230), color)
    blob(canvas, (cx + w * .2, top - 10, cx + w * 1.02, top + 230), color)
    d.polygon([(cx - 95, top - 5), (cx + 95, top - 5), (cx, top + 260)], fill=shirt)
    if tie:
        d.polygon([(cx - 26, top + 20), (cx + 26, top + 20), (cx + 40, top + 230), (cx, top + 290),
                   (cx - 40, top + 230)], fill=tie)
        d.polygon([(cx - 32, top - 5), (cx + 32, top - 5), (cx + 22, top + 32), (cx - 22, top + 32)], fill=tie)
    d.line((cx - 95, top - 5, cx - 10, top + 270), fill=tuple(max(c - 25, 0) for c in color), width=14)
    d.line((cx + 95, top - 5, cx + 10, top + 270), fill=tuple(max(c - 25, 0) for c in color), width=14)


def hand(canvas, cx, cy, r, skin):
    blob(canvas, (cx - r, cy - r * .8, cx + r, cy + r * .8), skin)


def smartphone(canvas, cx, cy, angle=-12, glow=False):
    ph = Image.new("RGBA", (190, 340), (0, 0, 0, 0))
    d = ImageDraw.Draw(ph)
    d.rounded_rectangle((0, 0, 189, 339), 26, fill=(25, 25, 30))
    d.rounded_rectangle((12, 18, 177, 320), 16, fill=(120, 190, 255) if glow else (60, 90, 140))
    ph = ph.rotate(angle, resample=Image.BICUBIC, expand=True)
    canvas.alpha_composite(ph, (int(cx - ph.width / 2), int(cy - ph.height / 2)))


def handbag(canvas, cx, cy, shake=0.0, t=0.0):
    dx = math.sin(t * 90) * 14 * shake
    rot = math.sin(t * 70) * 6 * shake
    bag = Image.new("RGBA", (420, 360), (0, 0, 0, 0))
    d = ImageDraw.Draw(bag)
    d.arc((90, 10, 330, 220), 180, 360, fill=(70, 30, 25), width=26)
    blob(bag, (20, 110, 400, 350), (120, 45, 40), gloss=0.25)
    d.rectangle((185, 150, 235, 185), fill=(220, 190, 90))
    if shake:
        blob(bag, (150, 70, 270, 150), (130, 210, 255), gloss=0.8)  # écran qui s'allume dans le sac
    bag = bag.rotate(rot, resample=Image.BICUBIC)
    canvas.alpha_composite(bag, (int(cx - 210 + dx), int(cy - 180)))
    if shake:
        d = ImageDraw.Draw(canvas)
        for k in range(3):
            r = 230 + k * 45 + (t * 400 % 45)
            d.arc((cx - r, cy - r * .8, cx + r, cy + r * .8), 200, 250, fill=(255, 255, 255), width=10)
            d.arc((cx - r, cy - r * .8, cx + r, cy + r * .8), 290, 340, fill=(255, 255, 255), width=10)


def cat(canvas, cx, cy, mouth=0.0, surprised=False, t=0.0):
    orange, dark = (235, 140, 55), (190, 95, 30)
    d = ImageDraw.Draw(canvas)
    blob(canvas, (cx - 230, cy - 60, cx + 230, cy + 200), orange)                # corps en miche
    d.polygon([(cx + 170, cy + 20), (cx + 300, cy - 160), (cx + 240, cy + 120)], fill=orange)  # queue
    blob(canvas, (cx - 170, cy - 260, cx + 170, cy + 40), orange)                # tête
    for s in (-1, 1):
        d.polygon([(cx + s * 150, cy - 180), (cx + s * 120, cy - 330), (cx + s * 40, cy - 240)], fill=orange)
        d.polygon([(cx + s * 128, cy - 200), (cx + s * 115, cy - 290), (cx + s * 65, cy - 235)], fill=(240, 160, 170))
    for k in (-1, 0, 1):
        d.line((cx + k * 40, cy - 255, cx + k * 30, cy - 205), fill=dark, width=10)
    er = 42 if surprised else 32
    for s in (-1, 1):
        ex = cx + s * 70
        d.ellipse((ex - er, cy - 160 - er, ex + er, cy - 160 + er), fill=(190, 220, 60))
        pw = 16 if surprised else 7
        d.ellipse((ex - pw, cy - 160 - er + 6, ex + pw, cy - 160 + er - 6), fill=(10, 10, 10))
    d.polygon([(cx - 18, cy - 105), (cx + 18, cy - 105), (cx, cy - 85)], fill=(230, 110, 130))
    if mouth > 0.1:
        d.ellipse((cx - 30, cy - 85, cx + 30, cy - 70 + 70 * mouth), fill=(90, 20, 30))
    else:
        d.arc((cx - 40, cy - 100, cx, cy - 65), 0, 180, fill=(80, 40, 30), width=6)
        d.arc((cx, cy - 100, cx + 40, cy - 65), 0, 180, fill=(80, 40, 30), width=6)
    for s in (-1, 1):
        for k in (-1, 0, 1):
            d.line((cx + s * 60, cy - 90 + k * 14, cx + s * 210, cy - 100 + k * 30), fill=(250, 250, 240), width=4)


def sweat_drop(canvas, x, y, s=1.0):
    blob(canvas, (x - 22 * s, y, x + 22 * s, y + 60 * s), (150, 210, 255), gloss=0.7)
    d = ImageDraw.Draw(canvas)
    d.polygon([(x - 18 * s, y + 20 * s), (x + 18 * s, y + 20 * s), (x, y - 30 * s)], fill=(150, 210, 255))


def soft(img, r=0.8):
    return img.filter(ImageFilter.GaussianBlur(r))
