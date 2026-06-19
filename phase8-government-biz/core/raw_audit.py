from __future__ import annotations
from typing import Iterable, List, Dict
from .schemas import NormalizedRecord


def raw_audit_rows(records: Iterable[NormalizedRecord]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for r in records:
        rows.append({
            "raw_record_name": f"{r.source_platform} {r.source_record_id}",
            "source_platform": r.source_platform,
            "source_record_id": r.source_record_id,
            "source_url": r.source_url,
            "pulled_at": r.pulled_at,
            "normalized_record_id": f"{r.source_platform}:{r.source_record_id}",
            "target_module": r.recommended_module,
            "record_hash": r.record_hash,
            "raw_data": r.raw_payload,
            "processing_status": "Processed",
            "error_details": ""
        })
    return rows
