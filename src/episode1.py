"""Épisode 1 — « Mais qui a bien pu écrire ça ? »

Chaque plan : kind (title/anchor/office/phone/end), cam (wide/cu_b/cu_m),
lines = [(personnage, texte prononcé, sous-titre)], sfx = [(bruitage, t, volume)],
ring = sac de Marine qui sonne (True ou (début, fin)), b/m = humeur et regard
de Bardella / Marine.
"""

SEGMENTS = [
    # Générique
    dict(kind="title", dur=2.3, sfx=[("jingle", 0.0, 0.9)]),

    # Le JT plante le décor (fait réel, formulé prudemment)
    dict(kind="anchor", lines=[
        ("anchor", "Selon Médiapart, des messages antisémites de 2013 seraient signés Jordan Bardella, qui dément.",
         "Selon Mediapart, des messages antisémites de 2013 seraient signés Jordan Bardella, qui dément."),
    ]),

    # Bureau : Bardella outré, Marine impassible
    dict(kind="office", cam="wide",
         lines=[("bardella", "Marine, c'est un complot ! Un montage grossier !",
                 "Marine, c'est un complot ! Un montage grossier !")],
         b=dict(mood="angry", gaze=(1, 0)), m=dict(mood="sly", gaze=(-1, 0))),

    # Le comique de l'aveuglement : il lit les indices qui le désignent
    dict(kind="office", cam="cu_b",
         lines=[("bardella", "Mère italienne... recalé à Sciences Po... interview au Parisien... Mais qui ça peut bien être ?",
                 "Mère italienne… recalé à Sciences Po… interview au Parisien… Mais qui ça peut bien être ?!")],
         b=dict(mood="suspicious", gaze=(0.7, 1)), phone_glow=True),

    # Regard caméra complice, signature des Guignols
    dict(kind="office", cam="cu_m",
         lines=[("marine", "Mystère, mon Jordan. Mystère.", "Mystère, mon Jordan. Mystère.")],
         m=dict(mood="sly", gaze=(0, 0))),

    dict(kind="office", cam="wide",
         lines=[("bardella", "J'ai une idée ! J'écris au destinataire !",
                 "J'ai une idée ! J'écris au destinataire !")],
         b=dict(mood="idea", gaze=(0, -0.3)), m=dict(mood="nervous", gaze=(-1, 0))),

    # Insert téléphone
    dict(kind="phone", dur=2.0, text="Coucou, c'est moi !", type_end=1.2, send_at=1.45,
         sfx=[("typing", 0.1, 0.8), ("whoosh", 1.4, 0.8)]),

    # DRING : c'est le sac de Marine qui sonne
    dict(kind="office", cam="wide", dur=1.25, ring=(0.05, 1.2),
         sfx=[("ring", 0.05, 0.9)],
         b=dict(mood="suspicious", gaze=(1, 0.6)), m=dict(mood="nervous", gaze=(-0.8, 0.8), sweat=True)),

    dict(kind="office", cam="cu_m",
         lines=[("marine", "C'est le chat.", "… C'est le chat."),
                ("cat", "Miaou ?", "Le chat : « Miaou ? »")],
         m=dict(mood="nervous", gaze=(-1, 0))),

    dict(kind="office", cam="cu_b",
         lines=[("bardella", "Bizarre...", "Bizarre…")],
         b=dict(mood="suspicious", gaze=(1, 0.2)), phone_glow=True),

    dict(kind="phone", dur=1.6, text="T'es qui ?", type_end=0.8, send_at=1.0,
         sfx=[("typing", 0.1, 0.6), ("whoosh", 0.95, 0.8)]),

    # Double sonnerie, Marine transpire
    dict(kind="office", cam="wide", dur=1.7, ring=True,
         sfx=[("ring", 0.05, 0.9), ("ring", 0.9, 0.9)],
         b=dict(mood="suspicious", gaze=(1, 0.5)), m=dict(mood="nervous", gaze=(0, 0), sweat=True)),

    # La vraie phrase de soutien, détournée — pendant que le sac sonne encore
    dict(kind="office", cam="cu_m", ring=True,
         lines=[("marine", "Je maintiens totalement ma confiance à Jordan !",
                 "Je maintiens TOTALEMENT ma confiance à Jordan !")],
         sfx=[("ring", 0.1, 0.35), ("ring", 1.2, 0.35), ("ring", 2.3, 0.35)],
         m=dict(mood="proud", gaze=(0, 0))),

    dict(kind="office", cam="wide",
         lines=[("bardella", "De toute façon, c'est la faute à l'intelligence artificielle !",
                 "De toute façon, c'est la faute à l'intelligence artificielle !")],
         b=dict(mood="idea", gaze=(-0.2, 0)), m=dict(mood="sly", gaze=(-1, 0))),

    # Chute méta : la vidéo est elle-même faite par une IA
    dict(kind="office", cam="cu_m", tail=0.6,
         lines=[("marine", "Voilà. D'ailleurs, ce sketch aussi.", "Voilà. D'ailleurs… ce sketch aussi.")],
         m=dict(mood="sly", gaze=(0, 0))),

    # Carton final (et le sac qui sonne encore)
    dict(kind="end", dur=4.2, ring=(2.4, 3.4), sfx=[("sting", 0.0, 0.8), ("ring", 2.4, 0.5)]),
]
