"""Épisode 1 (v2) — « Ce n'est pas mon écriture »

Construit sur le modèle du sketch Balladur / PPD de janvier 1995 : l'invité
nie en boucle face aux preuves (« Je n'ai jamais rien écrit de tel. » —
« Ah si, c'est là. » — « Ce n'est pas mon écriture. »), puis bascule dans le
gag du téléphone qui sonne dans le sac de Marine.

shot : plan (image) — anchor / bardella / marine / duo / marine_phone
lines : (personnage, texte prononcé, sous-titre)
sfx : (bruitage, t, volume)
tag : petit bandeau rouge en bas à gauche, comme au JT des Guignols
"""

SEGMENTS = [
    dict(shot="title", dur=2.3, sfx=[("jingle", 0.0, 0.8)]),

    dict(shot="anchor", tag="MEDIAPART", lines=[
        ("anchor", "Médiapart attribue à Jordan Bardella des messages antisémites de 2013. Il est avec nous. Bonsoir.",
         "Mediapart attribue à Jordan Bardella des messages antisémites de 2013. Il est avec nous. Bonsoir."),
    ]),
    dict(shot="bardella", lines=[
        ("bardella", "Bonsoir. Ce sont des montages grossiers. Je n'ai jamais rien écrit de tel.",
         "Bonsoir. Ce sont des montages grossiers. Je n'ai jamais rien écrit de tel."),
    ]),
    dict(shot="anchor", lines=[
        ("anchor", "Il y a votre mère italienne, votre échec à Sciences Po, votre interview au Parisien...",
         "Il y a votre mère italienne, votre échec à Sciences Po, votre interview au Parisien…"),
    ]),
    dict(shot="bardella", lines=[("bardella", "Ce n'est pas mon écriture.", "Ce n'est pas mon écriture.")]),
    dict(shot="anchor", lines=[("anchor", "C'est Messenger. Il n'y a pas d'écriture.", "C'est Messenger. Il n'y a pas d'écriture.")]),
    dict(shot="bardella", lead=0.6, lines=[("bardella", "Ce n'est pas mon Messendjeur.", "… Ce n'est pas mon Messenger.")]),

    dict(shot="marine", lines=[
        ("marine", "Jordan a toute ma confiance. Totalement.", "Jordan a toute ma confiance. Totalement."),
    ]),
    dict(shot="duo", lines=[
        ("bardella", "Je vais vous le prouver : j'écris au destinataire, on verra bien qui répond !",
         "Je vais vous le prouver : j'écris au destinataire, on verra bien qui répond !"),
    ], sfx_after=[("typing", 0.0, 0.7), ("ring", 1.3, 0.9)], extra=2.3, ring_from=1.3),

    dict(shot="marine", ring=True, lines=[("marine", "C'est mon chat.", "… C'est mon chat.")],
         sfx=[("ring", 0.0, 0.5)]),

    dict(shot="duo", dur=2.4, sfx=[("typing", 0.1, 0.7), ("ring", 0.9, 0.9), ("ring", 1.7, 0.9)], ring_from=0.9),

    dict(shot="anchor", ring=True, lines=[
        ("anchor", "Madame Le Pène... vous ne décrochez pas ?", "Madame Le Pen… vous ne décrochez pas ?"),
    ], sfx=[("ring", 0.0, 0.35), ("ring", 0.9, 0.35)]),

    dict(shot="marine_phone", lead=0.5, lines=[
        ("marine", "Allô ? ... Oui. Coucou, mon Jordanne.", "Allô ?… Oui. Coucou, mon Jordan."),
    ]),
    dict(shot="bardella", lead=0.8, lines=[("bardella", "Marine ?", "… Marine ?")], tail=0.9,
         sfx_after=[("applause", 0.15, 0.55)]),

    dict(shot="anchor", tail=0.4, lines=[("anchor", "Voilà. Sans transition...", "Voilà. Sans transition…")],
         sfx_after=[("sting", 0.0, 0.7)], extra=0.3),

    dict(shot="end", dur=3.8),
]
