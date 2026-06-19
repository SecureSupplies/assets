from __future__ import annotations
from .schemas import NormalizedRecord


def compliance_notes(record: NormalizedRecord) -> str:
    notes = ["Vendor registration", "Insurance/W-9", "SDS/product documentation where applicable"]
    text = f"{record.title} {record.description} {record.product_category}".lower()
    if "aviation" in text or "jet" in text or "avgas" in text:
        notes.append("Aviation fuel spec/quality documentation")
    if "oxygen" in text or "medical gas" in text:
        notes.append("Medical gas documentation and cylinder/bulk handling compliance")
    if "tank" in text:
        notes.append("Tank placement, secondary containment, delivery-site safety")
    if record.set_aside:
        notes.append(f"Set-aside review: {record.set_aside}")
    return "; ".join(notes)
