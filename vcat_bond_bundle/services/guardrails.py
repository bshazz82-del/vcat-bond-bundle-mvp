from __future__ import annotations
from typing import Optional, Tuple

def check_scope(narrative: Optional[str], orders_sought: Optional[str]) -> Tuple[bool, Optional[str]]:
    text = f"{narrative or ''} {orders_sought or ''}".lower()
    out_of_scope_keywords = [
        "family violence","intervention order","restraining order","avo",
        "police","criminal","assault","fraud","arrest","charge",
        "commercial lease","business lease","warehouse","shop","factory",
        "compensation","personal injury","repairs","maintenance"
    ]
    for kw in out_of_scope_keywords:
        if kw in text:
            return False, (
                "This tool can only assist with renter-initiated bond recovery. "
                "Your description mentions an issue this tool cannot handle (for example family violence, "
                "criminal matters, commercial leases, or non-bond claims)."
            )
    # Simple multi-issue heuristic
    if narrative and (narrative.count("\n") >= 2):
        return False, (
            "It looks like you may be raising multiple issues. This tool is limited to bond return claims only."
        )
    return True, None
