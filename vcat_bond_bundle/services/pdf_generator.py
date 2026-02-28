from __future__ import annotations
import io
from datetime import datetime
from typing import Iterable, List
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from ..models import Case, EvidenceFile

def generate_supporting_statement(case: Case, chronology: List[str]) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 20 * mm

    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, height - margin, "Supporting Statement")
    c.setFont("Helvetica", 10)
    y = height - 40 * mm
    for entry in chronology:
        if y < 40 * mm:
            c.showPage()
            y = height - 30 * mm
            c.setFont("Helvetica", 10)
        c.drawString(margin, y, f"- {entry}")
        y -= 7 * mm

    c.setFont("Helvetica", 8)
    c.drawString(margin, margin, f"Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()

def generate_orders_sought(case: Case) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    margin = 20 * mm
    height = A4[1]
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, height - margin, "Orders Sought")
    c.setFont("Helvetica", 10)
    text = case.orders_sought or "Repayment of the full bond to the applicant."
    text_obj = c.beginText(margin, height - 40 * mm)
    text_obj.textLines(text)
    c.drawText(text_obj)
    c.setFont("Helvetica", 8)
    c.drawString(margin, margin, f"Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()

def generate_evidence_index(evidence_files: Iterable[EvidenceFile]) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 20 * mm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, height - margin, "Evidence Index")
    c.setFont("Helvetica", 10)
    y = height - 40 * mm
    for idx, ev in enumerate(evidence_files, start=1):
        if y < 40 * mm:
            c.showPage()
            y = height - 30 * mm
            c.setFont("Helvetica", 10)
        c.drawString(margin, y, f"Exhibit {chr(ord('A') + idx - 1)}: {ev.filename} (pages: {ev.pages or '?'})")
        y -= 7 * mm
    c.setFont("Helvetica", 8)
    c.drawString(margin, margin, f"Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()

def generate_hearing_script(case: Case, chronology: List[str]) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 20 * mm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, height - margin, "Hearing Script")
    c.setFont("Helvetica", 10)
    y = height - 40 * mm
    c.drawString(margin, y, "Opening Remarks:")
    y -= 7 * mm
    c.setFont("Helvetica", 9)
    c.drawString(margin, y, "- Introduce yourself and state that you are seeking repayment of the bond.")
    y -= 10 * mm
    c.setFont("Helvetica", 10)
    c.drawString(margin, y, "Chronology of Events:")
    y -= 7 * mm
    c.setFont("Helvetica", 9)
    for entry in chronology:
        if y < 40 * mm:
            c.showPage()
            y = height - 30 * mm
            c.setFont("Helvetica", 9)
        c.drawString(margin, y, f"- {entry}")
        y -= 7 * mm
    if y < 60 * mm:
        c.showPage()
        y = height - 30 * mm
    c.setFont("Helvetica", 10)
    c.drawString(margin, y, "Closing:")
    y -= 7 * mm
    c.setFont("Helvetica", 9)
    c.drawString(margin, y, "- Thank the tribunal and restate your request for the bond to be repaid.")
    c.setFont("Helvetica", 8)
    c.drawString(margin, 20 * mm, f"Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()

def generate_checklist(case: Case) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    margin = 20 * mm
    height = A4[1]
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, height - margin, "Filing and Service Checklist")
    c.setFont("Helvetica", 10)
    y = height - 40 * mm
    checklist = [
        "Print and sign the Form 419A",
        "Attach the supporting statement and evidence bundle",
        "Ensure all exhibits are labelled and indexed",
        "Serve copies on the other parties (rental provider and co-renters)",
        "File the documents with VCAT (check current requirements)",
    ]
    for item in checklist:
        c.drawString(margin, y, f"- {item}")
        y -= 7 * mm
    c.setFont("Helvetica", 8)
    c.drawString(margin, 20 * mm, f"Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()
