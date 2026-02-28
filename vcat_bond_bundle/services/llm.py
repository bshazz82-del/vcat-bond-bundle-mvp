from __future__ import annotations
import re
from typing import List, Optional
from pydantic import BaseModel
from ..models import Case

class ChronologyEntry(BaseModel):
    date: str
    event: str

class HearingScript(BaseModel):
    opening: str
    evidence: List[str]
    closing: str

class LLMOutput(BaseModel):
    chronology: List[ChronologyEntry]
    hearing_script: HearingScript

def generate_llm_output(narrative: Optional[str], case: Optional[Case]) -> LLMOutput:
    chronology_entries: List[ChronologyEntry] = []
    if narrative:
        sentences = re.split(r"[.!?]\s+", narrative)
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                chronology_entries.append(ChronologyEntry(date="N/A", event=sentence))

    evidence_labels: List[str] = []
    if case and case.evidence_files:
        for idx, _ in enumerate(case.evidence_files, start=1):
            evidence_labels.append(f"Exhibit {chr(ord('A') + idx - 1)}")

    hearing_script = HearingScript(
        opening="Introduce yourself and state that you are seeking repayment of the bond.",
        evidence=evidence_labels,
        closing="Thank the tribunal and restate your request for the bond to be repaid."
    )
    return LLMOutput(chronology=chronology_entries, hearing_script=hearing_script)
