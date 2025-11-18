#!/bin/bash

usrDir='/home/sameer'
projDir="$usrDir/Shared/Sync/Private/Work/Projects/video-subtitle-extractor"

CSV="$projDir/replace.csv"
INPUT=$1
OUTPUT=$2

# Build sed expression dynamically
sed_expr=""
while IFS=, read -r find replace; do
  # Escape slashes and build word-boundary replacement
  escaped_find=$(printf '%s\n' "$find" | sed 's/[^^]/[&]/g; s/\^/\\^/g')
  sed_expr+="s/\\b$find\\b/$replace/g;"
done < "$CSV"

# Apply all replacements and write to output file
sed "$sed_expr" "$INPUT" > "$OUTPUT"
