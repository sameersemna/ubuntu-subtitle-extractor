"""
join_short_captions.py

Utility to join short captions in an SRT file with the following caption.

Behavior:
- Reads an input .srt file and merges any caption whose duration is less than
  `min_duration` seconds with the next caption, extending the timing accordingly.
- After merging, validates timings to ensure there are no overlaps; if a start
  is before the previous end, it will be bumped forward.
- Writes two files next to the input: `<basename>_joined.srt` (full result) and
  `<basename>_joined_errors.srt` (blocks that were modified during processing).

Usage:
    python join_short_captions.py -i input.srt [-t 3]

Options:
- -i/--input: input SRT file path
- -t/--threshold: minimum caption duration in seconds (default: 3)

This is intentionally lightweight and compatible with the existing repository's
minimal SRT parsing approach (blocks separated by blank lines, timing on the
second line as "HH:MM:SS,mmm --> HH:MM:SS,mmm").
"""

from datetime import datetime, timedelta
import getopt
import os
import re
import sys


DEFAULT_THRESHOLD_SECONDS = 3.0


def parse_srt_blocks(srt_text):
    """Split raw SRT text into a list of blocks. Each block is a dict with:
    - index_line (may be the numeric index or another identifier)
    - start (datetime)
    - end (datetime)
    - text_lines (list of strings)

    Blocks with malformed timing lines will keep start/end as None.
    """
    blocks = []
    # Normalize newlines and split by blank line (SRT blocks separated by blank)
    groups = re.sub('\r\n', '\n', srt_text).split('\n\n')
    for grp in groups:
        if not grp.strip():
            continue
        lines = grp.split('\n')
        idx_line = lines[0]
        start = end = None
        text_lines = lines[2:]
        if len(lines) >= 2 and ' --> ' in lines[1]:
            parts = lines[1].split(' --> ')
            try:
                start = datetime.strptime(parts[0], "%H:%M:%S,%f")
                end = datetime.strptime(parts[1], "%H:%M:%S,%f")
            except Exception:
                start = end = None
        blocks.append({
            'index': idx_line,
            'start': start,
            'end': end,
            'text_lines': text_lines,
            'raw_timing': lines[1] if len(lines) >= 2 else ''
        })
    return blocks


def format_srt_block(block, out_index=None):
    """Format a single block dict back to SRT text (using CRLF separators).

    If start/end are None, uses the original raw_timing value.

    Parameters:
    - block: the block dict
    - out_index: optional int to use as the numeric index for the output
      (automatic renumbering). If None, the original block['index'] is used.
    """
    if out_index is None:
        index_line = block.get('index', '')
    else:
        index_line = str(out_index)
    if block.get('start') is None or block.get('end') is None:
        timing = block.get('raw_timing', '')
    else:
        timing = block['start'].strftime("%H:%M:%S,%f")[:12] + ' --> ' + block['end'].strftime("%H:%M:%S,%f")[:12]
    text = '\n'.join(block.get('text_lines', []))
    # Ensure there is an index line even if empty to preserve block shape
    return f"{index_line}\n{timing}\n{text}"


def join_short_blocks(blocks, threshold_seconds=DEFAULT_THRESHOLD_SECONDS, separator_mode='auto'):
    """Join blocks whose duration is less than threshold_seconds with the next
    block. Returns (joined_blocks, modified_blocks) where modified_blocks are
    those that were changed and should be written to the errors file for review.

    This function also updates timings conservatively (merging end time and
    concatenating text lines). It does not change numeric indices.
    """
    if not blocks:
        return [], []

    joined = []
    modified = []
    i = 0
    while i < len(blocks):
        current = blocks[i]
        # If timings missing, attempt to preserve raw block and move on
        if current['start'] is None or current['end'] is None:
            joined.append(current)
            i += 1
            continue

        duration = (current['end'] - current['start']).total_seconds()
        if duration < threshold_seconds and i + 1 < len(blocks):
            # Merge with next block
            nxt = blocks[i + 1]
            # If next block has no timings, we can't reliably merge timings;
            # concatenate text and preserve timings as-is
            if nxt['start'] is None or nxt['end'] is None:
                # Append text to next block's text_lines with separator rules:
                # separator_mode controls insertion:
                # - 'auto': insert a single blank only if both sides have text
                # - 'none': never insert a blank
                # - 'always': always insert one blank between parts
                combined = []
                if current['text_lines']:
                    combined.extend(current['text_lines'])
                add_sep = False
                if separator_mode == 'always':
                    add_sep = True
                elif separator_mode == 'auto' and current['text_lines'] and nxt['text_lines']:
                    add_sep = True
                # Only add a separator if requested and not already present
                if add_sep:
                    combined.append('')
                if nxt['text_lines']:
                    combined.extend(nxt['text_lines'])
                nxt['text_lines'] = combined
                modified.append(nxt)
                i += 1  # skip current; next will be processed in next loop
                # Drop current from output (it is absorbed into next)
            else:
                # New merged block uses current's index, start, and next's end
                # Merge text lines similarly but avoid inserting an extra
                # blank line when not needed.
                merged_text = []
                if current['text_lines']:
                    merged_text.extend(current['text_lines'])
                add_sep = False
                if separator_mode == 'always':
                    add_sep = True
                elif separator_mode == 'auto' and current['text_lines'] and nxt['text_lines']:
                    add_sep = True
                if add_sep:
                    merged_text.append('')
                if nxt['text_lines']:
                    merged_text.extend(nxt['text_lines'])
                merged = {
                    'index': current['index'],
                    'start': current['start'],
                    'end': nxt['end'],
                    'text_lines': merged_text,
                    'raw_timing': current.get('raw_timing', '')
                }
                joined.append(merged)
                modified.append(merged)
                i += 2  # consumed two blocks
        else:
            joined.append(current)
            i += 1
    return joined, modified


def validate_and_fix_timings(blocks):
    """Validate timings to ensure non-decreasing and fix overlaps by bumping
    starts forward to the previous end when needed. Returns (fixed_blocks,
    error_blocks) where error_blocks are those modified during this step.
    """
    prev_end = datetime.strptime("00:00:00,000", "%H:%M:%S,%f")
    error_blocks = []
    fixed = []
    for b in blocks:
        # If no timings, pass through
        if b['start'] is None or b['end'] is None:
            fixed.append(b)
            continue
        start = b['start']
        end = b['end']
        changed = False
        if start < prev_end:
            # bump start forward to prev_end
            start = prev_end
            changed = True
        # Ensure end is after start; if not, extend end to start + 1ms
        if end <= start:
            end = start + timedelta(milliseconds=1)
            changed = True
        b2 = dict(b)
        b2['start'] = start
        b2['end'] = end
        fixed.append(b2)
        if changed:
            error_blocks.append(b2)
        prev_end = end
    return fixed, error_blocks


def write_outputs(input_path, blocks, error_blocks):
    base = os.path.splitext(input_path)[0]
    out_full = base + '_joined.srt'
    out_err = base + '_joined_errors.srt'
    # Write full joined/validated output
    # Renumber captions sequentially for the full output
    with open(out_full, 'w') as f:
        formatted = []
        for idx, b in enumerate(blocks, start=1):
            formatted.append(format_srt_block(b, out_index=idx))
        f.write('\r\n\r\n'.join(formatted))
    # For the error file, also renumber so it's easy to read/reindex.
    with open(out_err, 'w') as f:
        formatted_err = []
        for idx, b in enumerate(error_blocks, start=1):
            formatted_err.append(format_srt_block(b, out_index=idx))
        f.write('\r\n\r\n'.join(formatted_err))
    print(f"Wrote: {out_full} (full) and {out_err} (errors)")


def main(argv):
    inputfile = None
    threshold = DEFAULT_THRESHOLD_SECONDS
    separator_mode = 'auto'
    try:
        options, args = getopt.getopt(argv, "hi:t:s:", ["input=", "threshold=", "separator="])
    except Exception:
        print('Usage: join_short_captions.py -i <input.srt> [-t <seconds>]')
        return
    for o, a in options:
        if o == '-h':
            print('Usage: join_short_captions.py -i <input.srt> [-t <seconds>]')
            return
        if o in ('-i', '--input'):
            inputfile = a
        if o in ('-t', '--threshold'):
            try:
                threshold = float(a)
            except Exception:
                threshold = DEFAULT_THRESHOLD_SECONDS
        if o in ('-s', '--separator'):
            if a.lower() in ('auto', 'none', 'always'):
                separator_mode = a.lower()
            else:
                print("Invalid separator value; expected: auto, none, or always. Using 'auto'.")
                separator_mode = 'auto'
    if not inputfile:
        print('Missing input file. Use -i <input.srt>')
        return
    with open(inputfile, 'r') as f:
        srt_text = f.read()
    blocks = parse_srt_blocks(srt_text)
    joined, modified_by_join = join_short_blocks(blocks, threshold_seconds=threshold, separator_mode=separator_mode)
    validated, modified_by_validate = validate_and_fix_timings(joined)
    # Combine modified lists for error output (unique by index + start+end)
    # For simplicity, just concatenate; duplicates are acceptable here.
    error_blocks = modified_by_join + modified_by_validate
    write_outputs(inputfile, validated, error_blocks)


if __name__ == '__main__':
    main(sys.argv[1:])
