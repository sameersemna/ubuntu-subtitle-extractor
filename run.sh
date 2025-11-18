#!/bin/bash

# bash -i /home/sameer/Shared/Sync/Private/Work/Projects/video-subtitle-extractor/run.sh en.mp4

[ -f "$HOME/.bash_export" ] && source "$HOME/.bash_export"

usrDir='/home/sameer'
projDir="$usrDir/Shared/Sync/Private/Work/Projects/video-subtitle-extractor"
workDir="$projDir/output"
backendDir="$projDir/backend"

video_path=$1
# subtitle_res='1280x720'
subtitle_res='1920x1080'
subtitle_area=${2:-'10, 630, 10, 1270'} # ymin ymax xmin xmax
lang_code=${3:-'en'}
fileJson="$backendDir/run.json"

source $projDir/common.sh

dimensions=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "$video_path")
if [ -z "$dimensions" ]; then
    echo "Could not retrieve dimensions for '$video_path'. Check file path or if it's a valid video."
    exit 1
fi
video_width="${dimensions%x*}"
video_height="${dimensions#*x}"
echo "Video Width: $video_width"
echo "Video Height: $video_height"
subtitle_width=$(echo "$subtitle_res" | cut -d'x' -f1)
subtitle_height=$(echo "$subtitle_res" | cut -d'x' -f2)
echo "Subtitle Width: $subtitle_width"
echo "Subtitle Height: $subtitle_height"

# Prepare settings.ini for subtitle extraction
# Replace "Language =" in settings.ini with the extracted language code
sed -i "s/^Language = .*/Language = $lang_code/" $projDir/settings.ini
echo "Updated settings.ini with Language = $lang_code"

# Call the function and capture its line-by-line output into an array
# `mapfile -t my_array` reads lines into the `my_array` array, removing trailing newlines.
# `< <(...)` is process substitution, feeding the function's output as a file to mapfile.
mapfile -t subtitle_area_array < <(split_and_trim_string "$subtitle_area")

subtitle_calculated_array=()
# for item in "${subtitle_area_array[@]}"; do
for index in "${!subtitle_area_array[@]}"; do
    item="${subtitle_area_array[$index]}" # Get the element at the current index

    if [[ "$index" -eq 0 ]] || [[ "$index" -eq 1 ]]; then
        item_calculated=$(echo "$item * $video_height / $subtitle_height" | bc)
    else
        item_calculated=$(echo "$item * $video_width / $subtitle_width" | bc)
    fi
    subtitle_calculated_array+=("$item_calculated")
done

subtitle_area_calculated=$(join_array_by_delimiter ", " "${subtitle_calculated_array[@]}")

echo "{\"video_path\": \"$video_path\", \"subtitle_area\": \"$subtitle_area_calculated\"}"
echo "{\"video_path\": \"$video_path\", \"subtitle_area\": \"$subtitle_area_calculated\"}" > $fileJson
# exit

# conda activate subtitles

python $backendDir/main.py

# conda deactivate
