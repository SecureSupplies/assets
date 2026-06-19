"""Zoho CRM integration for Phase 8 Government Biz.

This package encapsulates the logic required to authenticate with
Zoho via OAuth, create custom modules and fields, upload data via
bulk API, and manage dashboards and tasks.  Only skeleton functions
are provided here; full implementations would map our Record model
into Zoho module schemas and handle retries, batching, error
reporting and token refresh.
"""

from .zoho_client import ZohoClient

__all__ = ["ZohoClient"]
