from __future__ import annotations
import json
from typing import Dict, Iterable, List
import requests
from core.compliance import compliance_notes
from core.route_records import sales_output
from core.schemas import NormalizedRecord
from .module_definitions import MODULE_API_NAMES


def api_name(label: str) -> str:
    return label.replace("/", " ").replace("-", " ").replace("&", "and").replace(".", "").title().replace(" ", "_")


def record_to_zoho(record: NormalizedRecord) -> Dict[str, object]:
    data = {
        "Source_Platform": record.source_platform,
        "Source_Record_ID": record.source_record_id,
        "Source_URL": record.source_url,
        "Raw_Payload_JSON": json.dumps(record.raw_payload, default=str)[:32000],
        "Notes": f"Priority {record.priority_label}; tags: {', '.join(record.fast_lane_tags)}"
    }
    if record.recommended_module == "GOV FAST PURCHASE POSTS":
        data.update({"Fast_Purchase_Name":record.title,"Buyer_Agency":record.agency_name,"Government_Level":record.government_level,"Jurisdiction":record.jurisdiction,"State_Territory":record.state or record.territory,"County_City":", ".join(x for x in [record.county, record.city] if x),"Buyer_Contact":record.buyer_contact,"Buyer_Email":record.buyer_email,"Buyer_Phone":record.buyer_phone,"Product_Category":record.product_category,"Product_Interest":record.product_interest,"Product_Keywords_Matched":", ".join(record.product_keywords_matched),"Quantity_Volume_Signal":record.unit_of_measure or str(record.estimated_volume or ""),"Estimated_Value":record.estimated_value,"Purchase_Path":record.purchase_path,"Purchase_Urgency":record.recommended_action,"Posted_Date":record.posted_date,"Due_Date":record.due_date,"Delivery_Location":record.place_of_performance,"Route_Terminal_Fit":record.route_fit,"Supplier_Fit":record.supplier_fit,"Compliance_Needed":compliance_notes(record),"Direct_PO_Eligible":record.direct_po_eligible,"Purchase_Card_Possible":record.direct_po_eligible,"Emergency_Trigger":record.emergency_trigger,"Fast_Purchase_Score":record.fast_purchase_score,"Margin_Potential":"High" if record.priority_label in {"A1","A2"} else "Review","Next_Action":record.recommended_action,"Next_Action_Due":record.due_date,"Status":record.recommended_action if record.recommended_action in {"Call Now","Quote Now","Procurement Review"} else "New"})
    elif record.recommended_module == "LEADS GOV":
        data.update({"Gov_Lead_Name":record.title,"Notice_Type":record.notice_type,"Government_Level":record.government_level,"Jurisdiction":record.jurisdiction,"Agency_Name":record.agency_name,"Buying_Office":record.buying_office,"Buyer_Contact":record.buyer_contact,"Buyer_Email":record.buyer_email,"Buyer_Phone":record.buyer_phone,"Product_Category":record.product_category,"Product_Interest":record.product_interest,"NAICS":", ".join(record.naics),"PSC_FSC":", ".join(record.psc_fsc),"NIGP":", ".join(record.nigp),"UNSPSC":", ".join(record.unspsc),"Posted_Date":record.posted_date,"Due_Date":record.due_date,"Award_Date":record.award_date,"Estimated_Value":record.estimated_value,"Estimated_Gallons_Units":record.estimated_volume,"Place_Of_Performance":record.place_of_performance,"State_Territory":record.state or record.territory,"Route_Terminal_Fit":record.route_fit,"Set_Aside":record.set_aside,"Contract_Vehicle":record.contract_vehicle,"Direct_PO_Eligible":record.direct_po_eligible,"Emergency_Trigger":record.emergency_trigger,"Priority_Score":record.priority_score,"Bid_Status":"Review" if record.priority_score >= 70 else "Watch","Next_Action":record.recommended_action,"Next_Action_Date":record.due_date,"Compliance_Notes":compliance_notes(record)})
    elif record.recommended_module == "GOV AUCTIONS":
        data.update({"Auction_Asset_Name":record.title,"Asset_Type":record.product_category,"Asset_Category":record.product_interest,"Location":record.place_of_performance,"State_Territory":record.state,"Current_Bid":record.estimated_value,"Auction_Close_Date":record.due_date,"Margin_Score":record.fast_purchase_score,"Buy_Pass_Recommendation":"Buy/evaluate" if record.fast_purchase_score >= 70 else "Pass/watch","Status":"Active"})
    elif record.recommended_module == "GOV AWARDS":
        data.update({"Award_Name":record.title,"Awarding_Agency":record.agency_name,"Recipient_Vendor":record.awarded_vendor or record.incumbent_vendor,"Product_Category":record.product_category,"Product_Keywords":", ".join(record.product_keywords_matched),"NAICS":", ".join(record.naics),"PSC_FSC":", ".join(record.psc_fsc),"NIGP":", ".join(record.nigp),"Award_Amount":record.estimated_value,"Award_Date":record.award_date,"Place_Of_Performance":record.place_of_performance,"State_Territory":record.state,"Contract_Vehicle":record.contract_vehicle,"Award_Type":record.notice_type,"Incumbent_Renewal_Watch":True,"Secure_Supplies_Pursuit_Strategy":"Track expiration, attack incumbent on price/service/logistics, and build direct buyer relationship."})
    elif record.recommended_module == "GOV DIRECT PO":
        so = sales_output(record)
        data.update({"Direct_PO_Target_Name":record.title,"Buyer_Agency":record.agency_name,"Buyer_Type":record.buying_office,"Government_Level":record.government_level,"Jurisdiction":record.jurisdiction,"Product_Fit":record.product_category,"Likely_Purchase_Need":record.description,"Estimated_Recurring_Value":record.estimated_value,"Contact_Name":record.buyer_contact,"Contact_Email":record.buyer_email,"Contact_Phone":record.buyer_phone,"Procurement_Portal":record.source_url,"Credit_Card_P_Card_Possible":record.direct_po_eligible,"Emergency_Supplier_Need":record.emergency_trigger,"Route_Fit":record.route_fit,"Sales_Script":so["sales_script"],"Next_Call_Date":record.due_date,"Status":"Active"})
    else:
        data.update({"Watchlist_Name":record.title,"Buyer_Agency":record.agency_name,"Product_Category":record.product_category,"Action_Plan":record.recommended_action,"Status":"Watch"})
    return {k:v for k,v in data.items() if v not in (None, "", [], {})}

class ZohoUpsertClient:
    def __init__(self, api_domain: str, headers: Dict[str, str], dry_run: bool = True):
        self.api_domain = api_domain.rstrip("/"); self.headers = headers; self.dry_run = dry_run
    def upsert_records(self, records: Iterable[NormalizedRecord]) -> Dict[str, object]:
        grouped: Dict[str, List[Dict[str, object]]] = {}
        for r in records:
            grouped.setdefault(MODULE_API_NAMES.get(r.recommended_module, MODULE_API_NAMES["GOV WATCHLIST"]), []).append(record_to_zoho(r))
        result = {"created_or_updated":0,"failed":0,"modules":{}}
        for module, rows in grouped.items():
            if self.dry_run:
                result["modules"][module] = {"action":"dry_run_upsert","count":len(rows),"sample":rows[:2]}; continue
            resp = requests.post(f"{self.api_domain}/crm/v8/{module}/upsert", headers=self.headers, params={"duplicate_check_fields":"Source_Record_ID"}, json={"data":rows}, timeout=60)
            if resp.status_code >= 400:
                result["failed"] += len(rows); result["modules"][module] = {"action":"failed","status_code":resp.status_code,"body":resp.text[:2000]}
            else:
                result["created_or_updated"] += len(rows); result["modules"][module] = {"action":"upserted","count":len(rows),"body":resp.json()}
        return result
