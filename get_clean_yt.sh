#!/bin/bash

# Script takes a youtube id, generates related video file and generates a captioned video using whisper, in english and one given language

# bash -i /home/sameer/Shared/Sync/Private/Work/Projects/video-subtitle-extractor/get_clean_yt.sh 4b8U7lT7l-M 1
# bash -i /home/sameer/Shared/Sync/Private/Work/Projects/video-subtitle-extractor/get_clean_yt.sh kxC5NDNNd0I 1 'de'

# [ -f "$HOME/.bashrc" ] && source "$HOME/.bashrc"
# [ -f "$HOME/.bash_export" ] && source "$HOME/.bash_export"

url=$1
processCaptions=${2:-0}
lang=${3:-de}

# -o "%(title)s-%(id)s.%(ext)s"
youtubedl="yt-dlp -S ext:mp4:m4a -o %(id)s"
youtubedl="$youtubedl --cookies-from-browser firefox"

echo 'Default yt-dlp:'
which yt-dlp

usrDir='/home/sameer'
projDir="$usrDir/Shared/Sync/Private/Work/Projects/video-subtitle-extractor"

find . -type f -name "._*" -delete

echo "############### 1. Download from youtube ###############"
conda activate youtube
echo 'Conda yt-dlp:'
which yt-dlp

# $youtubedl --skip-download --print video:channel_id $url
channel=$( $youtubedl --skip-download --print video:channel $url )
vidId=$( $youtubedl --skip-download --print video:id $url )
vidTitle=$( $youtubedl --skip-download --print video:title $url )

echo "=== PROCESSING: [$vidId] $vidTitle from $channel ==="
vidFile="$vidId.mp4"
audFile="$vidId.mp3"
clnFile="$vidId.cln.mp4"

dirName="$vidTitle [$vidId]"
dirName=${dirName// /_}
echo "Creating directory: $dirName"
mkdir -p $dirName

if [ -f $vidFile ]; then
    echo "File exists already: $vidFile"
else
    $youtubedl --list-formats $url
    echo "$youtubedl $url"
    $youtubedl $url
    sleep 2
fi
    
conda deactivate

echo "############### 2. Clean with spleeter ###############"
if [ -f $clnFile ]; then
    echo "File exists already: $clnFile"
# elif [ -f $audFile ]; then
#     echo "File exists already: $audFile"
else
    conda activate spleeter
    which spleeter
    bash $projDir/gen_captioned.sh "$vidFile"
    conda deactivate
fi

echo "=== DONE: [$vidId] $vidTitle from $channel ==="

if [ "$processCaptions" == "0" ]; then
    exit
fi

srtFile="$vidId.srt"
lang_srt=${srtFile/.srt/.$lang.srt}
en_srt=${srtFile/.srt/.en.srt}

echo "############### 3. Generate captions with whisper ###############"
if [ -f $srtFile ]; then
    echo "File exists already: $srtFile"
elif [ ! -f $audFile ]; then
    echo "File missing: $audFile"
else
    conda activate captions
    which whisper
    whisper "$audFile" --language "$lang" --task translate --fp16 False
    conda deactivate
fi

echo "############### 4. Generate captioned video with FFMPEG ###############"
if [ -f $en_srt ]; then
    if [ ! -s $en_srt ]; then
        echo "File exists, but is empty: $en_srt"
        echo "((( Give me the translations )))"
        echo "cat \"$lang_srt\" | xsel --clipboard --input"
        exit
    fi
    echo "File exists already: $en_srt"
    cmd="bash $projDir/join2srt.sh '$vidFile'"
    echo $cmd
else
    echo "File does not exist: $en_srt"
    touch "$en_srt"
    bash $projDir/replace.sh "$srtFile" "$lang_srt"
    echo "((( Give me the translations )))"
    echo "cat \"$lang_srt\" | xsel --clipboard --input"
fi

echo "=== COMPLETED: [$vidId] $vidTitle from $channel ==="
