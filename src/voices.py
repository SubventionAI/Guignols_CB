"""Voix caricaturées « façon imitateur des Guignols ».

Base : synthèse neuronale Piper (voix françaises génériques, aucune voix réelle
clonée). Caricature : on pousse des traits audibles connus du public avec Praat
(« Change gender » : hauteur, étendue mélodique, timbre, débit), puis on ajoute
du grain (éraillement, nasalité) avec sox.

Repères mesurés sur des interviews (hauteur médiane) : Bardella ~110 Hz,
Le Pen ~150 Hz. La caricature exagère : Jordan plus juvénile et récitant,
Marine plus grave, plus lente, plus éraillée.
"""
import os
import subprocess
import wave

import numpy as np
import parselmouth
from parselmouth.praat import call
from piper import PiperVoice
from piper.config import SynthesisConfig

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOICE_DIR = os.path.join(ROOT, "voices")
SR = 44100

CHARACTERS = {
    # Jordan : gendre idéal qui récite ses éléments de langage, débit mitraillette,
    # mélodie très régulière, un peu nasal et propre sur lui.
    "bardella": dict(model="fr_FR-tom-medium", speaker=None, length=0.86, noise=0.5,
                     formant=1.04, pitch=122, prange=0.8, dur=1.0,
                     sox=["highpass", "110", "equalizer", "1300", "1.2q", "+5", "treble", "+3"]),
    # Marine : voix de rocaille, grave, traînante, appuyée, cigarette-whisky.
    "marine": dict(model="fr_FR-siwis-medium", speaker=None, length=1.12, noise=0.75,
                   formant=0.94, pitch=128, prange=1.25, dur=1.0,
                   sox=["overdrive", "6", "18", "bass", "+6", "180", "equalizer", "2800", "1q", "+3",
                        "lowpass", "7500"]),
    # Présentateur : voix posée de JT, un peu feutrée
    "anchor": dict(model="fr_FR-upmc-medium", speaker=1, length=0.9, noise=0.6,
                   formant=1.0, pitch=105, prange=1.1, dur=1.0, sox=["bass", "+3"]),
    "cat": dict(model="fr_FR-siwis-medium", speaker=None, length=1.3, noise=0.8,
                formant=1.25, pitch=420, prange=2.0, dur=1.0, sox=[]),
}

_cache = {}


def _voice(model):
    if model not in _cache:
        _cache[model] = PiperVoice.load(os.path.join(VOICE_DIR, model + ".onnx"))
    return _cache[model]


def speak(character, text, out_path):
    c = CHARACTERS[character]
    raw = out_path + ".raw.wav"
    cfg = SynthesisConfig(speaker_id=c["speaker"], length_scale=c["length"], noise_scale=c["noise"])
    with wave.open(raw, "wb") as w:
        _voice(c["model"]).synthesize_wav(text, w, syn_config=cfg)
    snd = parselmouth.Sound(raw)
    snd = call(snd, "Change gender", 60, 500, c["formant"], c["pitch"], c["prange"], c["dur"])
    peak = np.abs(snd.values).max()
    if peak > 0:
        snd.values = snd.values * (0.8 / peak)
    mid = out_path + ".mid.wav"
    snd.save(mid, "WAV")
    subprocess.run(["sox", mid, "-r", str(SR), "-c", "1", "-b", "16", out_path, *c["sox"], "norm", "-1.5"],
                   check=True, stderr=subprocess.DEVNULL)
    os.remove(raw)
    os.remove(mid)
    with wave.open(out_path) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return x
