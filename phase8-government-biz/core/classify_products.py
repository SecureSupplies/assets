from __future__ import annotations
from typing import Dict, Iterable, List
import re
from .schemas import NormalizedRecord

PRODUCT_KEYWORDS: Dict[str, List[str]] = {
    "Diesel / ULSD / clear diesel": ["diesel", "ulsd", "ultra low sulfur diesel", "clear diesel", "fuel oil", "heating oil", "fleet fuel", "bulk fuel", "fuel delivery", "kerosene", "burner fuel"],
    "Red diesel / off-road diesel": ["red diesel", "dyed diesel", "off-road diesel", "off road diesel"],
    "Emergency generator fuel": ["generator fuel", "emergency fuel", "backup power fuel", "standby generator", "temporary fuel"],
    "DEF / AdBlue / AUS32": ["def", "diesel exhaust fluid", "aus32", "adblue", "urea solution", "bulk def", "def tote", "def tank"],
    "Jet A / Jet A-1 / aviation fuel": ["jet a", "jet-a", "jet a-1", "jet-a1", "aviation fuel", "jp-8", "jp8", "fbo fuel", "airport fuel", "aircraft fuel"],
    "Avgas": ["avgas", "aviation gasoline", "100ll"],
    "Marine diesel / MGO / bunkering": ["marine diesel", "mgo", "marine gas oil", "bunkering", "vessel fuel", "ferry fuel", "port fuel", "harbor fuel", "dredge fuel"],
    "Propane / LPG": ["propane", "lpg", "liquefied petroleum gas"],
    "CNG / LNG / RNG / natural gas": ["cng", "compressed natural gas", "lng", "liquefied natural gas", "rng", "renewable natural gas", "natural gas"],
    "Hydrogen / H2": ["hydrogen", "h2", "fuel cell"],
    "Oxygen / O2 / LOX": ["oxygen", "o2", "lox", "liquid oxygen", "medical oxygen"],
    "Nitrogen / N2 / LIN": ["nitrogen", "n2", "lin", "liquid nitrogen"],
    "CO2 / carbon dioxide": ["co2", "carbon dioxide", "dry ice"],
    "Helium / He": ["helium", "helium gas"],
    "Argon / specialty gases": ["argon", "specialty gas", "compressed gas", "liquefied gas", "cryogenic", "gas cylinder", "bulk gas", "industrial gas", "medical gas"],
    "Ammonia / urea / UAN / NPK / fertilizers": ["ammonia", "anhydrous ammonia", "urea", "uan", "uan 28", "uan 32", "npk", "fertilizer", "ammonium sulfate", "map", "dap"],
    "Water / wastewater chemicals": ["water treatment chemical", "wastewater chemical", "ph control", "odor control", "flocculant", "polymer", "caustic", "chlorine", "sodium hypochlorite", "sodium bisulfite", "alum"],
    "Fuel tanks / DEF tanks / water tanks / gas tanks": ["fuel tank", "diesel tank", "def tank", "water tank", "gas tank", "propane tank", "aboveground storage tank", "double wall tank", "portable tank", "temporary tank", "skid tank", "tank trailer", "iso tank", "fuel island", "fuel skid"],
    "Tank rentals": ["tank rental", "temporary tank", "rental tank", "portable tank rental"],
    "Pumps / dispensers / fuel management / telemetry": ["fuel pump", "dispenser", "telemetry", "fuel management system", "pump", "meter", "monitoring"],
    "Auction assets": ["auction", "surplus", "generator", "light tower", "fuel truck", "utility truck", "trailer", "forklift", "portable storage", "fleet vehicle"],
    "Data center fuel / backup power fuel": ["data center", "datacenter", "backup power", "critical power"],
    "Emergency response fuel": ["emergency response", "disaster response", "hurricane", "wildfire", "flood", "state of emergency", "same day", "next day"]
}

CODE_LANES = {
    "424710": "Diesel / ULSD / clear diesel", "424720": "Diesel / ULSD / clear diesel", "324110": "Diesel / ULSD / clear diesel",
    "325120": "Argon / specialty gases", "325311": "Ammonia / urea / UAN / NPK / fertilizers", "325312": "Ammonia / urea / UAN / NPK / fertilizers", "325314": "Ammonia / urea / UAN / NPK / fertilizers", "325998": "Water / wastewater chemicals", "562998": "Water / wastewater chemicals", "493190": "Fuel tanks / DEF tanks / water tanks / gas tanks", "532490": "Tank rentals",
    "9130": "Jet A / Jet A-1 / aviation fuel", "9140": "Diesel / ULSD / clear diesel", "6830": "Argon / specialty gases", "6810": "Water / wastewater chemicals", "6840": "Water / wastewater chemicals", "6850": "Water / wastewater chemicals", "5430": "Fuel tanks / DEF tanks / water tanks / gas tanks", "4930": "Pumps / dispensers / fuel management / telemetry", "4320": "Pumps / dispensers / fuel management / telemetry", "6115": "Emergency generator fuel",
    "405": "Diesel / ULSD / clear diesel", "430": "Argon / specialty gases", "335": "Ammonia / urea / UAN / NPK / fertilizers", "885": "Water / wastewater chemicals", "545": "Pumps / dispensers / fuel management / telemetry", "578": "Auction assets", "830": "Fuel tanks / DEF tanks / water tanks / gas tanks", "936": "Pumps / dispensers / fuel management / telemetry", "962": "Pumps / dispensers / fuel management / telemetry"
}
FAST_PURCHASE_KEYWORDS = ["rfq", "quote request", "quick quote", "informal quote", "purchase order", "p-card", "credit card", "direct purchase", "emergency purchase", "urgent", "immediate need", "same day", "next day", "spot buy", "small purchase", "simplified acquisition", "delivery needed", "fuel delivery", "generator fuel", "tank rental"]


def _contains(text: str, needle: str) -> bool:
    n = needle.lower().strip()
    if n in {"def", "h2", "o2", "n2", "he"}:
        return re.search(rf"\b{re.escape(n)}\b", text) is not None
    return n in text


def classify_record(record: NormalizedRecord) -> NormalizedRecord:
    text = f" {record.title} {record.description} {record.notice_type} {record.agency_name} {record.buying_office} {record.place_of_performance} ".lower()
    matches: Dict[str, List[str]] = {}
    for lane, keywords in PRODUCT_KEYWORDS.items():
        found = [kw for kw in keywords if _contains(text, kw)]
        if found:
            matches[lane] = found
    for code in list(record.naics) + list(record.psc_fsc) + list(record.nigp) + list(record.unspsc):
        lane = CODE_LANES.get(str(code).strip().upper().replace("PSC", "").replace("FSC", ""))
        if lane:
            matches.setdefault(lane, []).append(str(code))
    if matches:
        record.product_category = sorted(matches.items(), key=lambda item: len(item[1]), reverse=True)[0][0]
        record.product_interest = "; ".join(matches.keys())
        record.product_keywords_matched = sorted({kw for values in matches.values() for kw in values})
    lane_text = " ".join(matches.keys()).lower()
    tags = []
    if "tank" in lane_text and ("diesel" in lane_text or "fuel" in text): tags.append("TANK_PLUS_FUEL")
    if "diesel" in lane_text and ("def" in lane_text or "diesel exhaust fluid" in text): tags.append("DIESEL_PLUS_DEF")
    if "generator" in lane_text: tags.append("EMERGENCY_GENERATOR_FUEL")
    if "jet" in lane_text or "aviation" in lane_text: tags.append("AIRPORT_JET_A")
    if "marine" in lane_text or "bunkering" in lane_text: tags.append("PORT_MARINE_DIESEL")
    if ("oxygen" in lane_text or "water" in text) and "wastewater" in text: tags.append("WASTEWATER_OXYGEN")
    if "hospital" in text and "oxygen" in lane_text: tags.append("HOSPITAL_OXYGEN")
    if "propane" in lane_text: tags.append("PROPANE_ROUTE")
    if "cng" in lane_text or "lng" in lane_text or "rng" in lane_text: tags.append("CNG_LNG_PROJECT")
    if "fertilizer" in lane_text or "ammonia" in lane_text: tags.append("FERTILIZER_SEASONAL")
    if "auction" in lane_text or record.source_type.lower() == "auction": tags.append("AUCTION_MARGIN")
    if any(_contains(text, kw) for kw in ["disaster", "hurricane", "wildfire", "emergency"]): tags.append("DISASTER_RESPONSE")
    if "data center" in text or "backup power" in text: tags.append("DATA_CENTER_BACKUP_FUEL")
    if any(_contains(text, kw) for kw in FAST_PURCHASE_KEYWORDS): tags.append("DIRECT_PO")
    if "simplified acquisition" in text: tags.append("SIMPLIFIED_ACQUISITION")
    if "dla" in text: tags.append("DLA_ENERGY")
    record.fast_lane_tags = sorted(set(tags))
    record.direct_po_eligible = record.direct_po_eligible or any(_contains(text, kw) for kw in FAST_PURCHASE_KEYWORDS)
    record.emergency_trigger = record.emergency_trigger or any(_contains(text, kw) for kw in ["emergency", "urgent", "same day", "next day", "disaster", "hurricane", "wildfire", "flood"])
    return record


def classify_records(records: Iterable[NormalizedRecord]) -> List[NormalizedRecord]:
    return [classify_record(record) for record in records]
