import sys
import re
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, PageBreak, Spacer
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from bidi.algorithm import get_display
import arabic_reshaper

# Pattern for titles based on common Arabic terms (like your HTML code)
TITLE_PATTERN = re.compile(r'^(.*(?:الباب|الفصل|مقدمة|الخاتمة).*)$')

def decode_mojibake(text):
    return text.encode('latin1').decode('utf8')

def detect_titles(text_lines):
    title_list = []
    for i, line in enumerate(text_lines):
        if TITLE_PATTERN.match(line):
            title_list.append((i, line.strip()))
    return title_list

def render_pdf(text, filename, font_path):
    PAGE_WIDTH, PAGE_HEIGHT = A4
    margin = 50

    # Register Arabic font path
    pdfmetrics.registerFont(TTFont('Amiri', font_path))

    styles = getSampleStyleSheet()
    arabic_style = ParagraphStyle(
        'Arabic',
        parent=styles['Normal'],
        fontName='Amiri',
        fontSize=14,
        leading=18,
        rightIndent=50,
        alignment=2,
    )
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontName='Amiri',
        fontSize=26,
        leading=30,
        rightIndent=50,
        alignment=2,
        spaceBefore=20,
        spaceAfter=15,
        textColor='darkblue',
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontName='Amiri',
        fontSize=18,
        leading=22,
        rightIndent=50,
        alignment=2,
        spaceBefore=15,
        spaceAfter=10,
        textColor='darkred',
    )

    lines = text.split('\n')
    titles = detect_titles(lines)
    title_indices = {idx for idx, _ in titles}

    # Build TOC based on detected titles (similar to HTML TOC)
    toc = []
    for idx, title_text in titles:
        toc.append(title_text.strip())

    story = []

    # Add Table of Contents page
    reshaped = arabic_reshaper.reshape('فهرس المحتويات (Table of Contents)')
    bidi = get_display(reshaped)
    story.append(Paragraph(bidi, title_style))
    story.append(Spacer(1, 20))
    for toc_entry in toc:
        reshaped_entry = arabic_reshaper.reshape(toc_entry)
        bidi_entry = get_display(reshaped_entry)
        story.append(Paragraph(bidi_entry, subtitle_style))
        story.append(Spacer(1, 10))
    story.append(PageBreak())

    # Add rest of the content, formatting titles/subtitles distinctly
    paragraph_buffer = []
    for i, line in enumerate(lines):
        if line.strip() == '':
            continue
        reshaped_line = arabic_reshaper.reshape(line.strip())
        bidi_line = get_display(reshaped_line)
        if i in title_indices:
            # Title line
            p = Paragraph(bidi_line, title_style)
        else:
            p = Paragraph(bidi_line, arabic_style)
        story.append(p)
        story.append(Spacer(1, 6))

    # Custom canvas for page numbering
    class NumberedCanvas(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._saved_page_states = []

        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            num_pages = len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self.draw_page_number(self._pageNumber, num_pages)
                super().showPage()
            super().save()

        def draw_page_number(self, page_num, num_pages):
            text = f"{page_num} / {num_pages}"
            self.setFont("Amiri", 10)
            self.drawCentredString(PAGE_WIDTH / 2, 20, text)

    doc = SimpleDocTemplate(filename, pagesize=A4,
                            rightMargin=margin, leftMargin=margin,
                            topMargin=margin, bottomMargin=margin)

    doc.build(story, canvasmaker=NumberedCanvas)


def main():
    if len(sys.argv) < 2:
        print("Usage: python arabic_pdf_toc.py input.txt")
        sys.exit(1)

    input_file = sys.argv[1]
    font_path = '/home/sameer/Shared/Sync/Private/Work/Projects/video-subtitle-extractor/fonts/Amiri/Amiri-Regular.ttf'

    with open(input_file, 'r', encoding='latin1') as f:
        raw_text = f.read()

    decoded_text = decode_mojibake(raw_text)
    output_pdf = "output_toc_refined.pdf"
    render_pdf(decoded_text, output_pdf, font_path)
    print(f"PDF generated: {output_pdf}")

if __name__ == "__main__":
    main()
