"""Source adapters for Phase 8 Government Biz.

Each adapter encapsulates the logic required to fetch records from a
specific API or data feed and normalize them into the common Record
model defined in `core.models`.  Only a few stubs are included here; new
adapters can be added by following the same pattern.
"""

from .sam_adapter import SamAdapter
from .usaspending_adapter import UsaSpendingAdapter

__all__ = ["SamAdapter", "UsaSpendingAdapter"]
