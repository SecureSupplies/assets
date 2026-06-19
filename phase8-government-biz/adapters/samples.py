from __future__ import annotations
from .base import AdapterResult, BaseAdapter
from core.normalize import normalize_generic

SAMPLE_RECORDS = [
    {"id":"SAMPLE-SAM-RFQ-001","title":"RFQ emergency generator fuel delivery and temporary double wall diesel tank","description":"County Public Works requires immediate ULSD delivery, 10000 gallons, temporary fuel tank rental, telemetry and refill monitoring. Quote due within 48 hours.","notice_type":"RFQ","government_level":"Local","agency":"Example County Public Works","office":"Fleet and Emergency Management","state":"FL","due_date":"2026-06-19","estimated_value":48000,"naics":["424720"],"psc":"9140","source_url":"https://sam.gov/example/SAMPLE-SAM-RFQ-001"},
    {"id":"SAMPLE-USA-AWARD-002","title":"Award bulk diesel and DEF for municipal fleet annual supply","description":"Awarded vendor supplied diesel fuel and diesel exhaust fluid under annual requirements contract for city fleet, public works, and generators.","notice_type":"Award","government_level":"Local","agency":"Example City Fleet Services","recipient_name":"Incumbent Fuel LLC","state":"TX","award_date":"2025-11-15","estimated_value":625000,"naics":["424720"],"psc":"9140","source_url":"https://api.usaspending.gov/example/SAMPLE-USA-AWARD-002"},
    {"id":"SAMPLE-GSA-AUCTION-003","title":"Surplus 12000 gallon aboveground fuel tank with pump and dispenser","description":"GSA auction asset. Double wall AST, pump, dispenser, available for inspection. Potential rental fleet conversion after repair.","source_type":"auction","government_level":"Federal","agency":"GSA Auctions","state":"GA","current_bid":7500,"close_date":"2026-06-20","source_url":"https://gsaauctions.gov/example/SAMPLE-GSA-AUCTION-003"},
    {"id":"SAMPLE-STATE-PO-004","title":"Informal quote for sodium hypochlorite and liquid oxygen service at wastewater plant","description":"Water district seeks quote for sodium hypochlorite, liquid oxygen, CO2, and bulk delivery for wastewater treatment operations. P-card possible for urgent purchase.","notice_type":"Informal Quote","government_level":"Special District","agency":"Example Regional Water District","state":"CA","due_date":"2026-06-21","estimated_value":82000,"nigp":"885","source_url":"https://example-state-procurement.gov/bids/SAMPLE-STATE-PO-004"},
    {"id":"SAMPLE-AIRPORT-005","title":"Airport Jet A fuel supply and avgas emergency replenishment","description":"Regional airport requires Jet A and Avgas quote for FBO fuel inventory replenishment and storm response stock planning.","notice_type":"Solicitation","government_level":"Local","agency":"Example Regional Airport Authority","state":"LA","due_date":"2026-06-27","estimated_value":310000,"psc":"9130","source_url":"https://airport.example.gov/procurement/SAMPLE-AIRPORT-005"}
]

class SampleAdapter(BaseAdapter):
    source_name = "Phase 8 Sample Data"
    source_type = "sample"
    source_url = "local://phase8-samples"
    access_method = "Sample"
    def fetch(self, limit: int = 50) -> AdapterResult:
        records = [normalize_generic(raw, source_platform=self.source_name, source_type=raw.get("source_type", "sample"), source_url=str(raw.get("source_url", self.source_url))) for raw in SAMPLE_RECORDS[:limit]]
        return AdapterResult(records, self.health().ok(len(records)))
