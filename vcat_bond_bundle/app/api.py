from __future__ import annotations

import os
import fastapi
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Request
from sqlalchemy.orm import Session

from . import db, models, schemas
from .config import settings
from .utils import add_watermark
from .services import storage, guardrails, llm, pdf_generator, form_filler, pdf_merge
from .services import payment as payment_service

router = APIRouter()

@router.post("/upload", response_model=schemas.FileUploadResponse)
async def upload_file(
    case_id: int,
    file: UploadFile = File(...),
    db_session: Session = Depends(db.get_db),
) -> schemas.FileUploadResponse:
    if file.content_type not in ("application/pdf", "image/jpeg", "image/png"):
        raise HTTPException(status_code=400, detail="Unsupported file type")

    s3_key, _ = storage.save_upload(file.file, file.filename)
    evidence = models.EvidenceFile(
        case_id=case_id,
        filename=file.filename,
        s3_key=s3_key,
        mime_type=file.content_type,
        pages=0,
    )
    db_session.add(evidence)
    db_session.flush()

    db_session.add(models.AuditLog(case_id=case_id, event_type="upload", data=f"uploaded {file.filename}"))

    return schemas.FileUploadResponse(file_id=evidence.id, filename=evidence.filename, mime_type=evidence.mime_type)

@router.post("/case", response_model=schemas.CaseResponse)
async def create_or_update_case(payload: schemas.CaseCreateRequest, db_session: Session = Depends(db.get_db)) -> schemas.CaseResponse:
    session = db_session.query(models.UserSession).filter_by(session_uuid=payload.session_uuid).first()
    if session is None:
        session = models.UserSession(session_uuid=payload.session_uuid)
        db_session.add(session)
        db_session.flush()

    case = db_session.query(models.Case).filter_by(session_id=session.id, status="draft").first()
    if case is None:
        case = models.Case(session_id=session.id)
        db_session.add(case)
        db_session.flush()

    allowed, message = guardrails.check_scope(payload.narrative, payload.orders_sought)
    if not allowed:
        db_session.add(models.AuditLog(case_id=case.id, event_type="guardrail_block", data=message))
        raise HTTPException(status_code=400, detail=message)

    case.property_address = payload.property_address
    case.tenancy_end_date = payload.tenancy_end_date
    case.bond_amount = payload.bond_amount
    case.narrative = payload.narrative
    case.orders_sought = payload.orders_sought
    db_session.add(case)
    db_session.flush()
    db_session.add(models.AuditLog(case_id=case.id, event_type="case_update", data="Updated case fields"))

    return schemas.CaseResponse.from_orm(case)

@router.post("/case/{case_id}/generate-preview")
async def generate_preview(case_id: int, db_session: Session = Depends(db.get_db)):
    case = db_session.query(models.Case).filter_by(id=case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    allowed, message = guardrails.check_scope(case.narrative, case.orders_sought)
    if not allowed:
        raise HTTPException(status_code=400, detail=message)

    llm_output = llm.generate_llm_output(case.narrative, case)
    chronology_strings = [f"{e.date}: {e.event}" for e in llm_output.chronology]
    db_session.add(models.AuditLog(case_id=case.id, event_type="llm_output", data=llm_output.json(), prompt_version="v1"))

    form_bytes = form_filler.generate_form_419a(case)
    statement_bytes = pdf_generator.generate_supporting_statement(case, chronology_strings)
    orders_bytes = pdf_generator.generate_orders_sought(case)
    evidence_index_bytes = pdf_generator.generate_evidence_index(case.evidence_files)
    hearing_script_bytes = pdf_generator.generate_hearing_script(case, chronology_strings)
    checklist_bytes = pdf_generator.generate_checklist(case)

    evidence_paths = [os.path.join(settings.STORAGE_ROOT, ev.s3_key) for ev in case.evidence_files]
    merged_evidence_bytes = pdf_merge.merge_pdfs(evidence_paths) if evidence_paths else b""

    docs_data = {
        "form": form_bytes,
        "statement": statement_bytes,
        "orders": orders_bytes,
        "index": evidence_index_bytes,
        "script": hearing_script_bytes,
        "checklist": checklist_bytes,
    }
    if evidence_paths:
        docs_data["bundle"] = merged_evidence_bytes

    generated_docs = {}
    for doc_type, content in docs_data.items():
        key_unwm, _ = storage.save_generated(content, doc_type, ".pdf")
        wm_content = add_watermark(content)
        key_wm, _ = storage.save_generated(wm_content, f"{doc_type}_wm", ".pdf")

        db_session.add(models.GeneratedDoc(case_id=case.id, doc_type=doc_type, s3_key=key_unwm, watermarked=False))
        db_session.add(models.GeneratedDoc(case_id=case.id, doc_type=doc_type, s3_key=key_wm, watermarked=True))
        db_session.add(models.AuditLog(case_id=case.id, event_type="document_generated", data=doc_type))

        generated_docs[doc_type] = {"unwatermarked_key": key_unwm, "watermarked_key": key_wm}

    case.status = "preview_ready"
    db_session.add(case)
    db_session.flush()
    return {"case_id": case.id, "status": case.status, "documents": generated_docs}

@router.post("/case/{case_id}/create-checkout-session")
async def create_checkout_session(case_id: int, db_session: Session = Depends(db.get_db)):
    case = db_session.query(models.Case).filter_by(id=case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.status != "preview_ready":
        raise HTTPException(status_code=400, detail="Payment can only be initiated after preview is ready")
    url = payment_service.create_checkout_session(db_session, case)
    return {"checkout_url": url}

@router.post("/stripe-webhook")
async def stripe_webhook(request: Request, db_session: Session = Depends(db.get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    payment_service.handle_stripe_webhook(db_session, payload, sig_header)
    return {"status": "ok"}

@router.get("/case/{case_id}/documents/{doc_type}")
async def download_document(case_id: int, doc_type: str, preview: bool = True, db_session: Session = Depends(db.get_db)):
    valid_types = {"form","statement","orders","index","bundle","script","checklist"}
    if doc_type not in valid_types:
        raise HTTPException(status_code=400, detail="Invalid document type")

    case = db_session.query(models.Case).filter_by(id=case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    want_watermarked = True
    if case.status == "paid" and not preview:
        want_watermarked = False

    doc = (
        db_session.query(models.GeneratedDoc)
        .filter_by(case_id=case.id, doc_type=doc_type, watermarked=want_watermarked)
        .order_by(models.GeneratedDoc.created_at.desc())
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    path = os.path.join(settings.STORAGE_ROOT, doc.s3_key)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File missing from storage")

    with open(path, "rb") as f:
        content = f.read()

    return fastapi.responses.Response(
        content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={doc_type}.pdf"},
    )
