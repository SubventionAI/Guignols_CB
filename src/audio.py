"""Voix de synthèse (espeak-ng + mbrola) et bruitages générés en numpy."""
import os
import subprocess
import wave

import numpy as np

SR = 44100

# Réglages de voix : caricature sonore de chaque marionnette.
VOICES = {
    # Bardella : jeune premier pressé, voix montante et enjouée
    "bardella": dict(voice="mb-fr1", speed=200, pitch=70, sox=["pitch", "120", "treble", "+4"]),
    # Marine : voix grave et éraillée (pitch bas + saturation légère)
    "marine": dict(voice="mb-fr4", speed=150, pitch=20,
                   sox=["pitch", "-330", "overdrive", "6", "bass", "+5", "reverb", "8"]),
    # Présentateur du JT : posé, neutre
    "anchor": dict(voice="mb-fr1", speed=190, pitch=40, sox=["pitch", "-120", "reverb", "12"]),
    # Le chat
    "cat": dict(voice="mb-fr4", speed=120, pitch=99, sox=["pitch", "500"]),
}


def tts(speaker, text, out_path):
    """Synthétise `text` avec la voix de `speaker` -> wav mono 44.1 kHz."""
    v = VOICES[speaker]
    raw = out_path + ".raw.wav"
    subprocess.run(["espeak-ng", "-v", v["voice"], "-s", str(v["speed"]), "-p", str(v["pitch"]),
                    "-w", raw, text], check=True)
    subprocess.run(["sox", raw, "-r", str(SR), "-c", "1", out_path, *v["sox"], "norm", "-1"],
                   check=True)
    os.remove(raw)
    return load_wav(out_path)


def load_wav(path):
    with wave.open(path) as w:
        assert w.getframerate() == SR
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    return data.astype(np.float32) / 32768.0


def save_wav(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def envelope(x, fps):
    """Amplitude normalisée par image vidéo, pour la synchro des bouches."""
    hop = SR // fps
    n = int(np.ceil(len(x) / hop))
    env = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2) + 1e-9) for i in range(n)])
    env = env / (np.percentile(env, 95) + 1e-6)
    return np.clip(env, 0, 1)


# ---------------------------------------------------------------- bruitages

def _t(dur):
    return np.arange(int(dur * SR)) / SR


def _adsr(n, a=0.01, r=0.1):
    env = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    env[:na] = np.linspace(0, 1, na)
    if nr:
        env[-nr:] *= np.linspace(1, 0, nr)
    return env


def _brass(freq, dur, vol=0.3):
    t = _t(dur)
    x = sum((1 / k) * np.sin(2 * np.pi * freq * k * t + 0.3 * np.sin(2 * np.pi * 5 * t)) for k in range(1, 9))
    return vol * x / 2.5 * _adsr(len(t), 0.02, min(0.12, dur / 2))


def jingle():
    """Fanfare cuivrée façon générique de JT satirique."""
    notes = [(392, .14), (523, .14), (659, .14), (784, .32), (659, .14), (784, .6)]
    out = np.concatenate([_brass(f, d) for f, d in notes])
    # accord final + roulement de caisse claire
    chord = sum(_brass(f, 1.0, 0.18) for f in (523, 659, 784, 1046))
    out = np.concatenate([out, chord])
    roll = np.random.default_rng(1).normal(0, 0.12, len(out)) * (np.sin(2 * np.pi * 28 * np.arange(len(out)) / SR) > 0)
    roll *= np.linspace(0.2, 1, len(out)) ** 2
    return out + roll * 0.5


def sting():
    return np.concatenate([_brass(784, .12), _brass(523, .12), sum(_brass(f, .9, .2) for f in (392, 523, 659))])


def phone_ring(dur=1.0):
    """Sonnerie de portable : trille deux tons."""
    t = _t(dur)
    f = np.where(np.sin(2 * np.pi * 18 * t) > 0, 1320, 1760)
    x = 0.35 * np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.5
    x += 0.2 * np.sin(2 * np.pi * np.cumsum(f) / SR)
    # vibreur
    x += 0.15 * np.sin(2 * np.pi * 150 * t) * (np.sin(2 * np.pi * 3 * t) > -0.3)
    return x * _adsr(len(t), 0.005, 0.05)


def typing(dur=1.4, seed=2):
    rng = np.random.default_rng(seed)
    out = np.zeros(int(dur * SR))
    t = 0.0
    while t < dur - 0.05:
        n = int(0.025 * SR)
        click = rng.normal(0, 1, n) * np.exp(-np.linspace(0, 9, n)) * 0.35
        i = int(t * SR)
        out[i:i + n] += click
        t += rng.uniform(0.07, 0.16)
    return out


def whoosh(dur=0.45):
    t = _t(dur)
    f = 300 + 2600 * (t / dur) ** 2
    return 0.25 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / dur)


SFX = {"jingle": jingle, "sting": sting, "ring": phone_ring, "typing": typing, "whoosh": whoosh}
