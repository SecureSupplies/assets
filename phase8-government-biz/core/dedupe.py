from __future__ import annotations
from typing import Iterable, List, Set
import re
from .schemas import NormalizedRecord


def norm(value: str) -> str:
    value = (value or "").lower().strip()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def primary_key(record: NormalizedRecord) -> str:
    return f"{record.source_platform}:{record.source_record_id}".lower()


def fallback_key(record: NormalizedRecord) -> str:
    return "|".join([norm(record.title), norm(record.agency_name), norm(record.due_date), norm(record.state), norm(record.source_url), record.record_hash[:16]])


def dedupe_records(records: Iterable[NormalizedRecord]) -> List[NormalizedRecord]:
    seen_primary: Set[str] = set()
    seen_fallback: Set[str] = set()
    out: List[NormalizedRecord] = []
    for record in records:
        p = primary_key(record)
        f = fallback_key(record)
        if p in seen_primary or f in seen_fallback:
            continue
        seen_primary.add(p)
        seen_fallback.add(f)
        out.append(record)
    return out
