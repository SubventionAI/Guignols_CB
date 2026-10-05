# Les Guignols — Le Come-Back

Faire revivre l'esprit des *Guignols de l'info* (Canal+, 1988-2018) avec des
marionnettes générées par programme et des personnalités politiques d'aujourd'hui.

**Épisode 1 : « Mais qui a bien pu écrire ça ? »** (~42 s)

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
