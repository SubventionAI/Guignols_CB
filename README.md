# Les Guignols — Le Come-Back

Faire revivre l'esprit des *Guignols de l'info* (Canal+, 1988-2018) avec des
marionnettes générées par programme et des personnalités politiques d'aujourd'hui.

## Version actuelle : épisode 1 v4, nouveau style 3D animé par IA

- `output/guignols_comeback_ep1_v4.mp4` en 4:3, et `output/guignols_comeback_ep1_v4_vertical.mp4`

Ce qui change par rapport à la v3 (retours de Noa : bouches bizarres, tout le
reste immobile, rendu pas beau, trop collé aux marionnettes en latex) :

- **Une nouvelle direction artistique**, « Guignols nouvelle génération » :
  personnages 3D caricaturaux lisses (style film d'animation), têtes
  surdimensionnées, plateau de JT moderne avec vue sur Paris. Le style est
  volontairement cartoon, pour qu'on ne puisse pas le confondre avec un
  deepfake. Images dans `assets/v4/`.
- **Une animation faciale par IA (SadTalker)** : à partir de la voix, le
  modèle anime tout le visage (lèvres, mâchoire, joues, sourcils, mouvements
  de tête, clignements), y compris quand le personnage écoute en silence.
  `src/sadtalker_batch.py` enchaîne tous les plans en ne chargeant les
  modèles qu'une fois.
- **La netteté « dessin animé »** : le visage animé est repassé dans
  Real-ESRGAN (modèle anime) pour garder des contours nets
  (`src/enhance_faces.py`).
- **Le même sketch et les mêmes voix** que la v3.

```sh
python3 src/make_video_v4.py prepare            # minutage + pistes audio + jobs.json
cd /home/user/SadTalker && /home/user/st-venv/bin/python <repo>/src/sadtalker_batch.py <repo>/build/v4/anim/jobs.json
/home/user/st-venv/bin/python src/enhance_faces.py build/v4/anim
python3 src/make_video_v4.py render
```

## Épisode 1 v3 (remplacée), « C'est fou ce que les gens se ressemblent » (~57 s)

- `output/guignols_comeback_ep1_v3.mp4`, en 4:3 (1440x1080)
- `output/guignols_comeback_ep1_v3_vertical.mp4`, en 9:16 pour les réseaux

Ce qui change par rapport à la v2 (retours de Noa : voix robotiques, mâchoire
irregardable, sketch sans rythme, présentateur inconnu) :

- **La synchro labiale par variantes.** Pour chaque plan, des variantes de la
  même image ont été générées (bouche entrouverte, grande ouverte, en « O »,
  yeux fermés). À chaque image vidéo, on colle la bonne forme de bouche :
  l'ouverture est choisie d'après le volume de la voix, la voyelle arrondie
  d'après les formants. S'y ajoutent des clignements d'yeux aléatoires.
  Voir `src/make_video_v3.py`.
- **Des voix neuronales XTTS-v2** (`src/voices_xtts.py`). Elles partent de voix
  de lecteurs anonymes LibriVox (domaine public), choisies pour leur timbre,
  sans clonage d'une personnalité. Pour chaque réplique, plusieurs prises sont
  générées et la meilleure est gardée automatiquement : Whisper vérifie le
  texte et les mots-clés, UTMOS note le naturel. Les pauses sont raccourcies
  pour le rythme ping-pong.
- **Le présentateur est Pascal Praud**, en marionnette complaisante qui
  répète tout ce que dit Bardella, inspiré de PPD face à Balladur. Le sketch
  joue sur le déni, l'escalade de la sonnerie, la diversion (« on passe à un
  sujet grave : l'insécurité ! ») et la chute en rappel, avec applaudissements.
- **Les légendes ironiques** façon Guignols : « PASCAL PRAUD — JOURNALISTE
  IMPARTIAL », etc.

```sh
pip install coqui-tts[codec] "transformers>=4.57,<5" faster-whisper praat-parselmouth librosa opencv-python-headless
git clone https://github.com/tarepan/SpeechMOS /tmp/SpeechMOS   # note de naturel UTMOS
COQUI_TOS_AGREED=1 python3 src/gen_voices_v3.py   # voix (long sur CPU)
python3 src/make_video_v3.py && ./src/make_vertical.sh output/guignols_comeback_ep1_v3.mp4 output/guignols_comeback_ep1_v3_vertical.mp4
```

Licence : le modèle XTTS-v2 est sous Coqui Public Model License, réservée à
un usage non commercial.

## Épisode 1 v2 (remplacée), « Ce n'est pas mon écriture » (~55 s)

- `output/guignols_comeback_ep1_v2.mp4`, en 4:3 (1440x1080), comme à l'époque
- `output/guignols_comeback_ep1_v2_vertical.mp4`, en 9:16 pour les réseaux

Cette version a été refaite après avoir **visionné de vrais sketchs** de 1995
(analyse dans `research/NOTES.md`). Elle comprend :

- **les marionnettes en latex**, générées en images (Canva) dans le décor du JT
  des Guignols, puis animées : mâchoire articulée synchronisée sur la voix,
  dodelinement de la tête, sac qui vibre ;
- **les voix d'imitation caricaturées**, sans clonage : une voix de synthèse
  Piper déformée avec Praat et sox (`src/voices.py`) ;
- **un scénario construit sur le déni en boucle** du sketch Balladur / PPD,
  avec le gag du téléphone qui sonne dans le sac de Marine, les
  applaudissements et le « Voilà. Sans transition… ».

```sh
pip install piper-tts praat-parselmouth pillow numpy
# voix Piper (voices/) : fr_FR-tom-medium, fr_FR-siwis-medium, fr_FR-upmc-medium
#   https://huggingface.co/rhasspy/piper-voices/tree/main/fr/fr_FR
python3 src/make_video_v2.py && ./src/make_vertical.sh
```

## Première version (v1, abandonnée)

**Épisode 1 : « Mais qui a bien pu écrire ça ? »** (~42 s), avec des
marionnettes dessinées par le code et des voix robotiques. Elle a été jugée
trop éloignée du rendu des Guignols.

- `output/guignols_comeback_ep1.mp4`, en 16:9 (1280x720)
- `output/guignols_comeback_ep1_vertical.mp4`, en 9:16 pour Shorts, TikTok et Reels

## L'actu de départ

Le 1er octobre 2026, Mediapart publie des messages antisémites envoyés en 2013
sur Messenger. Le site les attribue à Jordan Bardella. Il dit les avoir fait
authentifier via Meta et par un commissaire de justice. Les éléments
biographiques présents dans la conversation pointent vers lui : une mère née en
Italie, un échec au concours de Sciences Po, une interview au *Parisien*.
Bardella **dément** être l'auteur. Il parle de « montages grossiers » et annonce
une plainte pour faux, usage de faux et diffamation. Marine Le Pen maintient
« totalement » sa confiance et dénonce des « manipulations ».

Le sketch ne reproduit **aucun** des messages. Les anciens messages sont floutés
à l'écran. Le carton final rappelle que Bardella conteste.

## Ce qu'on reprend des Guignols (période Chirac / Balladur)

| Mécanisme | Dans les Guignols | Dans l'épisode 1 |
|---|---|---|
| Duo à contraste | Chirac, impatient et sanguin, face à Balladur, hautain et impassible | Bardella, gendre idéal paniqué, face à Marine, sphinx rusé |
| Ironie dramatique | Le public sait ce que le personnage ignore | Bardella énumère les indices qui le désignent : « Mais qui ça peut bien être ?! » |
| Fausse amitié / rivalité | « mon ami de trente ans » | « Mystère, mon Jordan », dit avec un regard caméra complice |
| Regard caméra | La marionnette prend le public à témoin | Gros plans de Marine face caméra |
| Détournement de vraies phrases | Les citations réelles sont réutilisées à contre-sens | « Je maintiens TOTALEMENT ma confiance », pendant que son sac sonne |
| Running gag et escalade | « Putain, deux ans ! » | Le sac qui sonne : 1 fois, puis 2, puis en fond, puis sur le carton final |
| Caricature physique | Têtes énormes, traits poussés au maximum | Brushing gominé et sourire « dentifrice » étincelant ; casque blond et paupières de féline |
| Faux JT | Présentateur au bureau, encart incrusté, bandeau | Ouverture en JT avec encart « AFFAIRE BARDELLA » |
| Chute méta | Les marionnettes commentent l'émission | « C'est la faute à l'IA ! » / « D'ailleurs, ce sketch aussi. » |
| Gag absurde récurrent | — | Le chat (Marine éleveuse de chats) : alibi, portrait « Président d'honneur » |

## Découpage

1. **Générique** : « LES GUIGNOLS — LE COME-BACK », les marionnettes surgissent.
2. **JT** : le présentateur résume les faits. Encart Bardella, bandeau « DIRECT ».
3. **Bureau, plan large** : Bardella : « Marine, c'est un complot ! Un montage grossier ! »
4. **Gros plan Bardella**, il lit son téléphone : « Mère italienne… recalé à Sciences Po… interview au Parisien… Mais qui ça peut bien être ?! »
5. **Gros plan Marine**, regard caméra : « Mystère, mon Jordan. Mystère. »
6. **Plan large** : « J'ai une idée ! J'écris au destinataire ! »
7. **Insert téléphone** : il tape « Coucou, c'est moi ! » et l'envoie.
8. **Plan large** : DRING, le sac de Marine vibre et s'allume. Elle sue.
9. **Gros plan Marine** : « … C'est le chat. » Le chat : « Miaou ? »
10. **Gros plan Bardella** : « Bizarre… »
11. **Insert téléphone** : « T'es qui ? »
12. **Plan large** : DRING DRING.
13. **Gros plan Marine**, fière, pendant que le sac sonne : « Je maintiens TOTALEMENT ma confiance à Jordan ! »
14. **Plan large** : Bardella : « De toute façon, c'est la faute à l'intelligence artificielle ! »
15. **Gros plan Marine** : « Voilà. D'ailleurs… ce sketch aussi. »
16. **Carton final** : avertissement « parodie ». Le sac sonne encore.

## Fabrication

Tout est généré localement, sans banque d'images ni modèle vidéo externe :

- `src/puppets.py` : les marionnettes « latex » dessinées avec Pillow (ombrage
  radial, têtes surdimensionnées, paupières, bouches articulées), plus le chat,
  le sac et le téléphone.
- `src/audio.py` : les voix de synthèse (espeak-ng + mbrola) traitées avec sox
  pour caricaturer chaque timbre (voix grave et éraillée pour Marine, voix
  montante pour Bardella), et les bruitages synthétisés (fanfare, sonnerie,
  clavier, envoi).
- `src/episode1.py` : le scénario (plans, répliques, sous-titres, bruitages).
- `src/make_video.py` : le moteur. Il gère le minutage, la synchro des bouches
  sur l'amplitude de la voix, le dodelinement des têtes, les caméras (plan
  large / gros plans) et le montage ffmpeg.
- `src/make_vertical.sh` : la déclinaison verticale 9:16.

```sh
sudo apt-get install espeak-ng mbrola mbrola-fr1 mbrola-fr4 sox ffmpeg fonts-roboto
pip install pillow numpy
python3 src/make_video.py            # -> output/guignols_comeback_ep1.mp4
./src/make_vertical.sh               # -> output/guignols_comeback_ep1_vertical.mp4
```

Pour écrire un nouvel épisode, copier `src/episode1.py` et modifier la liste
`SEGMENTS`. Le moteur s'occupe du reste.

## Pistes pour aller plus loin

- **Voix** : le point faible actuel, ce sont les voix robotiques de synthèse.
  Un vrai imitateur, ou un outil de TTS ou de clonage de voix (en respectant le
  droit à l'image et à la voix des personnes), changerait tout.
- **Image** : on peut générer les têtes en latex avec un modèle d'image (style
  « latex puppet, Spitting Image »), puis les animer avec un outil de
  lip-sync.
- Ajouter d'autres marionnettes (Macron, Mélenchon, Attal…) et un vrai
  « PPD-like » récurrent au JT.

> Parodie satirique. Les personnages sont des caricatures et toutes les
> répliques sont inventées.
