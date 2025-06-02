#!/bin/bash

[ -f "$HOME/.bash_export" ] && source "$HOME/.bash_export"

usrDir='/home/sameer'
projDir="$usrDir/Shared/Sync/Private/Work/Projects/video-subtitle-extractor"
workDir="$projDir/output"
backendDir="$projDir/backend"
srt2ass="$usrDir/Shared/Sync/Private/Work/Projects/2srt2ass-cpp/2srt2ass++"

cores_count=$(nproc --all)
threads_count=$((cores_count - 2))
ffmpeg="/usr/bin/ffmpeg -threads $threads_count"
echo "cores_count:$cores_count | threads_count:$threads_count | $ffmpeg"

video_path=$1
lang_top=${2:-'en'}
lang_bottom=${2:-'de'}
limit=''
# limit='-to 60'

in_base=${video_path/.mp4/}
out_ass=${video_path/.mp4/.ass}

rm -f $out_ass

validate_srt() {
    file_srt=$1
    echo '**********************************************************'
    echo "Checking $file_srt"

    if [ ! -f $file_srt ]; then
        echo "Missing file: $file_srt"
        exit
    fi

    ffmpeg -i $file_srt $file_srt.test.srt -y

    echo '//////////////////////////////////////////////////////////'

    python $projDir/srtfix.py -i "$file_srt"
}

validate_srt "$in_base.$lang_top.srt"
validate_srt "$in_base.$lang_bottom.srt"
rm -f *.test.srt
# exit

echo "--- Merging SRTs to ASS..."
$srt2ass --top "$in_base.$lang_top.srt" --bottom "$in_base.$lang_bottom.srt" --output "$out_ass"
sleep 2

if [ ! -f $out_ass ]; then
    echo "XXX Failed to generate: $out_ass"
    exit
fi

echo "--- Replacing styles..."
# Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
# Style: Top,Arial,12,&H00F9FFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,0,8,10,10,10,0
# Style: Bot,Arial,12,&H00F9FFF9,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,0,2,10,10,10,0

sed -i 's#Style: Top,Arial,16,&H00F9FFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,0,8,10,10,10,0#Style: Top,Ubuntu,11,\&H30FFFFFF,\&H0088FFFF,\&HFF000000,\&H33000000,-1,0,0,0,100,100,0,0,4,0,5,8,10,10,10,0#' "$out_ass"
sleep 2
sed -i 's#Style: Bot,Arial,16,&H00F9FFF9,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,0,2,10,10,10,0#Style: Bot,Ubuntu,13,\&H05F9F9F9,\&H00FFFFFF,\&HFF000000,\&H22000000,-1,0,0,0,100,100,0,0,4,0,5,2,10,10,10,0#' "$out_ass"
sleep 2

if [ ! -f "./play.mp4" ]; then
    $ffmpeg -i "$video_path" -vf "eq=brightness=-0.5:gamma=0.7" $limit ./play.mp4
    sleep 2
fi
if [ ! -f "./play_captioned.mp4" ]; then
    cp $out_ass ./play.ass
    sleep 2
    $ffmpeg -i ./play.mp4 -vf "ass=./play.ass" $limit ./play_captioned.mp4
    sleep 2
    rm -f ./play.ass
fi

echo "=== DONE ==="