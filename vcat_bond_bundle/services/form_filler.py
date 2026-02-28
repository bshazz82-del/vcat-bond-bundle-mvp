from __future__ import annotations
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from ..models import Case

def generate_form_419a(case: Case) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 20 * mm

    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, height - margin, "VCAT Residential Tenancies – Application under s 419A")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, height - 40 * mm, "Applicant (Renter) Details:")
    c.setFont("Helvetica", 10)
    c.drawString(margin, height - 45 * mm, f"Session ID: {case.session.session_uuid}")
    if case.property_address:
        c.drawString(margin, height - 50 * mm, f"Property Address: {case.property_address}")
    if case.bond_amount:
        c.drawString(margin, height - 55 * mm, f"Bond Amount: {case.bond_amount}")
    if case.tenancy_end_date:
        c.drawString(margin, height - 60 * mm, f"Tenancy End Date: {case.tenancy_end_date.strftime('%Y-%m-%d')}")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, height - 75 * mm, "Orders Sought:")
    c.setFont("Helvetica", 10)
    orders_text = case.orders_sought or "Repayment of the full bond to the applicant."
    text_obj = c.beginText(margin, height - 80 * mm)
    text_obj.textLines(orders_text)
    c.drawText(text_obj)

    if case.narrative:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, height - 105 * mm, "Statement of Facts:")
        c.setFont("Helvetica", 10)
        text_obj = c.beginText(margin, height - 110 * mm)
        text_obj.textLines(case.narrative)
        c.drawText(text_obj)

    c.setFont("Helvetica", 8)
    c.drawString(margin, margin, f"Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    c.drawString(margin, margin - 10, "This document is not legal advice.")
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()
