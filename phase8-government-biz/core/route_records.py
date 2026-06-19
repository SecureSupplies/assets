from __future__ import annotations

from typing import Iterable, List

from .schemas import NormalizedRecord
from .score_opportunities import days_until


FAST_NOTICE_WORDS = ["rfq", "quote", "purchase order", "direct purchase", "emergency", "urgent", "small purchase", "simplified acquisition", "delivery needed", "spot buy"]
FORMAL_NOTICE_WORDS = ["rfi", "rfp", "sources sought", "presolicitation", "solicitation", "tender", "bid", "sole source"]
AUCTION_WORDS = ["auction", "surplus", "asset sale", "vehicle sale"]
AWARD_WORDS = ["award", "obligation", "recipient", "incumbent", "contract award"]
DIRECT_PO_BUYER_WORDS = ["public works", "city fleet", "county fleet", "school", "airport", "port", "transit", "utility", "water district", "wastewater", "hospital", "correction", "emergency management", "fire", "police", "tribal", "parks", "national guard"]


def route_record(record: NormalizedRecord) -> NormalizedRecord:
    text = f" {record.title} {record.description} {record.notice_type} {record.source_type} {record.agency_name} {record.buying_office} ".lower()
    expired = (days_until(record.due_date) or 0) < 0 if record.due_date else False

    if record.source_type.lower() == "auction" or any(word in text for word in AUCTION_WORDS):
        record.recommended_module = "GOV AUCTIONS"
        if expired:
            record.recommended_action = "Auction Closed / Pass"
        elif record.fast_purchase_score >= 80:
            record.recommended_action = "Evaluate Asset Buy"
        return record

    if any(word in text for word in AWARD_WORDS) or record.source_type.lower() == "award":
        record.recommended_module = "GOV AWARDS"
        record.recommended_action = "Incumbent / Renewal Watch"
        return record

    if expired:
        record.recommended_module = "GOV WATCHLIST"
        record.recommended_action = "Expired - Renewal / Rebid Watch"
        return record

    if record.fast_purchase_score >= 55 or record.direct_po_eligible or any(word in text for word in FAST_NOTICE_WORDS):
        record.recommended_module = "GOV FAST PURCHASE POSTS"
        return record

    if any(word in text for word in FORMAL_NOTICE_WORDS):
        record.recommended_module = "LEADS GOV"
        return record

    if any(word in text for word in DIRECT_PO_BUYER_WORDS):
        record.recommended_module = "GOV DIRECT PO"
        record.recommended_action = "Call Buyer / Vendor Registration"
        return record

    record.recommended_module = "LEADS GOV" if record.priority_score >= 70 else "GOV WATCHLIST"
    return record


def route_records(records: Iterable[NormalizedRecord]) -> List[NormalizedRecord]:
    return [route_record(record) for record in records]


def sales_output(record: NormalizedRecord) -> dict:
    product = record.product_category or "Secure Supplies product lane"
    buyer = record.agency_name or record.buying_office or "Government buyer"
    pricing_basis = "Rack/index + freight + margin target" if "fuel" in product.lower() or "diesel" in product.lower() else "Supplier quote + freight + target gross margin"
    script = f"We can support {product} with delivered supply, logistics coordination, and recurring service. Who handles same-day quote approval, purchase orders, vendor registration, and delivery scheduling?"
    if "tank" in " ".join(record.fast_lane_tags).lower() or "tank" in product.lower():
        script = "We can support delivered fuel, temporary tank rental, refill monitoring, and emergency dispatch. Who handles tank placement approval and same-day fuel PO issuance?"
    return {
        "action": record.recommended_action,
        "product": product,
        "buyer": buyer,
        "need": record.title,
        "route_fit": record.route_fit,
        "supplier_need": "Confirm terminal/supplier availability, carrier quote, insurance, and delivery window.",
        "sales_script": script,
        "email_subject": f"Quote support: {product} for {buyer}",
        "short_email": f"We can quote {product} for {record.title}. Please send delivery location, quantity, deadline, delivery access notes, and PO/p-card path so we can respond fast.",
        "product_fit_explanation": f"Matched {product} via {', '.join(record.product_keywords_matched[:8]) or 'source category/code'}.",
        "pricing_basis_needed": pricing_basis,
        "compliance_requirement": "Validate vendor registration, insurance, SDS/product documentation, and delivery-site requirements.",
        "bid_no_bid_recommendation": "Bid/quote" if record.priority_label in {"A1", "A2", "B1"} and not expired else "Watch/no-bid unless easy quote",
        "next_action_deadline": record.due_date or "Same day for A1/A2"
    }
