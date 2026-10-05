#!/bin/sh
# Version verticale 9:16 (Shorts / TikTok / Reels) : fond flouté + titre.
set -e
cd "$(dirname "$0")/.."
F=/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Black.ttf
ffmpeg -y -loglevel error -i output/guignols_comeback_ep1.mp4 -filter_complex "\
[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:2,eq=brightness=-0.25[bg];\
[0:v]scale=1080:-2[fg];\
[bg][fg]overlay=0:(H-h)/2,\
drawtext=fontfile=$F:text='LES GUIGNOLS':fontcolor=0xFFD728:fontsize=130:borderw=8:bordercolor=black:x=(w-tw)/2:y=360,\
drawtext=fontfile=$F:text='LE COME-BACK':fontcolor=white:fontsize=70:box=1:boxcolor=0xC81423:boxborderw=18:x=(w-tw)/2:y=530,\
drawtext=fontfile=$F:text='Ep. 1 - Mais qui a bien pu écrire ça ?':fontcolor=white:fontsize=44:x=(w-tw)/2:y=1420,\
drawtext=fontfile=$F:text='Parodie satirique':fontcolor=0xDDDDDD:fontsize=34:x=(w-tw)/2:y=1490" \
-c:v libx264 -crf 21 -pix_fmt yuv420p -c:a copy output/guignols_comeback_ep1_vertical.mp4
