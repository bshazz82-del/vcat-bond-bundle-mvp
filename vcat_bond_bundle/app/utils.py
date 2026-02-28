from __future__ import annotations
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter

def add_watermark(pdf_bytes: bytes, text: str = "PREVIEW – NOT FOR FILING") -> bytes:
    buffer = io.BytesIO()
    width, height = A4
    c = canvas.Canvas(buffer, pagesize=A4)
    c.saveState()
    c.setFont("Helvetica-Bold", 40)
    c.setFillColorRGB(0.6, 0.6, 0.6)
    c.setFillAlpha(0.2)
    c.translate(width / 2, height / 2)
    c.rotate(45)
    c.drawCentredString(0, 0, text)
    c.restoreState()
    c.showPage()
    c.save()
    buffer.seek(0)
    watermark_reader = PdfReader(buffer)
    watermark_page = watermark_reader.pages[0]

    original_reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()
    for page in original_reader.pages:
        page.merge_page(watermark_page)
        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()
