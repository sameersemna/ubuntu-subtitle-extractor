import sys
import os
import requests
from ftfy import fix_text

def fix_mojibake_source(source, is_url, output_path):
    if is_url:
        # Fetch content from URL
        response = requests.get(source)
        raw_bytes = response.content
    else:
        # Read content from local file
        with open(source, "rb") as f:
            raw_bytes = f.read()

    # Decode raw bytes as latin1 for fix_text to handle
    intermediate = raw_bytes.decode('latin1', errors='replace')
    fixed_text = fix_text(intermediate)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(fixed_text)

def is_url(path_or_url):
    return path_or_url.startswith("http://") or path_or_url.startswith("https://")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python fix_arabic_mojibake.py <input_file_or_url> <output_file.txt>")
        sys.exit(1)

    source = sys.argv[1]
    output_file = sys.argv[2]
    use_url = is_url(source)

    fix_mojibake_source(source, use_url, output_file)
    print(f"File saved with fixes applied: {output_file}")
