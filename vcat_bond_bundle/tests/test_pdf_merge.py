from io import BytesIO
import os, sys
import pytest
from reportlab.pdfgen import canvas
from pypdf import PdfReader

CURRENT_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from vcat_bond_bundle.app.services.pdf_merge import merge_pdfs

def create_pdf(path: str, num_pages: int) -> None:
    c = canvas.Canvas(path)
    for i in range(num_pages):
        c.drawString(100, 750, f"Page {i+1}")
        c.showPage()
    c.save()

@pytest.fixture
def tmp_pdfs(tmp_path):
    pdf1 = tmp_path / "file1.pdf"
    pdf2 = tmp_path / "file2.pdf"
    create_pdf(str(pdf1), 1)
    create_pdf(str(pdf2), 2)
    return [str(pdf1), str(pdf2)]

def test_merge_pdfs_page_count(tmp_pdfs, tmp_path):
    merged_bytes = merge_pdfs(tmp_pdfs)
    merged_path = tmp_path / "merged.pdf"
    with open(merged_path, "wb") as f:
        f.write(merged_bytes)
    reader = PdfReader(str(merged_path))
    assert len(reader.pages) == 3
