"""YellowSlate Production Scraper - Extracts complete school data."""

import asyncio
import json
import csv
import re
import os
from datetime import datetime
from playwright.async_api import async_playwright
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://yellowslate.com"
CHECKPOINT = "checkpoint.json"
RESULTS_DIR = "scraped_data"
os.makedirs(RESULTS_DIR, exist_ok=True)


def get_school_slugs(city: str) -> list[str]:
    """Phase 1: Get all school slugs from city page using requests."""
    url = f"{BASE_URL}/schools/{city}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    print(f"Fetching: {url}")
    res = requests.get(url, headers=headers, timeout=30)
    soup = BeautifulSoup(res.text, "html.parser")
    
    slugs = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith(f"/school/{city}/"):
            slugs.add(href)
    
    print(f"Found {len(slugs)} slugs")
    return list(slugs)


def parse_school_text(text: str) -> dict:
    """Parse school details from the raw text."""
    data = {
        "rating": None,
        "views": None,
        "reviews_count": None,
        "phone": None,
        "locality": None,
        "board": None,
        "established": None,
        "category": None,
        "classes": None,
        "gender": None,
        "fees_range": None,
        "about": None,
    }
    
    # Rating: 4.0/5 or similar
    match = re.search(r'(\d+\.?\d*)/5\s*Rating', text)
    if match:
        data["rating"] = match.group(1)
    
    # Views: 15142 Views
    match = re.search(r'([\d,]+)\s*Views', text)
    if match:
        data["views"] = match.group(1).replace(",", "")
    
    # Reviews: 105 Reviews
    match = re.search(r'([\d,]+)\s*Reviews', text)
    if match:
        data["reviews_count"] = match.group(1).replace(",", "")
    
    # Phone: +919513238818
    match = re.search(r'(\+\d{10,})', text)
    if match:
        data["phone"] = match.group(1)
    
    # Board: CBSE, Cambridge IGCSE or Board : CBSE
    match = re.search(r'[Bb]oard\s*:\s*([^\n]+)', text)
    if not match:
        match = re.search(r'(CBSE|IB|IGCSE|State Board|ICSE|Cambridge)[^,\n]*', text)
    if match:
        data["board"] = match.group(1).strip()
    
    # Established: Since : 2012
    match = re.search(r'[Ss]ince\s*:\s*(\d{4})', text)
    if match:
        data["established"] = match.group(1)
    
    # Category: Category : International Schools
    match = re.search(r'[Cc]ategory\s*:\s*([^\n]+)', text)
    if match:
        data["category"] = match.group(1).strip()
    
    # Classes: Nursery - 12 or 1 - 12
    match = re.search(r'(Nursery\s*-\s*\d+|\d+\s*-\s*\d+)', text)
    if match:
        data["classes"] = match.group(1)
    
    # Gender: Co-Education / Boys / Girls
    if "Co-Education" in text:
        data["gender"] = "Co-Education"
    elif "Girls" in text:
        data["gender"] = "Girls"
    elif "Boys" in text:
        data["gender"] = "Boys"
    
    # Fees: CBSE Fee Range :- 120,000 - 170,000
    match = re.search(r'[Ff]ee\s*[Rr]ange\s*[:-]\s*[\u20b9₹]?\s*([\d,]+)\s*-\s*([\d,]+)', text)
    if match:
        data["fees_range"] = f"{match.group(1)}-{match.group(2)}"
    
    # About section - between "About" and "Enquire Now" or "Show more"
    match = re.search(r'[Aa]bout\s+[^:\n]+([^\n]+(?:\n(?!\n|Show more|Enquire)).*)', text, re.DOTALL)
    if match:
        about = match.group(0)
        # Clean up
        about = re.sub(r'.*About\s+', '', about)
        about = re.sub(r'\nShow more.*', '', about)
        about = re.sub(r'\nEnquire Now.*', '', about)
        data["about"] = about.strip()[:500]
    
    return data


async def scrape_school(page, slug: str, city: str) -> dict:
    """Scrape a single school's details."""
    url = f"{BASE_URL}{slug}"
    data = {
        "slug": slug,
        "url": url,
        "city": city,
        "name": None,
        "name_with_locality": None,
    }
    
    await page.goto(url, wait_until="networkidle", timeout=30000)
    
    # Name
    try:
        data["name"] = await page.locator("h1").first.inner_text()
        data["name_with_locality"] = data["name"]
    except:
        pass
    
    # Get all page text
    try:
        full_text = await page.locator("body").inner_text()
        parsed = parse_school_text(full_text)
        data.update(parsed)
    except:
        pass
    
    # Extract locality from name if available (e.g., "School - Locality")
    if data.get("name"):
        match = re.search(r'-\s*([^-\n]+)\s*$', data["name"])
        if match:
            data["locality"] = match.group(1).strip()
    
    # Get images (all images on the page)
    try:
        imgs = await page.locator("img").all()
        data["images"] = []
        for img in imgs[:20]:  # Limit to 20 images
            src = await img.get_attribute("src")
            if src and "digitaloceanspaces" in src:
                data["images"].append(src)
    except:
        pass
    
    return data


async def get_slugs_with_playwright(city: str) -> list[str]:
    """Get slugs with scroll pagination using Playwright."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = f"{BASE_URL}/schools/{city}"
        await page.goto(url, wait_until="networkidle", timeout=60000)
        
        # Scroll to load all items
        for i in range(5):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
        
        # Get all school links
        links = await page.evaluate(f"""
            () => {{
                const anchors = Array.from(document.querySelectorAll('a[href^="/school/{city}/"]'));
                return [...new Set(anchors.map(a => a.href))];
            }}
        """)
        
        await browser.close()
        return [l.replace(BASE_URL, "") for l in links]


def load_checkpoint(city: str) -> list[dict]:
    """Load checkpoint for a city."""
    if os.path.exists(CHECKPOINT):
        with open(CHECKPOINT, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get(city, [])
    return []


def save_checkpoint(city: str, results: list):
    """Save checkpoint for a city."""
    data = {}
    if os.path.exists(CHECKPOINT):
        with open(CHECKPOINT, "r", encoding="utf-8") as f:
            data = json.load(f)
    
    data[city] = results
    
    with open(CHECKPOINT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_results(city: str, results: list, batch: int = None):
    """Save results to JSON and CSV."""
    if not results:
        return
    
    suffix = f"_batch{batch}" if batch else ""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save JSON
    json_path = f"{RESULTS_DIR}/schools_{city}_{ts}{suffix}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # Save CSV (flattened)
    flat = []
    for r in results:
        row = {}
        for k, v in r.items():
            if isinstance(v, list):
                row[k] = " | ".join(str(x) for x in v) if v else ""
            elif v is None:
                row[k] = ""
            else:
                row[k] = str(v)
        flat.append(row)
    
    if flat:
        csv_path = f"{RESULTS_DIR}/schools_{city}_{ts}{suffix}.csv"
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=flat[0].keys())
            writer.writeheader()
            writer.writerows(flat)
        print(f"Saved: {json_path}")
        print(f"Saved: {csv_path}")


async def scrape_city(city: str, limit: int = None):
    """Scrape all schools for a city."""
    print(f"\n{'='*60}")
    print(f" Scraping: {city.upper()}")
    print(f"{'='*60}")
    
    # Phase 1: Get slugs
    print("\n[Phase 1] Getting school slugs...")
    try:
        slugs = await get_slugs_with_playwright(city)
    except Exception as e:
        print(f"Playwright failed: {e}, using requests...")
        slugs = get_school_slugs(city)
    
    if not slugs:
        print("No slugs found!")
        return []
    
    print(f"Total: {len(slugs)} schools")
    if limit:
        slugs = slugs[:limit]
        print(f"Limited to: {limit}")
    
    # Load checkpoint
    scraped = load_checkpoint(city)
    scraped_urls = set([s.get("slug") for s in scraped])
    
    pending = [s for s in slugs if s not in scraped_urls]
    print(f"Already scraped: {len(scraped)} | Pending: {len(pending)}")
    
    # Phase 2: Scrape details
    print("\n[Phase 2] Scraping schools...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        results = list(scraped)
        
        for i, slug in enumerate(pending):
            print(f"  [{i+1}/{len(pending)}] {slug}")
            try:
                school = await scrape_school(page, slug, city)
                results.append(school)
                
                # Save checkpoint every 10
                if (i + 1) % 10 == 0:
                    save_checkpoint(city, results)
                    print(f"    Checkpoint saved")
                
                await asyncio.sleep(1.5)
                
            except Exception as e:
                print(f"    Error: {e}")
        
        await browser.close()
    
    # Final save
    save_checkpoint(city, results)
    save_results(city, results)
    
    print(f"\nTotal scraped: {len(results)}")
    return results


async def main():
    print("=" * 60)
    print(" YellowSlate Production Scraper")
    print("=" * 60)
    
    cities = ["hyderabad", "bengaluru", "pune", "mumbai", "kolkata", "delhi", "chennai"]
    
    # Scrape all cities with limits
    for city in cities:
        try:
            print(f"\n\n{'#'*50}")
            print(f" Starting: {city}")
            print(f"{'#'*50}")
            await scrape_city(city, limit=None)
            await asyncio.sleep(5)  # Delay between cities
        except Exception as e:
            print(f"Error with {city}: {e}")


if __name__ == "__main__":
    asyncio.run(main())