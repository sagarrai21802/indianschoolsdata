"""YellowSlate Scraper - Full pagination version."""

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
CHECKPOINT = "checkpoint_full.json"
RESULTS_DIR = "scraped_data"
os.makedirs(RESULTS_DIR, exist_ok=True)


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
    
    # Rating
    match = re.search(r'(\d+\.?\d*)/5\s*Rating', text)
    if match:
        data["rating"] = match.group(1)
    
    # Views
    match = re.search(r'([\d,]+)\s*Views', text)
    if match:
        data["views"] = match.group(1).replace(",", "")
    
    # Reviews
    match = re.search(r'([\d,]+)\s*Reviews', text)
    if match:
        data["reviews_count"] = match.group(1).replace(",", "")
    
    # Phone
    match = re.search(r'(\+\d{10,})', text)
    if match:
        data["phone"] = match.group(1)
    
    # Board
    match = re.search(r'[Bb]oard\s*:\s*([^\n]+)', text)
    if not match:
        match = re.search(r'(CBSE|IB|IGCSE|State Board|ICSE|Cambridge)[^,\n]*', text)
    if match:
        data["board"] = match.group(1).strip()
    
    # Established
    match = re.search(r'[Ss]ince\s*:\s*(\d{4})', text)
    if match:
        data["established"] = match.group(1)
    
    # Category
    match = re.search(r'[Cc]ategory\s*:\s*([^\n]+)', text)
    if match:
        data["category"] = match.group(1).strip()
    
    # Classes
    match = re.search(r'(Nursery\s*-\s*\d+|\d+\s*-\s*\d+)', text)
    if match:
        data["classes"] = match.group(1)
    
    # Gender
    if "Co-Education" in text:
        data["gender"] = "Co-Education"
    elif "Girls" in text:
        data["gender"] = "Girls"
    elif "Boys" in text:
        data["gender"] = "Boys"
    
    # Fees
    match = re.search(r'[Ff]ee\s*[Rr]ange\s*[:-]\s*[\u20b9₹]?\s*([\d,]+)\s*-\s*([\d,]+)', text)
    if match:
        data["fees_range"] = f"{match.group(1)}-{match.group(2)}"
    
    return data


async def get_all_slugs_with_scroll(city: str) -> list[str]:
    """Get all school slugs by scrolling through the city page."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = f"{BASE_URL}/schools/{city}"
        await page.goto(url, wait_until="networkidle", timeout=60000)
        
        print("  Scrolling to load all schools...")
        
        # Scroll patterns for infinite scroll
        last_count = 0
        no_new_content = 0
        max_scrolls = 30  # Increase for more schools
        
        for scroll_num in range(max_scrolls):
            # Scroll down
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
            
            # Check for loading spinner and wait
            try:
                spinner = await page.locator("[class*='spinner'], [class*='loading'], [class*='Skeleton']").count()
                if spinner > 0:
                    await asyncio.sleep(3)
            except:
                pass
            
            # Get current count
            current_count = await page.evaluate("""
                () => document.querySelectorAll('a[href^="/school/{city}/"]').length
            """.format(city=city))
            
            if current_count > last_count:
                print(f"    Scroll {scroll_num + 1}: {current_count} schools (was {last_count})")
                last_count = current_count
                no_new_content = 0
            else:
                no_new_content += 1
                if no_new_content >= 3:  # Stop if 3 scrolls with no new content
                    print(f"    No more content after {scroll_num + 1} scrolls")
                    break
        
        # Get all links
        links = await page.evaluate(f"""
            () => {{
                const anchors = Array.from(document.querySelectorAll('a[href^="/school/{city}/"]'));
                return [...new Set(anchors.map(a => a.href))];
            }}
        """)
        
        await browser.close()
        return [l.replace(BASE_URL, "") for l in links]


async def scrape_school(page, slug: str, city: str) -> dict:
    """Scrape a single school's details."""
    url = f"{BASE_URL}{slug}"
    data = {"slug": slug, "url": url, "city": city}
    
    await page.goto(url, wait_until="networkidle", timeout=30000)
    
    # Name
    try:
        data["name"] = await page.locator("h1").first.inner_text()
    except:
        pass
    
    # Get page text
    try:
        full_text = await page.locator("body").inner_text()
        parsed = parse_school_text(full_text)
        data.update(parsed)
    except:
        pass
    
    # Extract locality from name
    if data.get("name"):
        match = re.search(r'-\s*([^-\n]+)\s*$', data["name"])
        if match:
            data["locality"] = match.group(1).strip()
    
    # Images
    try:
        imgs = await page.locator("img").all()
        data["images"] = []
        for img in imgs[:20]:
            src = await img.get_attribute("src")
            if src and "digitaloceanspaces" in src:
                data["images"].append(src)
    except:
        pass
    
    return data


def load_checkpoint(city: str) -> tuple[list, set]:
    """Load checkpoint and return (results, urls_set)."""
    if os.path.exists(CHECKPOINT):
        with open(CHECKPOINT, "r", encoding="utf-8") as f:
            data = json.load(f)
            results = data.get(city, [])
            urls = set([s.get("slug") for s in results])
            return results, urls
    return [], set()


def save_checkpoint(all_data: dict):
    """Save all checkpoints."""
    with open(CHECKPOINT, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)


def save_results(city: str, results: list):
    """Save results to files."""
    if not results:
        return
    
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON
    json_path = f"{RESULTS_DIR}/full_{city}_{ts}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # CSV
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
        csv_path = f"{RESULTS_DIR}/full_{city}_{ts}.csv"
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=flat[0].keys())
            writer.writeheader()
            writer.writerows(flat)
    
    print(f"  Saved: {len(results)} schools to {json_path}")


async def scrape_city(city: str, batch_save: int = 25):
    """Scrape all schools for a city."""
    print(f"\n{'='*60}")
    print(f" Scraping: {city.upper()}")
    print(f"{'='*60}")
    
    # Phase 1: Get all slugs
    print("\n[Phase 1] Getting school slugs...")
    slugs = await get_all_slugs_with_scroll(city)
    print(f"  Total slugs found: {len(slugs)}")
    
    if not slugs:
        print("  No slugs found!")
        return []
    
    # Load checkpoint
    results, scraped_urls = load_checkpoint(city)
    pending = [s for s in slugs if s not in scraped_urls]
    print(f"  Already scraped: {len(results)} | Pending: {len(pending)}")
    
    if not pending:
        print("  All schools already scraped!")
        return results
    
    # Phase 2: Scrape details
    print(f"\n[Phase 2] Scraping {len(pending)} schools...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        for i, slug in enumerate(pending):
            print(f"  [{i+1}/{len(pending)}] {slug[:60]}...")
            try:
                school = await scrape_school(page, slug, city)
                results.append(school)
                
                # Save checkpoint
                if (i + 1) % batch_save == 0:
                    all_data = {}
                    if os.path.exists(CHECKPOINT):
                        with open(CHECKPOINT, "r", encoding="utf-8") as f:
                            all_data = json.load(f)
                    all_data[city] = results
                    save_checkpoint(all_data)
                    print(f"    Checkpoint: {len(results)} schools")
                
                await asyncio.sleep(1.5)
                
            except Exception as e:
                print(f"    Error: {e}")
        
        await browser.close()
    
    # Final save
    all_data = {}
    if os.path.exists(CHECKPOINT):
        with open(CHECKPOINT, "r", encoding="utf-8") as f:
            all_data = json.load(f)
    all_data[city] = results
    save_checkpoint(all_data)
    save_results(city, results)
    
    print(f"\n  Total: {len(results)} schools scraped")
    return results


async def main():
    print("=" * 60)
    print(" YellowSlate Full Scraper - All Schools")
    print("=" * 60)
    
    # Target cities
    cities = ["hyderabad", "bengaluru", "pune", "mumbai", "kolkata", "delhi", "chennai"]
    
    # Scrape first city to test
    test_city = "hyderabad"
    
    print(f"\nStarting with: {test_city}")
    await scrape_city(test_city, batch_save=25)
    
    print("\n" + "=" * 60)
    print(" Done!")


if __name__ == "__main__":
    asyncio.run(main())