"""Pré-génère toutes les répliques de l'épisode v3 (long : à lancer en tâche de fond)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import voices_xtts
from episode1_v3 import SEGMENTS
OUT = os.path.join(voices_xtts.ROOT, "build", "v3", "voices")
os.makedirs(OUT, exist_ok=True)
for i, seg in enumerate(SEGMENTS):
    for j, (spk, say, sub) in enumerate(seg.get("lines", [])):
        p = os.path.join(OUT, f"line_{i:02d}_{j}.wav")
        if os.path.exists(p):
            continue
        print(f"{i:02d}.{j} {spk}: {say}", flush=True)
        voices_xtts.speak(spk, say, p)
print("TERMINE", flush=True)
