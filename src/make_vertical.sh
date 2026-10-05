#!/bin/sh
# Version verticale 9:16 (Shorts / TikTok / Reels) : fond flouté + titre.
# Usage : ./src/make_vertical.sh [entrée.mp4] [sortie.mp4] [titre épisode]
set -e
cd "$(dirname "$0")/.."
IN=${1:-output/guignols_comeback_ep1_v2.mp4}
OUTV=${2:-output/guignols_comeback_ep1_v2_vertical.mp4}
EP=${3:-Ep. 1 - Ce n est pas mon écriture}
F=/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Black.ttf
ffmpeg -y -loglevel error -i "$IN" -filter_complex "\
[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:2,eq=brightness=-0.25[bg];\
[0:v]scale=1080:-2[fg];\
[bg][fg]overlay=0:(H-h)/2,\
drawtext=fontfile=$F:text='LES GUIGNOLS':fontcolor=white:fontsize=130:borderw=8:bordercolor=0xC81423:x=(w-tw)/2:y=330,\
drawtext=fontfile=$F:text='LE COME-BACK':fontcolor=white:fontsize=70:box=1:boxcolor=0xC81423:boxborderw=18:x=(w-tw)/2:y=500,\
drawtext=fontfile=$F:text='$EP':fontcolor=white:fontsize=46:x=(w-tw)/2:y=1440,\
drawtext=fontfile=$F:text='Parodie satirique':fontcolor=0xDDDDDD:fontsize=34:x=(w-tw)/2:y=1510" \
-c:v libx264 -crf 21 -pix_fmt yuv420p -c:a copy "$OUTV"
