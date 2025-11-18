# -*- coding: utf-8 -*-
"""
srtfix.py
------------
Small utility to scan and (lightly) fix common issues in SubRip (.srt) files.

Behavior:
- Reads an input .srt file and attempts to correct simple timing problems where
  a caption's start time is earlier than the previous caption's end time.
- Writes two output files alongside the input: one with the full (possibly
  corrected) captions and one containing only caption blocks that were changed
  (errors). Filenames are created by appending "_fixed.srt" and "_error.srt"
  to the input basename.

Notes / limitations:
- This tool performs minimal parsing and expects a basic SRT block format:
  index line, timing line ("HH:MM:SS,mmm --> HH:MM:SS,mmm"), and one or more
  text lines. Blocks are separated by a blank line. It tries to be tolerant
  but isn't a full SRT parser.
"""

from datetime import datetime
import getopt
import re
import sys

# Global counter for number of corrections made. Kept simple for reporting.
count = 0


def fix_srt(inputfile):
  """Read an SRT file, attempt to fix issues, and write two output files.

  Inputs:
  - inputfile: path to the .srt file to process

  Outputs (side-effects):
  - Writes <basename>_fixed.srt containing all captions (some possibly
    corrected).
  - Writes <basename>_error.srt containing only the caption blocks that were
    detected and modified (useful for review).

  The function does not return a value; it uses the module-level `count` to
  report how many corrections were detected.
  """
  global count
  parsed_file, errors_file = '', ''
  try:
    # Read the whole file into memory (SRT files are usually small).
    with open(inputfile, 'r') as f:
      srt_file = f.read()
      parsed_file, errors_file = parse_srt(srt_file)
  except Exception:
    # Silently ignore read/parse errors to match original behaviour.
    # In a more robust tool we'd surface the exception to the caller.
    pass
  finally:
    # Build output filenames by removing the input extension and appending
    # suffixes. This mirrors the original implementation.
    outputfile1 = ''.join(inputfile.split('.')[:-1]) + '_fixed.srt'
    outputfile2 = ''.join(inputfile.split('.')[:-1]) + '_error.srt'
    with open(outputfile1, 'w') as f:
      f.write(parsed_file)
    with open(outputfile2, 'w') as f:
      f.write(errors_file)
    print('Detected %s errors in "%s". Fixed file saved as "%s" (Errors only as "%s").' % (count, inputfile, outputfile1, outputfile2))


# Keep track of the previous caption's end time so we can detect overlaps
# (a caption that starts before the previous one ends). Initialized to zero.
previous_end_time = datetime.strptime("00:00:00,000", "%H:%M:%S,%f")


def parse_times(times):
  """Normalize and validate a pair of SRT timestamps.

  Inputs:
  - times: a two-element list/tuple of strings: [start_time, end_time], where
    each time string follows the SRT format "%H:%M:%S,%f" (milliseconds).

  Returns:
  - [corrected_times, error_flag]
    - corrected_times: list of two formatted time strings (start, end)
    - error_flag: boolean indicating whether a correction was made

  Side-effects:
  - May increment the module-level `count` when a correction is applied.
  - Updates module-level `previous_end_time` to the end time parsed here.

  Behavior detail:
  - If a caption's start time is earlier than `previous_end_time`, the start
    is bumped forward to `previous_end_time` and an error is recorded. This
    avoids overlapping captions.
  """
  global previous_end_time
  global count
  _error = False
  _times = []

  # Parse each time string into a datetime for easy comparison.
  for time_code in times:
    t = datetime.strptime(time_code, "%H:%M:%S,%f")
    _times.append(t)

  # If start time is before the previous block's end time, adjust it to the
  # previous end time to prevent overlaps. This is the primary "fix" this
  # script performs.
  if _times[0] < previous_end_time:
    _times[0] = previous_end_time
    count += 1
    _error = True

  # Update previous_end_time so the next caption can be validated against it.
  previous_end_time = _times[1]

  # Convert times back to the SRT format strings (trim extra microseconds to
  # keep the original millisecond precision). The slice [:12] keeps
  # "HH:MM:SS,mmm" (12 characters including commas).
  _times[0] = _times[0].strftime("%H:%M:%S,%f")[:12]
  _times[1] = _times[1].strftime("%H:%M:%S,%f")[:12]

  return [_times, _error]


def parse_srt(srt_file):
  """Parse SRT content and attempt to correct timing issues.

  This function does a light-weight split on caption blocks separated by a
  blank line and inspects each block's timing line. It returns two strings:
  - The full (possibly corrected) SRT content using CRLF separators.
  - A second SRT-like string containing only the caption blocks that were
    modified (errors), again using CRLF separators.
  """
  global count
  parsed_srt = []
  parsed_err = []

  # Precompute a small structure of all captions so we can look ahead/behind
  # when a timing line is malformed.
  all_captions = []
  # Normalize CRLF to LF first, then split by blank lines into blocks.
  all_lines = re.sub('\r\n', '\n', srt_file).split('\n\n')
  for idx, srt_group in enumerate(all_lines):
    lines = srt_group.split('\n')
    if len(lines) >= 3:
      times = lines[1].split(' --> ')
    # Store a minimal representation for lookups later. The text is not used
    # during this initial pass but keeping the shape makes the later logic
    # easier to follow.
    all_captions.append({
      "times": times,
      "text": ""
    })
#   print(all_captions)
  for idx, srt_group in enumerate(all_lines):
    # Split the block into lines: [index, timing, ...text]
    lines = srt_group.split('\n')
    if len(lines) >= 3:
      times = lines[1].split(' --> ')

    # If timing line doesn't contain both start and end, attempt to infer
    # missing pieces from neighboring caption blocks.
    if len(times) < 2:
      # Informative prints retained from original script to help debug
      # problematic SRTs when running interactively.
      print(f"XXX Times length Error at: {lines}")
      print(f"XXX at times: {times}")
      error = True
      count += 1
      try:
        border_time_before = all_captions[idx - 1]['times'][1]
      except Exception:
        border_time_before = ''
      try:
        border_time_after = all_captions[idx + 1]['times'][0]
      except Exception:
        border_time_after = ''
      border_times = [border_time_before, border_time_after]
      # Fill in missing start/end using nearby captions when available.
      correct_times = [
        times[0] if len(times) > 0 else border_time_before,
        times[1] if len(times) > 1 else border_time_after
      ]
    else:
        [correct_times, error] = parse_times(times)

    # If an error (correction) occurred, build a cleaned caption block and add
    # it to the errors list so the user can review only the changed entries.
    if error:
      print(f"XXX Error ({count}) at: {times}")
      print(f"XXX Corrected: {correct_times}")
      # Trim whitespace from each text line when saving the corrected block.
      clean_text = map(lambda x: x.strip(' '), lines[2:])
      srt_group = lines[0].strip(' ') + '\n' + ' --> '.join(correct_times) + '\n' + '\n'.join(clean_text)
      parsed_err.append(srt_group)

    # Regardless of whether we changed the block or not, include the (original
    # or modified) block in the full parsed output.
    parsed_srt.append(srt_group)
#   print(parsed_srt)
#   print(parsed_err)
  return '\r\n\r\n'.join(parsed_srt), '\r\n\r\n'.join(parsed_err)


def main(argv):
  """Simple CLI wrapper to read -i/--input and call fix_srt.

  The function preserves the original lightweight getopt-based parsing.
  """
  inputfile = None
  try:
    options, arguments = getopt.getopt(argv, "hi:", ["input="])
  except Exception:
    print('Usage: test.py -i <input file>')

  for o, a in options:
    if o == '-h':
      print('Usage: test.py -i <input file>')
      sys.exit()
    elif o in ['-i', '--input']:
      inputfile = a
  fix_srt(inputfile)


if __name__ == '__main__':
  main(sys.argv[1:])
