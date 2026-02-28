from __future__ import annotations
from io import BytesIO
from typing import List
from pypdf import PdfReader, PdfWriter

def merge_pdfs(file_paths: List[str]) -> bytes:
    writer = PdfWriter()
    for path in file_paths:
        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()
