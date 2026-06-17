"""
Automated CRM enrichment script for Secure Supplies.

This script iterates through Leads, Accounts, and Contacts modules in a Zoho CRM
and enriches each record by gathering information from public web sources. It
then updates the CRM with verified product categories (e.g. Diesel, DEF), phone
numbers, emails, websites, addresses, and route assignments. Once configured
with valid API credentials, the script runs continuously until all records
across all modules have been processed.

**Note**: Running this script will update data in your CRM. Review and test
carefully before executing in production. Do not commit your API credentials
into source control.
"""

import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


class ZohoCRMClient:
    """A thin wrapper around the Zoho CRM REST API."""

    def __init__(self, access_token: str, base_url: str = "https://www.zohoapis.com/crm/v2"):
        self.access_token = access_token
        self.base_url = base_url.rstrip("/")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "Content-Type": "application/json",
        }

    def list_records(self, module: str, page: int = 1, per_page: int = 200) -> Dict:
        """
        Retrieve a page of records from a given module. Adjust `per_page` as
        necessary; Zoho CRM limits this to 200 per call.
        """
        url = f"{self.base_url}/{module}?page={page}&per_page={per_page}"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        return response.json()

    def update_record(self, module: str, record_id: str, data: Dict) -> Dict:
        """Update a single record in the specified module."""
        url = f"{self.base_url}/{module}/{record_id}"
        payload = {"data": [data]}
        response = requests.put(url, headers=self._headers(), data=json.dumps(payload))
        response.raise_for_status()
        return response.json()


@dataclass
class CompanyInfo:
    """Container for information scraped about a company."""

    products: List[str] = field(default_factory=list)
    phone: Optional[str] = None
    other_phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    notes: List[str] = field(default_factory=list)


class CompanyScraper:
    """
    Provides methods to search for and extract company data from public web pages.

    Note: Web scraping may violate the terms of service of some websites and
    should respect robots.txt where appropriate. This example uses simple search
    heuristics and is for demonstration purposes only. Consider using an
    official API or third‑party data provider for production use.
    """

    def __init__(self):
        self.session = requests.Session()

    def _search_web(self, query: str, max_results: int = 5) -> List[str]:
        """
        Perform a simple web search using DuckDuckGo and return a list of result URLs.
        In production you should integrate with a proper search API.
        """
        params = {"q": query, "format": "json", "no_html": 1}
        search_url = "https://duckduckgo.com/html/"
        try:
            resp = self.session.get(search_url, params=params, timeout=10)
            resp.raise_for_status()
        except Exception as exc:
            logging.warning(f"Search request failed for query '{query}': {exc}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        links = []
        for a in soup.select("a.result__a"):
            href = a.get("href")
            if href and href.startswith("http"):
                links.append(href)
            if len(links) >= max_results:
                break
        return links

    def _extract_contact_info(self, html: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Simple heuristics to find phone number, email, and a secondary phone."""
        phone_pattern = re.compile(r"\+?\d[\d\s().-]{7,}\d")
        email_pattern = re.compile(r"[\w.-]+@[\w.-]+\.[a-zA-Z]{2,}")
        phones = phone_pattern.findall(html)
        emails = email_pattern.findall(html)
        primary_phone = phones[0] if phones else None
        other_phone = phones[1] if len(phones) > 1 else None
        email = emails[0] if emails else None
        return primary_phone, other_phone, email

    def _extract_address(self, html: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Very simplistic address extraction. For real use cases, integrate with
        geocoding or address-parsing services.
        """
        # Placeholder: look for a pattern like "123 Main St, City, ST 12345"
        address_pattern = re.compile(r"([\dA-Za-z.,'\s-]+),(\s*)([A-Za-z\s]+),(\s*)([A-Z]{2})\s*(\d{5})")
        match = address_pattern.search(html)
        if match:
            street = match.group(1).strip()
            city = match.group(3).strip()
            state = match.group(5).strip()
            zip_code = match.group(6).strip()
            return street, city, state, zip_code, "US"
        return None, None, None, None, None

    def scrape_company_info(self, company_name: str) -> CompanyInfo:
        """
        Given a company name, search the web and attempt to extract relevant data.
        This method returns a CompanyInfo instance with populated fields.
        """
        info = CompanyInfo()
        query = f"{company_name} fuel diesel supplier"
        urls = self._search_web(query)
        for url in urls:
            try:
                resp = self.session.get(url, timeout=10)
                resp.raise_for_status()
            except Exception:
                continue
            html = resp.text

            # Identify product categories
            lowered = html.lower()
            if "diesel" in lowered:
                if "diesel" not in info.products:
                    info.products.append("Diesel")
            if "def" in lowered or "diesel exhaust fluid" in lowered:
                if "DEF" not in info.products:
                    info.products.append("DEF")
            if "bulk fuel" in lowered:
                if "Bulk Fuel" not in info.products:
                    info.products.append("Bulk Fuel")
            if "gasoline" in lowered:
                if "Gasoline" not in info.products:
                    info.products.append("Gasoline")
            if "propane" in lowered:
                if "Propane" not in info.products:
                    info.products.append("Propane")
            if "kerosene" in lowered:
                if "Kerosene" not in info.products:
                    info.products.append("Kerosene")
            if "lubricant" in lowered or "lubricants" in lowered:
                if "Lubricants" not in info.products:
                    info.products.append("Lubricants")
            # Extract contact information only if not already found
            if not info.phone or not info.email:
                phone, other_phone, email = self._extract_contact_info(html)
                info.phone = info.phone or phone
                info.other_phone = info.other_phone or other_phone
                info.email = info.email or email
            # Extract address
            if not info.address:
                street, city, state, zip_code, country = self._extract_address(html)
                if street:
                    info.address = street
                    info.city = city
                    info.state = state
                    info.zip_code = zip_code
                    info.country = country
            # Find website domain
            if not info.website:
                # Use the base URL as website
                parsed = re.match(r"https?://([^/]+)/", url)
                if parsed:
                    info.website = f"https://{parsed.group(1)}"
            # If we've filled enough details, break
            if info.products and info.phone and info.email and info.address:
                break
        return info


def determine_route(city: Optional[str], state: Optional[str]) -> Optional[str]:
    """
    Placeholder function to map a city/state to a route name. In practice,
    populate this mapping using the Routes module from your CRM. Return None
    if no suitable route is found.
    """
    if not state:
        return None
    # Example hardcoded mapping; extend as needed
    route_map = {
        ("TX",): "Texas",
        ("CA",): "California",
        ("FL",): "Florida",
    }
    for states, route_name in route_map.items():
        if state.upper() in states:
            return route_name
    return None


def enrich_module_records(crm: ZohoCRMClient, module: str, scraper: CompanyScraper):
    """
    Iterate through all records in a module and enrich each one with data from
    public sources. Logs progress and updates.
    """
    page = 1
    while True:
        logging.info(f"Fetching {module} page {page}")
        records_response = crm.list_records(module, page=page, per_page=200)
        records = records_response.get("data", [])
        if not records:
            break  # No more pages
        for record in records:
            record_id = record.get("id")
            company_name = record.get("Company_Name") or record.get("Account_Name") or record.get("Last_Name")
            if not company_name:
                continue
            logging.info(f"Processing {module} record {record_id}: {company_name}")
            info = scraper.scrape_company_info(company_name)
            update_data = {}
            # Append products to existing multi-select field if present
            existing_products = record.get("Product") or []
            all_products = set(existing_products) | set(info.products)
            if all_products:
                update_data["Product"] = list(all_products)
            # Update phone fields
            if info.phone and (not record.get("Phone")):
                update_data["Phone"] = info.phone
            if info.other_phone and (not record.get("Other_Phone")):
                update_data["Other_Phone"] = info.other_phone
            # Update email
            if info.email and (not record.get("Email")):
                update_data["Email"] = info.email
            # Update website
            if info.website and (not record.get("Website")):
                update_data["Website"] = info.website
            # Update address fields
            if info.address and (not record.get("Address")):
                update_data["Address" ] = info.address
            if info.city and (not record.get("City")):
                update_data["City"] = info.city
            if info.state and (not record.get("State")):
                update_data["State"] = info.state
            if info.zip_code and (not record.get("Zip")):
                update_data["Zip"] = info.zip_code
            if info.country and (not record.get("Country")):
                update_data["Country"] = info.country
            # Route assignment
            route = determine_route(info.city, info.state)
            if route and (not record.get("Route")):
                update_data["Route"] = route
            if update_data:
                try:
                    crm.update_record(module, record_id, update_data)
                    logging.info(f"Updated {module} record {record_id}: {update_data}")
                except Exception as exc:
                    logging.error(f"Failed to update {module} record {record_id}: {exc}")
            # Throttle between records to avoid rate limits
            time.sleep(1)
        page += 1


def main():
    access_token = os.getenv("ZOHO_ACCESS_TOKEN")
    if not access_token:
        logging.error("Please set the ZOHO_ACCESS_TOKEN environment variable.")
        sys.exit(1)
    crm = ZohoCRMClient(access_token)
    scraper = CompanyScraper()
    # Enrich Leads
    enrich_module_records(crm, "Leads", scraper)
    # Enrich Accounts
    enrich_module_records(crm, "Accounts", scraper)
    # Enrich Contacts
    enrich_module_records(crm, "Contacts", scraper)


if __name__ == "__main__":
    main()