#!/bin/bash

# dimensionsDefault='100, 980, 150, 1760'
dimensionsDefault='100,880,20,1900'
dimensionsDefault='20,1060,20,1900'
dimensions=${1:-$dimensionsDefault}

# --- Configuration ---
# Specify the path to your file containing the YouTube links
LINKS_FILE="list_subs.csv"
DONE_FILE="done_subs.csv"

# --- Script Logic ---

# Check if the links file exists
if [ ! -f "$LINKS_FILE" ]; then
  echo "Error: Links file not found at '$LINKS_FILE'"
  exit 1
fi

echo "Starting to process links from $LINKS_FILE..."
echo "---"

# Read the file line by line
# IFS= : Prevents 'read' from trimming leading/trailing whitespace
# -r   : Prevents 'read' from interpreting backslashes as escape sequences
# < "$LINKS_FILE" : Redirects the file's content into the 'while' loop
while IFS= read -r line || [[ -n "$line" ]]; do  
    # Skip empty lines or lines that are comments (start with #)
    if [ -z "$line" ] || [[ "$line" == \#* ]]; then
        continue
    fi
    echo "Found line: $line"
    # Line is CSV with URL and language code
    IFS=',' read -r url lang_code <<< "$line"
    echo "Processing URL: $url with language code: $lang_code"

    # Download youtube video in folder named after video id in MP4 format
    video_id=$(echo "$url" | grep -oP '(?<=v=)[^&]+')
    echo "Video ID extracted: $video_id"
    dir_name="./down/${video_id}"

    # Check if this link has already been processed
    if grep -q ",$video_id," "$DONE_FILE" 2>/dev/null; then
        echo "This link has already been processed. Skipping..."
        echo "---"
        continue
    fi

    if [ ! -f "$dir_name/org.mp4" ]; then
        echo "Directory $dir_name does not contain org.mp4"
        mkdir -p "$dir_name"
        yt-dlp "$url" -f mp4 -o "$dir_name/org.%(ext)s" # Download original video in best MP4 format
        sleep 2
    else
        echo "Directory $dir_name already contains org.mp4, skipping download."
    fi

    # get full path to org.mp4
    org_mp4_path=$(realpath "$dir_name/org.mp4")

    if [ ! -f "$org_mp4_path" ]; then
        echo "Error: Downloaded video file not found at '$org_mp4_path'"
        exit 1
    fi

    cmd="bash run.sh '$org_mp4_path' '$dimensions' '$lang_code'"  
    echo $cmd
    # eval $cmd
    bash run.sh "$org_mp4_path" "$dimensions" "$lang_code"

    # Mark this link as done by appending to DONE_FILE with current datetime
    echo "$(date),$video_id,$url,$lang_code" >> "$DONE_FILE"
    
    # --- End of Processing Logic ---
    echo "--- Sleeping for 60 seconds before processing the next link ---"
    sleep 60

done < "$LINKS_FILE"

echo "---"
echo "Finished processing all links."