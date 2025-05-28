#!/bin/bash

# bash ./VideoSubFinderCli.run  -h

fileVid='/home/sameer/Shared/Sync/Private/Work/Projects/videosubfinder-cli/Build/Docker/test_en.mp4'
fileSrt='/home/sameer/Shared/Sync/Private/Work/Projects/videosubfinder-cli/Build/Docker/test_en.srt'
dirResults='/home/sameer/Shared/Sync/Private/Work/Projects/videosubfinder-cli/Build/Docker/test_results'

# cmd="bash ./VideoSubFinderCli.run -c -r -ccti -i \"$fileVid\" -cscti \"$fileSrt\" -o \"$dirResults\" -te 0.5 -be 0.1 -le 0.1 -re 0.9 -s 0:00:10:300 -e 0:00:13:100"
# cmd="bash ./VideoSubFinderCli.run -c -r -i \"$fileVid\" -ces \"$fileSrt\" -o \"$dirResults\" -te 0.5 -be 0.1 -le 0.1 -re 0.9 -s 0:00:10:300 -e 0:00:13:100"
cmd="bash ./VideoSubFinderCli.run -c -r -i \"$fileVid\" -ces \"$fileSrt\" -o \"$dirResults\""
echo $cmd
eval $cmd

