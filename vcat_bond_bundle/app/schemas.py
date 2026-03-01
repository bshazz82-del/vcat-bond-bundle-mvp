from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class FileUploadResponse(BaseModel):
    file_id: int = Field(...)
    filename: str
    mime_type: str


class CaseCreateRequest(BaseModel):
    session_uuid: str
    property_address: Optional[str] = None
    tenancy_end_date: Optional[datetime] = None
    bond_amount: Optional[str] = None
    narrative: Optional[str] = None
    orders_sought: Optional[str] = None


class CaseResponse(BaseModel):
    # ✅ Pydantic v2 replacement for "orm_mode = True"
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    property_address: Optional[str]
    tenancy_end_date: Optional[datetime]
    bond_amount: Optional[str]
    narrative: Optional[str]
    orders_sought: Optional[str]
