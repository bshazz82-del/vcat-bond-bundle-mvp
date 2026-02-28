from __future__ import annotations

import os
import uuid
from typing import BinaryIO, Tuple

from ..config import settings

STORAGE_ROOT = settings.STORAGE_ROOT

def ensure_storage_dirs() -> None:
    os.makedirs(STORAGE_ROOT, exist_ok=True)
    os.makedirs(os.path.join(STORAGE_ROOT, "uploads"), exist_ok=True)
    os.makedirs(os.path.join(STORAGE_ROOT, "generated"), exist_ok=True)

def save_upload(file_obj: BinaryIO, filename: str) -> Tuple[str, str]:
    ensure_storage_dirs()
    ext = os.path.splitext(filename)[1]
    key = f"uploads/{uuid.uuid4().hex}{ext}"
    saved_path = os.path.join(STORAGE_ROOT, key)
    os.makedirs(os.path.dirname(saved_path), exist_ok=True)
    with open(saved_path, "wb") as f:
        file_obj.seek(0)
        f.write(file_obj.read())
    return key, saved_path

def save_generated(content: bytes, doc_type: str, extension: str = ".pdf") -> Tuple[str, str]:
    ensure_storage_dirs()
    key = f"generated/{doc_type}_{uuid.uuid4().hex}{extension}"
    saved_path = os.path.join(STORAGE_ROOT, key)
    os.makedirs(os.path.dirname(saved_path), exist_ok=True)
    with open(saved_path, "wb") as f:
        f.write(content)
    return key, saved_path
