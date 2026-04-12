"""
Download public annual reports from SEC EDGAR and other sources.

Sources:
- SEC EDGAR (USA): 10-K annual reports, 100,000+ available
- Companies House (UK): Annual accounts
- SEBI (India): Annual reports of listed companies

Downloads the documents and saves them for processing by process_real_documents.py.

Output: data/seeds/real/*.txt (plain text of reports)

Usage:
  pip install requests
  python3 scripts/download_public_reports.py --source sec --count 100
"""

import json
import os
import sys
import time
import argparse
import requests
from pathlib import Path

OUTPUT_DIR = Path("data/seeds/real")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# SEC EDGAR - top companies by market cap
# These are public 10-K filings (annual reports)
# Includes US, Indian ADRs, UK ADRs, Canadian dual-listed (all file 10-K or 20-F with SEC)
SEC_COMPANIES = [
    # US Tech
    ("AAPL", "0000320193", "Apple"),
    ("MSFT", "0000789019", "Microsoft"),
    ("GOOGL", "0001652044", "Alphabet"),
    ("AMZN", "0001018724", "Amazon"),
    ("META", "0001326801", "Meta"),
    ("NVDA", "0001045810", "NVIDIA"),
    ("TSLA", "0001318605", "Tesla"),
    ("ORCL", "0001341439", "Oracle"),
    ("CRM", "0001108524", "Salesforce"),
    ("ADBE", "0000796343", "Adobe"),
    ("INTC", "0000050863", "Intel"),
    ("AMD", "0000002488", "AMD"),
    ("CSCO", "0000858877", "Cisco"),
    ("IBM", "0000051143", "IBM"),
    ("AVGO", "0001730168", "Broadcom"),
    ("QCOM", "0000804328", "Qualcomm"),
    ("NOW", "0001373715", "ServiceNow"),
    ("INTU", "0000896878", "Intuit"),
    ("NFLX", "0001065280", "Netflix"),
    ("PYPL", "0001633917", "PayPal"),
    ("UBER", "0001543151", "Uber"),
    ("ABNB", "0001559720", "Airbnb"),
    ("SPOT", "0001639920", "Spotify"),
    ("SHOP", "0001594805", "Shopify"),
    # US Finance
    ("JPM", "0000019617", "JPMorgan Chase"),
    ("BAC", "0000070858", "Bank of America"),
    ("WFC", "0000072971", "Wells Fargo"),
    ("GS", "0000886982", "Goldman Sachs"),
    ("MS", "0000895421", "Morgan Stanley"),
    ("V", "0001403161", "Visa"),
    ("MA", "0001141391", "Mastercard"),
    ("AXP", "0000004962", "American Express"),
    ("BLK", "0001364742", "BlackRock"),
    ("SCHW", "0000316709", "Charles Schwab"),
    ("C", "0000831001", "Citigroup"),
    ("USB", "0000036104", "US Bancorp"),
    # US Healthcare
    ("JNJ", "0000200406", "Johnson & Johnson"),
    ("PFE", "0000078003", "Pfizer"),
    ("UNH", "0000731766", "UnitedHealth"),
    ("ABBV", "0001551152", "AbbVie"),
    ("LLY", "0000059478", "Eli Lilly"),
    ("MRK", "0000310158", "Merck"),
    ("TMO", "0000097745", "Thermo Fisher"),
    ("DHR", "0000313616", "Danaher"),
    ("BMY", "0000014272", "Bristol-Myers Squibb"),
    ("AMGN", "0000318154", "Amgen"),
    # US Consumer
    ("WMT", "0000104169", "Walmart"),
    ("PG", "0000080424", "Procter & Gamble"),
    ("KO", "0000021344", "Coca-Cola"),
    ("PEP", "0000077476", "PepsiCo"),
    ("NKE", "0000320187", "Nike"),
    ("MCD", "0000063908", "McDonald's"),
    ("SBUX", "0000829224", "Starbucks"),
    ("DIS", "0001744489", "Disney"),
    ("CMCSA", "0001166691", "Comcast"),
    # US Industrial
    ("BA", "0000012927", "Boeing"),
    ("CAT", "0000018230", "Caterpillar"),
    ("GE", "0000040545", "General Electric"),
    ("HON", "0000773840", "Honeywell"),
    ("LMT", "0000936468", "Lockheed Martin"),
    ("RTX", "0000101829", "Raytheon"),
    ("GD", "0000040533", "General Dynamics"),
    ("DE", "0000315189", "John Deere"),
    ("MMM", "0000066740", "3M"),
    # US Energy
    ("XOM", "0000034088", "Exxon Mobil"),
    ("CVX", "0000093410", "Chevron"),
    ("COP", "0001163165", "ConocoPhillips"),
    ("SLB", "0000087347", "Schlumberger"),
    # US Telecom
    ("VZ", "0000732717", "Verizon"),
    ("T", "0000732717", "AT&T"),
    # US Transport
    ("UPS", "0001090727", "UPS"),
    ("FDX", "0001048911", "FedEx"),
    ("DAL", "0000027904", "Delta"),
    ("UAL", "0000100517", "United Airlines"),
    # US Retail
    ("HD", "0000354950", "Home Depot"),
    ("COST", "0000909832", "Costco"),
    ("TGT", "0000027419", "Target"),
    ("LOW", "0000060667", "Lowe's"),
    # Indian ADRs (file 20-F with SEC)
    ("INFY", "0001067491", "Infosys"),
    ("WIT", "0001123799", "Wipro"),
    ("HDB", "0001144967", "HDFC Bank"),
    ("IBN", "0001111759", "ICICI Bank"),
    ("RDY", "0001380006", "Dr Reddys"),
    ("TTM", "0001105005", "Tata Motors"),
    ("SIFY", "0001094324", "Sify Technologies"),
    # UK/European ADRs (file 20-F with SEC)
    ("BP", "0000313807", "BP"),
    ("SHEL", "0001306965", "Shell"),
    ("AZN", "0000901832", "AstraZeneca"),
    ("GSK", "0001131399", "GSK"),
    ("UL", "0000217167", "Unilever"),
    ("NVS", "0001114448", "Novartis"),
    ("SAP", "0001000184", "SAP"),
    ("SNY", "0001121404", "Sanofi"),
    ("VOD", "0000839923", "Vodafone"),
    ("DEO", "0000835403", "Diageo"),
    # Canadian dual-listed
    ("TD", "0000947263", "TD Bank"),
    ("RY", "0001000275", "Royal Bank of Canada"),
    ("BMO", "0000927971", "Bank of Montreal"),
    ("BNS", "0000009631", "Bank of Nova Scotia"),
    ("CNQ", "0000928054", "Canadian Natural Resources"),
    ("SU", "0000311337", "Suncor Energy"),
    ("ENB", "0000895728", "Enbridge"),
    ("CNI", "0000016868", "Canadian National Railway"),
    ("BCE", "0000718940", "BCE Inc"),
    ("MFC", "0001086888", "Manulife"),
]

USER_AGENT = "Rabbit Research research@reattend.ai"


def get_10k_filings(cik: str, max_filings: int = 1) -> list[dict]:
    """Get latest 10-K filings for a company."""
    cik_padded = cik.zfill(10)

    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        if not resp.ok:
            return []
        data = resp.json()

        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        accessions = recent.get("accessionNumber", [])
        dates = recent.get("filingDate", [])
        docs = recent.get("primaryDocument", [])

        filings = []
        for i, form in enumerate(forms):
            if form == "10-K" and len(filings) < max_filings:
                filings.append({
                    "accession": accessions[i].replace("-", ""),
                    "date": dates[i],
                    "document": docs[i],
                    "cik": cik,
                })
        return filings
    except Exception as e:
        print(f"  Error fetching filings: {e}")
        return []


def download_filing(cik: str, accession: str, document: str, company_name: str) -> str:
    """Download a 10-K filing and extract text."""
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/{document}"

    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=120)
        if not resp.ok:
            print(f"  HTTP {resp.status_code}")
            return ""

        html = resp.text

        # Strip HTML tags to get plain text
        import re
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'&lt;', '<', text)
        text = re.sub(r'&gt;', '>', text)
        text = re.sub(r'&#\d+;', ' ', text)
        text = re.sub(r'\s+', ' ', text)

        return text.strip()
    except Exception as e:
        print(f"  Error: {e}")
        return ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=40, help="Number of companies")
    parser.add_argument("--per-company", type=int, default=1, help="Filings per company")
    args = parser.parse_args()

    print(f"Downloading {args.count} companies x {args.per_company} filings from SEC EDGAR")
    print(f"Output: {OUTPUT_DIR}")

    success = 0
    failures = 0

    for ticker, cik, name in SEC_COMPANIES[:args.count]:
        print(f"\n{ticker} ({name})")

        filings = get_10k_filings(cik, args.per_company)
        if not filings:
            print(f"  No 10-K filings found")
            failures += 1
            continue

        for filing in filings:
            filename = OUTPUT_DIR / f"10k_{ticker}_{filing['date']}.txt"
            if filename.exists():
                print(f"  Already exists: {filename.name}")
                success += 1
                continue

            print(f"  Downloading 10-K {filing['date']}...")
            text = download_filing(
                filing["cik"],
                filing["accession"],
                filing["document"],
                name,
            )

            if text and len(text) > 5000:
                filename.write_text(text[:500000], encoding="utf-8")  # Cap at 500K chars
                size_kb = len(text) // 1024
                print(f"  Saved: {filename.name} ({size_kb}KB)")
                success += 1
            else:
                print(f"  FAILED (got {len(text)} chars)")
                failures += 1

            time.sleep(0.5)  # SEC rate limit

    print(f"\n{'='*60}")
    print(f"  Success: {success}, Failures: {failures}")
    print(f"  Files in: {OUTPUT_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
