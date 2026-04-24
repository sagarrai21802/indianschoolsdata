"""
Yellow Slate - Full School Scraper
Extracts school data from all cities.
"""

import asyncio
import json
import csv
import re
from urllib.parse import urljoin
from playwright.async_api import async_playwright
import pandas as pd


async def parse_school_text(text: str) -> dict:
    """Parse school details from card text."""
    if not text:
        return {"name": "", "board": "", "location": "", "fees": ""}
    
    # Split on newlines and filter empty
    lines = [l.strip() for l in text.split('\n') if l.strip() and l.strip() not in ['Enquire Now', 'Read more...', '']]
    
    data = {
        "name": "",
        "board": "",
        "location": "",
        "fees": ""
    }
    
    # Format: BOARD, NAME, LOCATION, FEES
    # Try to identify each field
    for i, line in enumerate(lines):
        # Board has slashes (e.g., CBSE/IB/IGCSE)
        if '/' in line and any(b in line.upper() for b in ['CBSE', 'IB', 'IGCSE', 'ICSE', 'CAMBRIDGE', 'STATE']):
            data["board"] = line
        # Fees start with ₹
        elif line.startswith('₹'):
            data["fees"] = line
        # Name is typically the longest text
        elif len(line) > 10 and not data["name"]:
            data["name"] = line
        # Location is short
        elif len(line) < 40 and data["name"] and not data["location"]:
            data["location"] = line
    
    return data


async def scrape_city(city: str, browser, max_pages: int = 5) -> list[dict]:
    """Scrape all schools for a city."""
    all_schools = []
    page = await browser.new_page()
    
    page_num = 1
    while page_num <= max_pages:
        # Build URL - try different pagination patterns
        if page_num == 1:
            url = f"https://yellowslate.com/schools/{city}"
        else:
            # Try common pagination patterns
            url = f"https://yellowslate.com/schools/{city}?page={page_num}"
        
        print(f"  [Page {page_num}] {url}")
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(4000)
            
            # Get all school links - use query_selector_all with JS
            school_links = await page.evaluate(f"""() => {{
                const links = Array.from(document.querySelectorAll('a[href*="/school/"]'));
                return links
                    .filter(a => a.href.includes('/school/{city}'))
                    .map(a => {{
                        return {{
                            href: a.href,
                            text: a.textContent?.trim() || ''
                        }};
                    }});
            }}""")
            
            if not school_links:
                print(f"    No schools found on page {page_num}")
                break
            
            # Deduplicate by URL
            seen_urls = set()
            for s in school_links:
                url = s.get('href', '')
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                
                # Parse the school data
                parsed = await parse_school_text(s.get('text', ''))
                parsed['url'] = url
                parsed['school_slug'] = url.split('/school/')[-1] if '/school/' in url else ''
                parsed['city'] = city
                
                if parsed['name']:
                    all_schools.append(parsed)
            
            print(f"    Found {len(school_links)} schools ({len(all_schools)} unique)")
            
            # Debug: show first parsed school
            if all_schools:
                print(f"    Sample: {all_schools[0]}")
            
        except Exception as e:
            print(f"    Error: {e}")
            break
        
        page_num += 1
        await asyncio.sleep(1)
    
    await page.close()
    return all_schools


async def main():
    CITIES = [
        "hyderabad", "bengaluru", "pune", "mumbai",
        "kolkata", "delhi", "chennai", "vizag",
        "noida", "gurugram", "faridabad"
    ]
    
    print("=" * 60)
    print(" Yellow Slate Full School Scraper")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        all_schools = []
        for city in CITIES[:3]:  # Start with first 3 cities
            print(f"\n[City] {city.upper()}")
            schools = await scrape_city(city, browser)
            all_schools.extend(schools)
            print(f"  Total so far: {len(all_schools)}")
            
            await asyncio.sleep(2)
        
        await browser.close()
    
    # Save to CSV
    if all_schools:
        # Deduplicate
        seen = set()
        unique = []
        for s in all_schools:
            key = s.get('url', '')
            if key not in seen:
                seen.add(key)
                unique.append(s)
        
        df = pd.DataFrame(unique)
        df.to_csv("yellowslate_schools.csv", index=False, encoding="utf-8-sig")
        
        print(f"\n{'='*60}")
        print(f"Total schools: {len(unique)}")
        print(f"Saved to yellowslate_schools.csv")
        print(f"\nSample data:")
        print(df.head(10).to_string())


if __name__ == "__main__":
    asyncio.run(main())