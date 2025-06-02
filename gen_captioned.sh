#!/bin/bash

# conda activate spleeter

[ -f "$HOME/.bash_export" ] && source "$HOME/.bash_export"

usrDir='/home/sameer'
projDir="$usrDir/Shared/Sync/Private/Work/Projects/video-subtitle-extractor"
workDir="$projDir/output"
backendDir="$projDir/backend"

cores_count=$(nproc --all)
threads_count=$((cores_count - 2))
ffmpeg="/usr/bin/ffmpeg -threads $threads_count"
echo "cores_count:$cores_count | threads_count:$threads_count | $ffmpeg"

video_path=$1
lang=${2:-'de'}

video_path_clean=${video_path/.mp4/.cln.mp4}
audio_path=${video_path/.mp4/.mp3}
out_srt=${video_path/.mp4/.srt}
lang_srt=${video_path/.mp4/.$lang.srt}
en_srt=${video_path/.mp4/.en.srt}

if [ -f $audio_path ]; then
    echo "Final File exists: $audio_path"
elif [ -f $video_path_clean ]; then
    echo "File exists: $video_path_clean"
else
    bash clean_vid_sound.sh "$video_path"
    sleep 2
fi

if [ -f $audio_path ]; then
    echo "File exists: $audio_path"
else
    $ffmpeg -i "$video_path_clean" "$audio_path" -n
    sleep 2
fi

echo '-------------------------------------------'
ffprobe "$video_path"
echo '-------------------------------------------'
echo '#1. Now run the following commands'
echo '-------------------------------------------'
cmd="conda activate captions"
echo $cmd
cmd="whisper \"$audio_path\" --language \"$lang\"  --task translate --fp16 False"
echo $cmd
echo '-------------------------------------------'
echo "#2. Get English translations"
echo '-------------------------------------------'
echo "cp \"$out_srt\" \"$lang_srt\"; cp \"$out_srt\" \"$en_srt\";"
echo "cat \"$lang_srt\" | xsel --clipboard --input"
# echo "cat \"$en_srt\" | pbcopy"
echo '-------------------------------------------'
echo "#3. Join both captions and burn"
echo '-------------------------------------------'
cmd="bash $projDir/join2srt.sh '$video_path'"
echo $cmd
echo '-------------------------------------------'

# alias pbcopy='xclip -selection clipboard -i'
# alias pbpaste='xclip -selection clipboard -o'

# alias pbcopy='xsel --clipboard --input'
# alias pbpaste='xsel --clipboard --output'
