"""YellowSlate Scraper - Remaining Cities."""

import asyncio
import json
import csv
import re
import os
from datetime import datetime
from playwright.async_api import async_playwright

BASE_URL = "https://yellowslate.com"
CHECKPOINT = "checkpoint_remaining.json"
RESULTS_DIR = "scraped_data"
os.makedirs(RESULTS_DIR, exist_ok=True)


def parse_school_text(text: str) -> dict:
    data = {
        "rating": None, "views": None, "reviews_count": None,
        "phone": None, "locality": None, "board": None,
        "established": None, "category": None, "classes": None,
        "gender": None, "fees_range": None, "about": None,
    }
    
    if m := re.search(r'(\d+\.?\d*)/5\s*Rating', text):
        data["rating"] = m.group(1)
    if m := re.search(r'([\d,]+)\s*Views', text):
        data["views"] = m.group(1).replace(",", "")
    if m := re.search(r'([\d,]+)\s*Reviews', text):
        data["reviews_count"] = m.group(1).replace(",", "")
    if m := re.search(r'(\+\d{10,})', text):
        data["phone"] = m.group(1)
    if m := re.search(r'[Bb]oard\s*:\s*([^\n]+)', text) or re.search(r'(CBSE|IB|IGCSE|State Board|ICSE|Cambridge)[^,\n]*', text):
        data["board"] = m.group(1).strip()
    if m := re.search(r'[Ss]ince\s*:\s*(\d{4})', text):
        data["established"] = m.group(1)
    if m := re.search(r'[Cc]ategory\s*:\s*([^\n]+)', text):
        data["category"] = m.group(1).strip()
    if m := re.search(r'(Nursery\s*-\s*\d+|\d+\s*-\s*\d+)', text):
        data["classes"] = m.group(1)
    if "Co-Education" in text: data["gender"] = "Co-Education"
    elif "Girls" in text: data["gender"] = "Girls"
    elif "Boys" in text: data["gender"] = "Boys"
    if m := re.search(r'[Ff]ee\s*[Rr]ange\s*[:-]\s*[\u20b9₹]?\s*([\d,]+)\s*-\s*([\d,]+)', text):
        data["fees_range"] = f"{m.group(1)}-{m.group(2)}"
    
    return data


async def get_all_slugs(city: str) -> list[str]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = f"{BASE_URL}/schools/{city}"
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
        except:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        all_slugs = {}
        
        for scroll_num in range(10):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1.5)
            
            slugs = await page.evaluate(f"""() => {{
                const links = Array.from(document.querySelectorAll('a[href^="/school/{city}/"]'));
                return links.map(a => a.getAttribute('href')).filter(h => h);
            }}""")
            
            for slug in slugs:
                if slug.startswith(f"/school/{city}/"):
                    all_slugs[slug] = True
            
            if scroll_num == 0:
                print(f"    Found: {len(all_slugs)} schools")
            
            if scroll_num >= 2:
                break
        
        await browser.close()
        return list(all_slugs.keys())


async def scrape_school(page, slug: str, city: str) -> dict:
    url = f"{BASE_URL}{slug}"
    data = {"slug": slug, "url": url, "city": city}
    
    try:
        await page.goto(url, wait_until="networkidle", timeout=25000)
    except:
        await page.goto(url, wait_until="domcontentloaded", timeout=25000)
    
    try:
        data["name"] = await page.locator("h1").first.inner_text()
    except:
        pass
    
    try:
        full_text = await page.locator("body").inner_text()
        parsed = parse_school_text(full_text)
        data.update(parsed)
    except:
        pass
    
    if data.get("name"):
        if m := re.search(r'-\s*([^-\n]+)\s*$', data["name"]):
            data["locality"] = m.group(1).strip()
    
    try:
        imgs = await page.locator("img").all()
        data["images"] = [await img.get_attribute("src") for img in imgs[:15] if "digitaloceanspaces" in (await img.get_attribute("src") or "")]
    except:
        pass
    
    return data


def save_checkpoint(data: dict):
    with open(CHECKPOINT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_results(city: str, results: list):
    if not results:
        return
    
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    json_path = f"{RESULTS_DIR}/rem_{city}_{ts}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    flat = []
    for r in results:
        row = {k: " | ".join(str(x) for x in v) if isinstance(v, list) else (v or "") for k, v in r.items()}
        flat.append(row)
    
    if flat:
        csv_path = f"{RESULTS_DIR}/rem_{city}_{ts}.csv"
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=flat[0].keys())
            writer.writeheader()
            writer.writerows(flat)
    
    print(f"  Saved: {len(results)} schools")


async def scrape_city(city: str):
    print(f"\n=== {city.upper()} ===")
    
    slugs = await get_all_slugs(city)
    print(f"  Total: {len(slugs)}")
    
    if not slugs:
        return []
    
    checkpoint = {}
    if os.path.exists(CHECKPOINT):
        with open(CHECKPOINT, "r", encoding="utf-8") as f:
            checkpoint = json.load(f)
    
    scraped = checkpoint.get(city, [])
    scraped_urls = set([s.get("slug") for s in scraped])
    pending = [s for s in slugs if s not in scraped_urls]
    
    print(f"  Pending: {len(pending)}")
    
    if not pending:
        return scraped
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        for i, slug in enumerate(pending):
            print(f"  [{i+1}/{len(pending)}] ", end="", flush=True)
            try:
                school = await scrape_school(page, slug, city)
                scraped.append(school)
                print(f"{school.get('name', 'N/A')[:30]}")
                
                if (i + 1) % 10 == 0:
                    checkpoint[city] = scraped
                    save_checkpoint(checkpoint)
                
                await asyncio.sleep(1.2)
            except Exception as e:
                print(f"Error: {e}")
        
        await browser.close()
    
    checkpoint[city] = scraped
    save_checkpoint(checkpoint)
    save_results(city, scraped)
    
    print(f"  Done: {len(scraped)} schools")
    return scraped


async def main():
    cities = ["jaipur", "chandigarh", "kochi", "lucknow", "surat"]
    
    for city in cities:
        try:
            await scrape_city(city)
            await asyncio.sleep(2)
        except Exception as e:
            print(f"Error: {city} - {e}")
    
    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())