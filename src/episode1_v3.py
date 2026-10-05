"""Épisode 1 (v3) — « C'est fou ce que les gens se ressemblent »

Inspirations tirées des vrais sketchs (research/NOTES.md) :
- le présentateur complaisant (PPD qui sert la soupe à Balladur, « sur France 2
  on ne me contredit jamais ») -> Pascal Praud qui répète tout ce que dit
  Bardella, comme un perroquet ;
- le déni face aux preuves (« ce n'est pas mon écriture ») ;
- l'escalade du gag (le sac de Marine qui sonne de plus en plus) ;
- la diversion du présentateur (« on passe à un sujet grave : l'insécurité ») ;
- la chute en rappel (callback) + applaudissements du public.

Chaque plan : shot, lines = [(perso, texte prononcé, sous-titre)], sfx, ring...
"""

SEGMENTS = [
    dict(shot="title", dur=2.2, sfx=[("jingle", 0.0, 0.8)]),

    dict(shot="praud", tag="MEDIAPART", caption=("PASCAL PRAUD", "JOURNALISTE IMPARTIAL"), lines=[
        ("praud", "Bonsoir ! C'est un scandale : le site Médiapart s'attaque à Jordan Bardella, pour des messages de 2013 ! Jordan, bonsoir !",
         "Bonsoir ! C'est un scandale : le site Mediapart s'attaque à Jordan Bardella pour des messages de 2013 ! Jordan, bonsoir !")]),
    dict(shot="bardella", caption=("JORDAN BARDELLA", "17 ANS EN 2013"), lines=[("bardella", "Bonsoir Pascal.", "Bonsoir Pascal.")]),
    dict(shot="praud", lines=[
        ("praud", "En 2013, vous aviez dix-sept ans ! C'était un enfant ! On fait le procès d'un enfant !",
         "En 2013, vous aviez 17 ans ! C'était un enfant ! On fait le procès d'un enfant !")]),
    dict(shot="bardella", lines=[("bardella", "Et en plus, ce n'est pas moi.", "Et en plus, ce n'est pas moi.")]),
    dict(shot="praud", lines=[("praud", "Et en plus, c'est pas lui !", "Et en plus, c'est pas lui !")]),
    dict(shot="praud", lines=[
        ("praud", "Bon, Média-parte dit que l'auteur a une mère italienne, et qu'il a raté Sciences Po.",
         "Bon, Mediapart dit que l'auteur a une mère italienne et qu'il a raté Sciences Po.")]),
    dict(shot="bardella", lead=0.5, lines=[
        ("bardella", "C'est fou ce que les gens se ressemblent.", "… C'est fou ce que les gens se ressemblent.")]),
    dict(shot="praud", lines=[
        ("praud", "C'est fou ce que les gens se ressemblent !", "C'est fou ce que les gens se ressemblent !")]),

    dict(shot="praud", lines=[("praud", "Marine Le Pen, vous le soutenez ?", "Marine Le Pen, vous le soutenez ?")]),
    dict(shot="marine", keep_last_pause=0.7, caption=("MARINE LE PEN", "ÉLEVEUSE DE CHATS"), lines=[
        ("marine", "Totalement. Jordan a toujours été très gentil avec moi. Même en 2013.",
         "Totalement. Jordan a toujours été très gentil avec moi… Même en 2013.")]),

    dict(shot="duo", lines=[
        ("bardella", "D'ailleurs, je vais vous prouver que c'est un faux. J'écris au destinataire !",
         "D'ailleurs, je vais vous prouver que c'est un faux. J'écris au destinataire !")],
         sfx_after=[("typing", 0.0, 0.7), ("ring", 1.2, 0.9)], extra=2.1, ring_from=1.2),
    dict(shot="praud", ring=True, lead=0.4, lines=[("praud", "Marine, ça sonne.", "… Marine, ça sonne.")],
         sfx=[("ring", 0.0, 0.4)]),
    dict(shot="marine", lines=[("marine", "C'est le chat.", "C'est le chat.")]),
    dict(shot="duo", dur=2.0, sfx=[("typing", 0.05, 0.7), ("ring", 0.7, 0.9), ("ring", 1.4, 0.9)], ring_from=0.7),
    dict(shot="praud", ring=True, lines=[
        ("praud", "Bon ! Pas de polémique ! On passe à un sujet grave : l'insécurité !",
         "Bon ! Pas de polémique ! On passe à un sujet grave : l'insécurité !")],
         sfx=[("ring", 0.0, 0.35), ("ring", 0.8, 0.35)]),

    dict(shot="marine_phone", lead=0.3, lines=[
        ("marine", "Allô ? Oui. Coucou, mon Jordan.", "Allô ? Oui… Coucou, mon Jordan.")]),
    dict(shot="bardella", lead=0.6, lines=[("bardella", "Marine ?", "… Marine ?")]),
    dict(shot="praud", lead=0.4, tail=0.3, lines=[
        ("praud", "C'est fou ce que les gens se ressemblent.", "C'est fou ce que les gens se ressemblent.")],
         sfx_after=[("applause", 0.0, 0.6)], extra=1.6),

    dict(shot="end", dur=3.6),
]
