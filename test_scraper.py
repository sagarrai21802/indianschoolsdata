"""
YellowSlate Scraper - Quick Test Version
"""

import asyncio
import json
from playwright.async_api import async_playwright

BASE_URL = "https://yellowslate.com"

async def get_school_slugs_simple(city: str) -> list[str]:
    """Get school slugs using simple request + beautifulsoup."""
    import requests
    from bs4 import BeautifulSoup
    
    url = f"{BASE_URL}/schools/{city}"
    headers = {"User-Agent": "Mozilla/5.0"}
    
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


async def scrape_one_school(page, slug: str):
    """Scrape a single school."""
    url = f"{BASE_URL}{slug}"
    data = {"slug": slug, "url": url}
    
    await page.goto(url, wait_until="networkidle", timeout=30000)
    
    # Get h1
    try:
        data["name"] = await page.locator("h1").first.inner_text()
    except:
        data["name"] = None
    
    # Get all text
    try:
        data["text"] = await page.locator("body").inner_text()
    except:
        data["text"] = None
    
    # Get images
    try:
        imgs = await page.locator("img").all()
        data["img_count"] = len(imgs)
    except:
        data["img_count"] = 0
    
    return data


async def main():
    city = "hyderabad"
    
    print("=" * 50)
    print(" Quick Test Scraper")
    print("=" * 50)
    
    # Phase 1: Get slugs
    print("\n[Phase 1] Getting school slugs...")
    slugs = await get_school_slugs_simple(city)
    
    # Take first 3 for testing
    test_slugs = slugs[:3]
    print(f"Testing with {len(test_slugs)} schools: {test_slugs}")
    
    # Phase 2: Scrape details
    print("\n[Phase 2] Scraping details...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        results = []
        for i, slug in enumerate(test_slugs):
            print(f"  [{i+1}] {slug}")
            try:
                data = await scrape_one_school(page, slug)
                results.append(data)
                print(f"      Name: {data.get('name', 'N/A')}")
                print(f"      Images: {data.get('img_count', 0)}")
            except Exception as e:
                print(f"      ERROR: {e}")
            
            await asyncio.sleep(1)
        
        await browser.close()
    
    # Save results
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nSaved {len(results)} results to test_results.json")
    print("\nSample first result:")
    if results:
        print(json.dumps(results[0], indent=2, ensure_ascii=False)[:1000])


if __name__ == "__main__":
    asyncio.run(main())