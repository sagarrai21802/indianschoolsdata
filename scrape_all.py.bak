"""YellowSlate Complete Scraper - Hierarchical City/School Crawler."""

import asyncio
import json
import csv
import re
import os
from datetime import datetime
from playwright.async_api import async_playwright

BASE_URL = "https://yellowslate.com"
RESULTS_DIR = "scraped_data"
os.makedirs(RESULTS_DIR, exist_ok=True)


# ---------- helpers ----------
def parse_school_text(text: str) -> dict:
    if not text:
        return {}
    data = {}
    # rating 4.0/5
    if m := re.search(r'(\d+\.?\d*)/5\s*Rating', text):
        data["rating"] = m.group(1)
    # 15142 Views / 105 Reviews
    if m := re.search(r'([\d,]+)\s*Views', text):
        data["views"] = m.group(1).replace(",", "")
    if m := re.search(r'([\d,]+)\s*Reviews', text):
        data["reviews_count"] = m.group(1).replace(",", "")
    # +919513238818
    if m := re.search(r'(\+\d{10,})', text):
        data["phone"] = m.group(1)
    # Board : CBSE, IB, IGCSE
    if m := re.search(r'[Bb]oard\s*:\s*([^\n]+)', text) or re.search(r'(CBSE|IB|IGCSE|State Board|ICSE|Cambridge)[^,\n]*', text):
        data["board"] = m.group(1).strip()
    # Since : 2012
    if m := re.search(r'[Ss]ince\s*:\s*(\d{4})', text):
        data["established"] = m.group(1)
    # Category : International Schools
    if m := re.search(r'[Cc]ategory\s*:\s*([^\n]+)', text):
        data["category"] = m.group(1).strip()
    # Nursery - 12
    if m := re.search(r'(Nursery\s*-\s*\d+|\d+\s*-\s*\d+)', text):
        data["classes"] = m.group(1)
    # Co-Education / Girls / Boys
    if "Co-Education" in text:
        data["gender"] = "Co-Education"
    elif "Girls" in text:
        data["gender"] = "Girls"
    elif "Boys" in text:
        data["gender"] = "Boys"
    # fee range
    if m := re.search(r'[Ff]ee\s*[Rr]ange\s*[:-]\s*[\u20b9₹]?\s*([\d,]+)\s*-\s*([\d,]+)', text):
        data["fees_range"] = f"{m.group(1)}-{m.group(2)}"
    return data


async def collect_city_slugs(city: str) -> list[str]:
    """Collect all unique school slugs for a given city with scroll pagination."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        url = f"{BASE_URL}/schools/{city}"
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
        except:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

        # Scroll to load all school entries
        for _ in range(10):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1.5)

        slugs = await page.evaluate(f"""
            () => {{
                const links = Array.from(document.querySelectorAll('a[href^="/school/{city}/"]'));
                return [...new Set(links.map(a => a.getAttribute('href')))].filter(h => h);
            }}
        """)

        await browser.close()
        return slugs


async def scrape_school(page, slug: str, city: str) -> dict:
    url = f"{BASE_URL}{slug}"
    data = {"city": city, "slug": slug, "url": url}

    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
    except:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)

    # name h1
    try:
        data["name"] = await page.locator("h1").first.inner_text()
    except:
        pass

    # description text
    try:
        full_text = await page.locator("body").inner_text()
        parsed = parse_school_text(full_text)
        data.update(parsed)
    except:
        pass

    # locality from name if pattern "Name - Locality"
    locality = None
    if data.get("name"):
        if m := re.search(r'-\s*([^\n]+)\s*$', data["name"]):
            locality = m.group(1).strip()
    if locality and not data.get("locality"):
        data["locality"] = locality

    # images from DigitalOcean CDN
    try:
        imgs = await page.locator("img").all()
        data["images"] = [await img.get_attribute("src") for img in imgs if "digitaloceanspaces" in (await img.get_attribute("src") or "")]
    except:
        pass

    # fallback raw HTML for complex parsing (if fields missing)
    if not data.get("rating"):
        try:
            html = await page.content()
            if "schools" in html.lower():
                data["raw_html_fallback"] = True
        except:
            pass

    return data


def save_checkpoint(city: str, results: list):
    with open(os.path.join(RESULTS_DIR, f"checkpoint_{city}.json"), "w", encoding="utf-8") as f:
        json.dump({city: results}, f, ensure_ascii=False, indent=2)


def save_city_results(city: str, results: list):
    if not results:
        return
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # JSON
    jpath = os.path.join(RESULTS_DIR, f"{city}_{ts}.json")
    with open(jpath, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # CSV flatten
    flat = []
    for r in results:
        row = {"city": city}
        for k, v in r.items():
            if isinstance(v, list):
                row[k] = " | ".join(str(x) for x in v) if v else ""
            elif v is None:
                row[k] = ""
            else:
                row[k] = str(v)
        flat.append(row)

    if flat:
        keys = flat[0].keys()
        cpath = os.path.join(RESULTS_DIR, f"{city}_{ts}.csv")
        with open(cpath, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(flat)

    print(f"  [{city}] saved {len(results)} schools")


async def process_city(city: str):
    print(f"\n{'='*50}")
    print(f" Scraping: {city.upper()}")
    print(f"{'='*50}")

    # Phase 1: collect slugs
    print("  [1/2] Collecting school slugs...")
    slugs = await collect_city_slugs(city)
    print(f"    Found {len(slugs)} unique school pages")

    if not slugs:
        return []

    # checkpoint resume
    city_checkpoint = os.path.join(RESULTS_DIR, f"checkpoint_{city}.json")
    scraped = []
    scraped_urls = set()
    if os.path.exists(city_checkpoint):
        with open(city_checkpoint, "r", encoding="utf-8") as f:
            sc = json.load(f)
            scraped = sc.get(city, [])
        scraped_urls = set([s.get("slug") for s in scraped])
    print(f"    Already scraped: {len(scraped)} | Pending: {len(slugs) - len(scraped_urls)}")

    pending = [s for s in slugs if s not in scraped_urls]
    if not pending:
        return scraped

    # Phase 2: detailed scrape
    print(f"  [2/2] Scraping {len(pending)} schools...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for i, slug in enumerate(pending):
            prefix = f"  [{i+1}/{len(pending)}]"
            try:
                school = await scrape_school(page, slug, city)
                scraped.append(school)
                print(f"    {prefix} {school.get('name','N/A')[:40]}")

                if (i + 1) % 10 == 0:
                    save_checkpoint(city, scraped)
            except Exception as e:
                print(f"    {prefix} ERROR: {e}")

            await asyncio.sleep(1.3)  # gentle rate limit

        await browser.close()

    save_checkpoint(city, scraped)
    save_city_results(city, scraped)
    return scraped


async def main():
    # Read cities from file
    cities = []
    try:
        with open('cities_to_scrape.txt', 'r') as f:
            cities = [line.strip() for line in f if line.strip()]
        print(f"Loaded {len(cities)} cities from cities_to_scrape.txt")
    except FileNotFoundError:
        print("cities_to_scrape.txt not found, using default cities")
        cities = [
            "hyderabad", "bengaluru", "pune", "mumbai",
            "kolkata", "delhi", "chennai", "vizag",
            "ahmedabad", "jaipur", "chandigarh", "kochi",
            "lucknow", "noida", "gurugram", "surat", "faridabad"
        ]

    print("=" * 60)
    print(" YellowSlate Full Hierarchical Crawler")
    print("=" * 60)

    all_results = {}
    for city in cities:
        try:
            schools = await process_city(city)
            all_results[city] = schools
            print(f"  DONE: {city} -> {len(schools)} schools")
        except Exception as e:
            print(f"  FAILED {city}: {e}")
            all_results[city] = []

    # final merge + save
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    merge_path = os.path.join(RESULTS_DIR, f"all_{ts}.json")
    with open(merge_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    merge_path_csv = os.path.join(RESULTS_DIR, f"all_{ts}.csv")
    flat = []
    for city, schools in all_results.items():
        for s in schools:
            row = {"city": city}
            for k, v in s.items():
                if isinstance(v, list):
                    row[k] = " | ".join(str(x) for x in v) if v else ""
                elif v is None:
                    row[k] = ""
                else:
                    row[k] = str(v)
            flat.append(row)

    with open(merge_path_csv, "w", newline="", encoding="utf-8-sig") as f:
        keys = flat[0].keys() if flat else []
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(flat)

    print(f"\n{'='*60}")
    print(f" TOTAL SCHOOLS SCRAPED: {len(flat)}")
    print(f" JSON: {merge_path}")
    print(f" CSV:  {merge_path_csv}")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())