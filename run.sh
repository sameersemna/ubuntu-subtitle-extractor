#!/bin/bash

[ -f "$HOME/.bash_export" ] && source "$HOME/.bash_export"

usrDir='/home/sameer'
projDir="$usrDir/Shared/Sync/Private/Work/Projects/video-subtitle-extractor"
workDir="$projDir/output"
backendDir="$projDir/backend"

video_path=$1
subtitle_res='1280x720'
subtitle_area=${2:-'10, 630, 10, 1270'} # ymin ymax xmin xmax
fileJson="$backendDir/run.json"

echo "{\"video_path\": \"$video_path\", \"subtitle_area\": \"$subtitle_area\"}" > $fileJson

# conda activate subtitles

python $backendDir/main.py

# conda deactivate
