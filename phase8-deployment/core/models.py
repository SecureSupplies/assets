"""Data models for Phase 8 Government Biz.

Defines a simple record dataclass used throughout the ingestion and processing
pipeline.  In a full implementation this would include many more
attributes and type annotations; this stub keeps things minimal for
demonstration.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Record:
    """Normalized representation of a government sourcing opportunity."""

    source: str
    id: str
    title: str
    description: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)
    taxonomy: Optional[str] = None
    fast_purchase_score: Optional[int] = None
    opportunity_score: Optional[int] = None
    module: Optional[str] = None  # target CRM module
