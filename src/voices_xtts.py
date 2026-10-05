"""Voix v3 : synthèse neuronale XTTS-v2 (bien plus naturelle que Piper).

Chaque personnage part d'une voix de référence ANONYME (lecteurs bénévoles
LibriVox, domaine public) choisie pour son timbre : on ne clone aucune
personnalité. La caricature vient du choix du timbre, du débit et d'un léger
traitement (Marine plus grave et éraillée, Bardella plus rapide).

Pour chaque réplique : plusieurs prises, et on garde la meilleure selon
Whisper (le texte est-il bien dit, sans mots parasites ?) et UTMOS (naturel).
"""
import difflib
import os
import re
import subprocess

os.environ.setdefault("COQUI_TOS_AGREED", "1")

import librosa
import numpy as np
import torch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, "research", "refvoices", "clips")
SR = 44100

CHARACTERS = {
    # Praud : conteur animé, débit rapide, voix rocailleuse d'indignation
    "praud": dict(ref="praud_p3_long.wav", speed=1.12, temp=0.8, sox=["bass", "+2"]),
    # Bardella : jeune voix lisse, récitante, rapide
    "bardella": dict(ref="bard_a_long.wav", speed=1.1, temp=0.65, sox=["pitch", "60", "treble", "+2"]),
    # Marine : voix grave et éraillée, lente
    "marine": dict(ref="marine_a_long.wav", speed=0.95, temp=0.7,
                   sox=["pitch", "-170", "overdrive", "3", "bass", "+4"]),
}

_tts = _mos = _wm = None


def _models():
    global _tts, _mos, _wm
    if _tts is None:
        from TTS.api import TTS
        from faster_whisper import WhisperModel
        torch.set_num_threads(4)
        _tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        _mos = torch.hub.load("/tmp/SpeechMOS", "utmos22_strong", source="local", trust_repo=True)
        _wm = WhisperModel("small", device="cpu", compute_type="int8")
    return _tts, _mos, _wm


def _norm(s):
    s = s.lower().replace("’", "'")
    s = re.sub(r"[^a-zàâäéèêëîïôöùûüç0-9' ]", " ", s)
    return " ".join(s.split())


def score(path, text):
    _, mos, wm = _models()
    y, _ = librosa.load(path, sr=16000)
    m = float(mos(torch.from_numpy(y).unsqueeze(0), 16000))
    heard = " ".join(s.text for s in wm.transcribe(path, language="fr")[0])
    sim = difflib.SequenceMatcher(None, _norm(text), _norm(heard)).ratio()
    return m, sim, heard


def speak(character, text, out_path, takes=3, must=()):
    tts, _, _ = _models()
    c = CHARACTERS[character]
    best = None
    for k in range(takes):
        torch.manual_seed(1000 + k)
        raw = f"{out_path}.take{k}.wav"
        tts.tts_to_file(text=text, speaker_wav=os.path.join(REF, c["ref"]), language="fr",
                        file_path=raw, speed=c["speed"], temperature=c["temp"])
        proc = f"{out_path}.take{k}.p.wav"
        subprocess.run(["sox", raw, "-r", str(SR), "-c", "1", "-b", "16", proc, *c["sox"], "norm", "-1.5"],
                       check=True, stderr=subprocess.DEVNULL)
        m, sim, heard = score(proc, text)
        total = sim * 4 + m
        if must and not all(w in _norm(heard) for w in must):
            total -= 3
        print(f"    [{character}] prise {k}: sim={sim:.2f} mos={m:.2f} | {heard.strip()}", flush=True)
        if best is None or total > best[0]:
            best = (total, proc)
        if sim > 0.97 and m > 3.3 and (not must or total > 6):
            break
    os.replace(best[1], out_path)
    for f in os.listdir(os.path.dirname(out_path) or "."):
        p = os.path.join(os.path.dirname(out_path), f)
        if ".take" in f and p.startswith(out_path):
            os.remove(p)
    y, _ = librosa.load(out_path, sr=SR)
    return y.astype(np.float32)
