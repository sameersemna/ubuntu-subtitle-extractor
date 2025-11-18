import sys
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Frame, SimpleDocTemplate
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from bidi.algorithm import get_display
import arabic_reshaper

def decode_mojibake(text):
    return text.encode('latin1').decode('utf8')

def render_pdf(text, filename, font_path):
    PAGE_WIDTH, PAGE_HEIGHT = A4

    # Register the Arabic font
    pdfmetrics.registerFont(TTFont('Amiri', font_path))

    styles = getSampleStyleSheet()
    arabic_style = ParagraphStyle(
        'Arabic',
        parent=styles['Normal'],
        fontName='Amiri',    # Use registered Arabic font here
        fontSize=14,
        leading=18,
        rightIndent=50,
        alignment=2,  # right aligned
    )

    margin = 50
    frame_width = PAGE_WIDTH - 2 * margin
    frame_height = PAGE_HEIGHT - 2 * margin

    paragraphs = text.split('\n\n')  # split on double new lines

    story = []
    for para in paragraphs:
        if para.strip():
            reshaped_text = arabic_reshaper.reshape(para.strip())
            bidi_text = get_display(reshaped_text)
            p = Paragraph(bidi_text, arabic_style)
            story.append(p)
            story.append(Paragraph("<br/><br/>", arabic_style))  # add space between paragraphs

    # Custom canvas to add page numbers at bottom center
    class NumberedCanvas(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            canvas.Canvas.__init__(self, *args, **kwargs)
            self.pages = []

        def showPage(self):
            self.pages.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            page_count = len(self.pages)
            for page_num, page in enumerate(self.pages, start=1):
                self.__dict__.update(page)
                self.draw_page_number(page_num, page_count)
                canvas.Canvas.showPage(self)
            canvas.Canvas.save(self)

        def draw_page_number(self, page_num, page_count):
            page_number_text = f"{page_num} / {page_count}"
            self.setFont("Amiri", 10)
            self.drawCentredString(PAGE_WIDTH / 2, 20, page_number_text)

    doc = SimpleDocTemplate(filename, pagesize=A4,
                            rightMargin=margin, leftMargin=margin,
                            topMargin=margin, bottomMargin=margin)

    doc.build(story, canvasmaker=NumberedCanvas)


def main():
    if len(sys.argv) < 2:
        print("Usage: python arabic_to_pdf_wrapped.py input.txt")
        return
    input_file = sys.argv[1]
    font_path = '/home/sameer/Shared/Sync/Private/Work/Projects/video-subtitle-extractor/fonts/Amiri/Amiri-Regular.ttf'

    with open(input_file, 'r', encoding='latin1') as f:
        raw_text = f.read()

    text = decode_mojibake(raw_text)
    output_pdf = "output_wrapped_with_font.pdf"
    render_pdf(text, output_pdf, font_path)
    print(f"PDF generated: {output_pdf}")

if __name__ == "__main__":
    main()
