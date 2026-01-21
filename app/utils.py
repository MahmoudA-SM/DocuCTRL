import io
import os
import segno
import arabic_reshaper
from bidi.algorithm import get_display

from pypdf import PdfReader, PdfWriter, Transformation
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def fix_arabic(text: str) -> str:

    if not text:
        return ""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def create_qr_buffer(data: str) -> io.BytesIO:

    qr = segno.make(data)
    out = io.BytesIO()
    qr.save(out, kind="png", scale=6)
    out.seek(0)
    return out


def generate_serial(owner_code: str, year: int, seq_id: int) -> str:

    return f"{owner_code}-{year}-{seq_id:04d}"


def _register_arabic_font() -> str:

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    font_path = os.path.join(base_dir, "assets", "Amiri-Regular.ttf")
    font_name = "Amiri"

    if os.path.exists(font_path):

        try:
            pdfmetrics.getFont(font_name)
        except KeyError:
            pdfmetrics.registerFont(TTFont(font_name, font_path))
        return font_name

    return "Helvetica"

STAMP_PADDING = 24  # points (~0.33 inch)
STAMP_QR_SIZE = 90  # points
STAMP_LINE_GAP = 12
STAMP_FONT_SIZE = 10
STAMP_TEXT_LINES = 3
STAMP_TEXT_GAP = 10
STAMP_HEADER_HEIGHT = (
    STAMP_PADDING
    + STAMP_QR_SIZE
    + STAMP_TEXT_GAP
    + (STAMP_TEXT_LINES - 1) * STAMP_LINE_GAP
    + STAMP_FONT_SIZE
    + STAMP_PADDING
)


def _make_watermark_pdf(
    page_width: float,
    page_height: float,
    serial: str,
    project_name: str,
    owner_company_name: str,
    qr_png: io.BytesIO,
) -> io.BytesIO:

    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(page_width, page_height))


    padding = STAMP_PADDING
    qr_size = STAMP_QR_SIZE
    line_gap = STAMP_LINE_GAP
    font_size = STAMP_FONT_SIZE


    stamp_right = page_width - padding
    stamp_top = page_height - padding


    qr_x = stamp_right - qr_size
    qr_y = stamp_top - qr_size


    from reportlab.lib.utils import ImageReader
    qr_image = ImageReader(qr_png)
    c.drawImage(qr_image, qr_x, qr_y, width=qr_size, height=qr_size, mask="auto")


    text_right = stamp_right
    text_y = qr_y - STAMP_TEXT_GAP


    font_name = _register_arabic_font()
    serial_line = fix_arabic(f"\u0627\u0644\u0631\u0642\u0645 \u0627\u0644\u062a\u0633\u0644\u0633\u0644\u064a: {serial}")
    owner_line = fix_arabic(f"\u0627\u0644\u062c\u0647\u0629 \u0627\u0644\u0645\u0627\u0644\u0643\u0629: {owner_company_name}")
    project_line = fix_arabic(f"\u0627\u0633\u0645 \u0627\u0644\u0645\u0634\u0631\u0648\u0639: {project_name}")

    c.setFont(font_name, font_size)

    c.drawRightString(text_right, text_y, serial_line)
    text_y -= line_gap
    c.drawRightString(text_right, text_y, owner_line)
    text_y -= line_gap
    c.drawRightString(text_right, text_y, project_line)

    c.save()
    packet.seek(0)
    return packet

def stamp_pdf(
    input_pdf_path: str,
    output_pdf_path: str,
    serial: str,
    project_name: str,
    owner_company_name: str,
) -> None:

    reader = PdfReader(input_pdf_path)
    if not reader.pages:
        raise ValueError("Input PDF has no pages")

    first_page = reader.pages[0]
    page_width = float(first_page.mediabox.width)
    page_height = float(first_page.mediabox.height)
    header_height = STAMP_HEADER_HEIGHT

    qr_png = create_qr_buffer(serial)
    watermark_stream = _make_watermark_pdf(
        page_width,
        page_height + header_height,
        serial,
        project_name,
        owner_company_name,
        qr_png,
    )

    watermark_reader = PdfReader(watermark_stream)
    watermark_page = watermark_reader.pages[0]

    writer = PdfWriter()

    for idx, page in enumerate(reader.pages):
        if idx == 0:
            new_page = writer.add_blank_page(
                width=page_width,
                height=page_height + header_height,
            )
            new_page.merge_page(page)
            new_page.merge_page(watermark_page)
        else:
            writer.add_page(page)

    with open(output_pdf_path, "wb") as f:
        writer.write(f)
