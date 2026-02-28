from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def generate_uuid() -> str:
    return str(uuid.uuid4())

class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(Integer, primary_key=True, index=True)
    session_uuid = Column(String, unique=True, default=generate_uuid, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    cases = relationship("Case", back_populates="session")

class Case(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("user_sessions.id"), nullable=False)
    status = Column(String, default="draft", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    retention_expires_at = Column(DateTime, nullable=True)

    property_address = Column(String, nullable=True)
    tenancy_end_date = Column(DateTime, nullable=True)
    bond_amount = Column(String, nullable=True)
    narrative = Column(Text, nullable=True)
    orders_sought = Column(Text, nullable=True)

    session = relationship("UserSession", back_populates="cases")
    evidence_files = relationship("EvidenceFile", back_populates="case")
    generated_docs = relationship("GeneratedDoc", back_populates="case")
    audit_logs = relationship("AuditLog", back_populates="case")

class EvidenceFile(Base):
    __tablename__ = "evidence_files"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    filename = Column(String, nullable=False)
    s3_key = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    pages = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    case = relationship("Case", back_populates="evidence_files")

class GeneratedDoc(Base):
    __tablename__ = "generated_docs"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    doc_type = Column(String, nullable=False)
    s3_key = Column(String, nullable=False)
    watermarked = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    case = relationship("Case", back_populates="generated_docs")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    event_type = Column(String, nullable=False)
    data = Column(Text, nullable=True)
    prompt_version = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    case = relationship("Case", back_populates="audit_logs")

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    stripe_session_id = Column(String, nullable=False)
    amount = Column(String, nullable=False)
    currency = Column(String, nullable=False, default="AUD")
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)
    case = relationship("Case")
