#!/bin/bash

cores_count=$(nproc --all)
threads_count=$((cores_count - 2))
ffmpeg="/usr/bin/ffmpeg -threads $threads_count"
echo "cores_count:$cores_count | threads_count:$threads_count | $ffmpeg"

# IMPORTANT: This function relies on Bash's extended globbing for efficient trimming.
# Make sure to enable it before calling the function if it's not already enabled in your script.
# `shopt -s extglob` enables it, `shopt -u extglob` disables it.
# It's set globally at the top of this script for demonstration.

# split_and_trim_string: Splits a string by comma and trims whitespace from each element.
# Arguments:
#   $1 - The input string (e.g., " item1 , item2 , item3 ")
# Output:
#   Each trimmed element is printed on a new line.
# Example usage:
#   mapfile -t my_array < <(split_and_trim_string "one , two , three ")
#   echo "${my_array[0]}" # Output: one
split_and_trim_string() {
  local input_str="$1"
  local OLD_IFS="$IFS" # Save current IFS
  IFS=','             # Set comma as the delimiter for splitting

  # Read the string into a temporary array
  # -r prevents backslash escapes from being interpreted
  # -a creates an indexed array
  # <<< "$input_str" is a "here string" that feeds the variable content to read
  read -r -a raw_elements <<< "$input_str"

  IFS="$OLD_IFS" # Restore original IFS

  local trimmed_item
  # Loop through each element in the temporary array
  for item in "${raw_elements[@]}"; do
    # Trim leading whitespace using parameter expansion:
    # `##+([[:space:]])` removes the longest match of one or more whitespace characters from the beginning
    trimmed_item="${item##+([[:space:]])}"

    # Trim trailing whitespace using parameter expansion:
    # `%%+([[:space:]])` removes the longest match of one or more whitespace characters from the end
    trimmed_item="${trimmed_item%%+([[:space:]])}"

    # Print the trimmed item. Each item on a new line makes it easy for mapfile to capture.
    echo "$trimmed_item"
  done
}

# join_array_by_delimiter: Joins elements of an array into a single string using a specified delimiter.
#
# Arguments:
#   $1 - The delimiter string (e.g., ",", " - ", "::")
#   $@ - The array elements to join (passed as separate arguments)
#
# Returns:
#   Prints the joined string to standard output.
#
# Example Usage:
#   my_array=("apple" "banana with space" "orange")
#   joined_string=$(join_array_by_delimiter ", " "${my_array[@]}")
#   echo "$joined_string" # Output: apple, banana with space, orange
#
#   joined_string=$(join_array_by_delimiter "::" "one" "two" "three four")
#   echo "$joined_string" # Output: one::two::three four
join_array_by_delimiter() {
  local delimiter="$1" # Store the first argument as the delimiter
  shift              # Remove the first argument (delimiter) from the positional parameters

  # Save the current IFS value
  local OLD_IFS="$IFS"

  # Set IFS to the desired delimiter for this function's scope
  # This makes "${@}" (or "${*}") expand with the new delimiter
  IFS="$delimiter"

  # Print the joined elements.
  # "${*}" expands all positional parameters into a single word,
  # separated by the first character of IFS (or by IFS if it's multi-character
  # and used within double quotes in Bash 4.4+).
  # Using "${@}" would expand each element as a separate word, which is not what we want for joining.
  echo "$*"

  # Restore the original IFS value
  IFS="$OLD_IFS"
}