from adapters.samples import SampleAdapter
from core.config import Settings
from core.classify_products import classify_records
from core.score_opportunities import score_records
from core.route_records import route_records
from core.dedupe import dedupe_records


def records():
    return route_records(score_records(classify_records(SampleAdapter(Settings()).fetch().records)))


def test_fast_purchase():
    item = records()[0]
    assert item.fast_purchase_score >= 70
    assert item.recommended_module == "GOV FAST PURCHASE POSTS"


def test_auction_route():
    assert any(r.recommended_module == "GOV AUCTIONS" for r in records())


def test_dedupe():
    raw = SampleAdapter(Settings()).fetch().records
    assert len(dedupe_records(raw + [raw[0]])) == len(raw)
