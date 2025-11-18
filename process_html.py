import sys
import re
import html

def decode_mojibake(text):
    # Decode mojibake (UTF-8 bytes misread as Latin1)
    return text.encode('latin1').decode('utf8')

def find_titles(text_lines):
    headers = []
    # Titles often include words like 'الباب', 'الفصل', 'مقدمة', etc.
    title_pattern = re.compile(r'^(.*(?:الباب|الفصل|مقدمة|الخاتمة).*)$')
    for i, line in enumerate(text_lines):
        if title_pattern.match(line):
            headers.append((i, line.strip()))
    return headers

def extract_footnotes(text):
    # Simple extract of footnotes marked like: [1], (1), etc.
    footnotes = {}
    footnote_pattern = re.compile(r'(\[\d+\])')
    lines = text.split('\n')
    for i, line in enumerate(lines):
        matches = footnote_pattern.findall(line)
        for m in matches:
            # naive collection: footnote text after marker — this requires manual adjustment
            footnotes[m] = footnotes.get(m, []) + [line]
    return footnotes

def generate_html(text):
    lines = text.split('\n')
    html_lines = []
    toc = []
    page_num = 1
    lines_per_page = 40
    line_count = 0
    
    # Find titles for TOC and mark lines
    titles = find_titles(lines)
    title_set = set(i for i, t in titles)

    # HTML header and styling for RTL and Arabic font
    header_html = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<title>Arabic Document</title>
<style>
body {
    font-family: "Arial", "Tahoma", sans-serif;
    direction: rtl;
    margin: 20px;
    line-height: 1.6;
    font-size: 18px;
}
h1 { color: darkblue; }
h2 { color: darkred; }
hr.pagebreak {
  border: none;
  border-top: 1px dashed #888;
  margin: 30px 0;
}
footer {
    text-align: center;
    font-size: 12px;
    color: #555;
    margin-top: 30px;
}
.toc a {
    text-decoration: none;
    color: #0066cc;
}
</style>
</head>
<body>
<h1>فهرس المحتويات (Table of Contents)</h1>
<div class="toc">
<ul>
'''

    # Build TOC
    for i, title in titles:
        cleaned_title = html.escape(title)
        anchor = f"title_{i}"
        toc.append(f'<li><a href="#{anchor}">{cleaned_title}</a></li>')

    footer_html = '''
</ul>
</div>
<hr class="pagebreak">
<footer>Rendered Arabic document with page breaks and TOC</footer>
</body>
</html>
'''
    
    html_lines.append(header_html)
    html_lines.append('\n'.join(toc))
    html_lines.append('<hr class="pagebreak">')

    for idx, line in enumerate(lines):
        escaped_line = html.escape(line)

        if idx in title_set:
            # Treat title as h1 or h2 based on keywords
            if 'مقدمة' in escaped_line or 'خاتمة' in escaped_line:
                html_lines.append(f'<h2 id="title_{idx}">{escaped_line}</h2>')
            else:
                html_lines.append(f'<h1 id="title_{idx}">{escaped_line}</h1>')
            line_count += 1
        elif escaped_line.strip() == '':
            html_lines.append('<br>')
            line_count += 1
        else:
            html_lines.append(f'<p>{escaped_line}</p>')
            line_count += 1

        if line_count >= lines_per_page:
            html_lines.append(f'<hr class="pagebreak"><footer>صفحة {page_num}</footer>')
            page_num += 1
            line_count = 0

    html_lines.append(footer_html)
    return '\n'.join(html_lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python process_arabic.py input.txt")
        sys.exit(1)

    input_file = sys.argv[1]

    with open(input_file, 'r', encoding='latin1') as f:
        raw_text = f.read()

    decoded_text = decode_mojibake(raw_text)
    html_out = generate_html(decoded_text)

    output_file = 'output.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_out)

    print(f'Processed HTML saved to {output_file}')

if __name__ == "__main__":
    main()
