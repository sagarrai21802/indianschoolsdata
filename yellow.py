"""
Yellow Slate School Scraper
============================
Scrapes school listings from yellowslate.com using Playwright.
Intercepts the internal API calls the Next.js frontend makes,
then hits those endpoints directly for all cities/pages.

Install:
    pip install playwright pandas
    playwright install chromium
"""

import asyncio
import json
import csv
import time
import re
from urllib.parse import urljoin, urlparse, parse_qs
from playwright.async_api import async_playwright
import pandas as pd


# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
BASE_URL = "https://yellowslate.com"

# Cities available on Yellow Slate
CITIES = [
    "hyderabad", "bengaluru", "pune", "mumbai",
    "kolkata", "delhi", "chennai", "vizag",
    "noida", "gurugram", "faridabad"
]

# If you only want specific cities, uncomment and edit:
# CITIES = ["hyderabad", "delhi"]

OUTPUT_FILE = "yellowslate_schools.csv"
INTERCEPTED_API_FILE = "intercepted_api_calls.json"


# ──────────────────────────────────────────────
# STEP 1 — INTERCEPT THE INTERNAL API
# Run this once to discover what API endpoint the site calls
# ──────────────────────────────────────────────
async def intercept_api_calls(city: str = "hyderabad") -> list[dict]:
    """
    Opens the school listing page in a real browser,
    intercepts all XHR/fetch calls, and logs any that look like
    school data API calls.
    """
    api_calls = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Intercept all network requests
        async def handle_request(request):
            url = request.url
            # Look for API calls (usually /api/ or external data endpoints)
            if any(kw in url for kw in ["/api/", "graphql", "schools", ".json"]):
                if "yellowslate.com" in url or "_next/data" in url:
                    api_calls.append({
                        "url": url,
                        "method": request.method,
                        "headers": dict(request.headers),
                    })

        async def handle_response(response):
            url = response.url
            # Capture responses from likely data endpoints
            if any(kw in url for kw in ["/api/", "_next/data"]) and "yellowslate.com" in url:
                try:
                    content_type = response.headers.get("content-type", "")
                    if "json" in content_type:
                        body = await response.json()
                        api_calls.append({
                            "url": url,
                            "method": "RESPONSE",
                            "body_preview": str(body)[:500],
                        })
                        print(f"  ✅ Captured API response: {url}")
                        print(f"     Preview: {str(body)[:200]}")
                except Exception:
                    pass

        page.on("request", handle_request)
        page.on("response", handle_response)

        target_url = f"{BASE_URL}/schools/{city}"
        print(f"Opening: {target_url}")
        await page.goto(target_url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)  # Wait for dynamic content

        # Also check Next.js data URLs (Next.js fetches /_next/data/... for SSG/SSR pages)
        print("\n📡 All intercepted API-like calls:")
        for call in api_calls:
            print(f"  {call.get('method', '')} → {call.get('url', '')}")

        await browser.close()

    return api_calls


# ──────────────────────────────────────────────
# STEP 2 — SCRAPE SCHOOL DATA FROM RENDERED PAGE
# If we can't find a clean API, extract from rendered HTML
# ──────────────────────────────────────────────
async def scrape_schools_from_page(page, url: str) -> list[dict]:
    """
    Extracts school cards from a rendered listing page.
    Adjust the selectors based on what you see in DevTools.
    """
    await page.goto(url, wait_until="networkidle", timeout=30000)
    await page.wait_for_timeout(2000)

    schools = []

    # Try to find school cards — inspect yellowslate.com to confirm selectors
    # Common patterns for Next.js school listing sites:
    school_cards = await page.query_selector_all(
        "[class*='school-card'], [class*='SchoolCard'], "
        "[class*='school_card'], [class*='card'], "
        "article, [data-testid*='school']"
    )

    if not school_cards:
        print(f"  ⚠️  No school cards found with standard selectors on {url}")
        print("     → Open the page in Chrome DevTools and inspect the school card HTML")
        print("     → Then update the selectors in this function")
        return []

    for card in school_cards:
        school = {}
        try:
            # School name
            name_el = await card.query_selector("h2, h3, h4, [class*='name'], [class*='title']")
            if name_el:
                school["name"] = (await name_el.inner_text()).strip()

            # Location
            loc_el = await card.query_selector("[class*='location'], [class*='address'], [class*='area']")
            if loc_el:
                school["location"] = (await loc_el.inner_text()).strip()

            # Board / curriculum
            board_el = await card.query_selector("[class*='board'], [class*='curriculum']")
            if board_el:
                school["board"] = (await board_el.inner_text()).strip()

            # Fee
            fee_el = await card.query_selector("[class*='fee'], [class*='Fee']")
            if fee_el:
                school["fee"] = (await fee_el.inner_text()).strip()

            # School detail page link
            link_el = await card.query_selector("a")
            if link_el:
                href = await link_el.get_attribute("href")
                school["url"] = urljoin(BASE_URL, href) if href else ""

            if school.get("name"):
                schools.append(school)

        except Exception as e:
            print(f"  Error parsing card: {e}")

    return schools


# ──────────────────────────────────────────────
# STEP 3 — HANDLE PAGINATION
# ──────────────────────────────────────────────
async def scrape_all_pages_for_city(browser, city: str) -> list[dict]:
    """
    Handles pagination for a city's school listing.
    """
    page = await browser.new_page()
    all_schools = []
    page_num = 1

    while True:
        # Yellow Slate pagination — adjust if their URL pattern is different
        # Common patterns: ?page=2  or  /page/2  or  infinite scroll
        if page_num == 1:
            url = f"{BASE_URL}/schools/{city}"
        else:
            url = f"{BASE_URL}/schools/{city}?page={page_num}"

        print(f"  Scraping {city} — page {page_num}: {url}")
        schools = await scrape_schools_from_page(page, url)

        if not schools:
            print(f"  No more schools found on page {page_num}, stopping.")
            break

        for s in schools:
            s["city"] = city  # Tag with city

        all_schools.extend(schools)
        print(f"  ✅ Found {len(schools)} schools on page {page_num}")
        page_num += 1
        await asyncio.sleep(1)  # Be polite to the server

    await page.close()
    return all_schools


# ──────────────────────────────────────────────
# ALTERNATIVE: NEXT.JS DATA API APPROACH
# Next.js apps expose /_next/data/{buildId}/... endpoints
# This is often the cleanest way to get structured JSON
# ──────────────────────────────────────────────
async def get_nextjs_build_id(page) -> str:
    """
    Extract the Next.js build ID from the page source.
    Next.js exposes it in window.__NEXT_DATA__.buildId
    """
    await page.goto(f"{BASE_URL}/home", wait_until="domcontentloaded")
    build_id = await page.evaluate("() => window.__NEXT_DATA__?.buildId || ''")
    print(f"Next.js Build ID: {build_id}")
    return build_id


async def fetch_nextjs_data(page, build_id: str, city: str, page_num: int = 1) -> dict | None:
    """
    Fetch data via the Next.js internal data API.
    URL pattern: /_next/data/{buildId}/schools/{city}.json?page=N
    """
    url = f"{BASE_URL}/_next/data/{build_id}/schools/{city}.json"
    if page_num > 1:
        url += f"?page={page_num}"

    print(f"  Fetching Next.js data: {url}")
    response = await page.goto(url, wait_until="domcontentloaded")

    if response and response.status == 200:
        try:
            data = await response.json()
            return data
        except Exception:
            text = await response.text()
            print(f"  Response (first 300 chars): {text[:300]}")
            return None
    else:
        status = response.status if response else "no response"
        print(f"  ❌ Got status {status} for {url}")
        return None


# ──────────────────────────────────────────────
# MAIN RUNNER
# ──────────────────────────────────────────────
async def main():
    print("=" * 60)
    print("  Yellow Slate School Scraper")
    print("=" * 60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # ── PHASE 1: Discover Next.js Build ID ──
        print("\n[Phase 1] Getting Next.js build ID...")
        build_id = await get_nextjs_build_id(page)

        if build_id:
            print(f"\n[Phase 2] Trying Next.js data API with build ID: {build_id}")

            all_schools = []
            for city in CITIES:
                print(f"\n📍 City: {city.upper()}")
                page_num = 1

                while True:
                    data = await fetch_nextjs_data(page, build_id, city, page_num)
                    if not data:
                        break

                    # Navigate the JSON structure — this depends on their schema
                    # Common keys: pageProps.schools, pageProps.data, props.pageProps
                    page_props = data.get("pageProps", {})
                    print(f"  pageProps keys: {list(page_props.keys())[:10]}")

                    # Try common data paths
                    schools_data = (
                        page_props.get("schools")
                        or page_props.get("data", {}).get("schools")
                        or page_props.get("schoolList")
                        or []
                    )

                    if not schools_data:
                        print(f"  No schools array found. Full pageProps preview:")
                        print(f"  {str(page_props)[:400]}")
                        break

                    for school in schools_data:
                        school["city"] = city
                        all_schools.append(school)

                    print(f"  ✅ Page {page_num}: {len(schools_data)} schools")

                    # Check if there are more pages
                    total = page_props.get("total") or page_props.get("totalCount") or 0
                    per_page = page_props.get("perPage") or page_props.get("limit") or 20
                    if page_num * per_page >= total:
                        break
                    page_num += 1
                    await asyncio.sleep(0.5)

        else:
            # ── FALLBACK: Intercept API calls first ──
            print("\n[Phase 1b] Build ID not found. Running API interception...")
            api_calls = await intercept_api_calls("hyderabad")

            with open(INTERCEPTED_API_FILE, "w") as f:
                json.dump(api_calls, f, indent=2)
            print(f"\n💾 Saved intercepted calls to {INTERCEPTED_API_FILE}")
            print("   → Review this file to find the API endpoint, then update the script.")

            # ── FALLBACK: DOM scraping ──
            print("\n[Phase 2] Falling back to DOM scraping...")
            all_schools = []
            for city in CITIES:
                print(f"\n📍 City: {city.upper()}")
                schools = await scrape_all_pages_for_city(browser, city)
                all_schools.extend(schools)
                print(f"  Total for {city}: {len(schools)}")
                await asyncio.sleep(2)

        await browser.close()

    # ── SAVE TO CSV ──
    if all_schools:
        df = pd.DataFrame(all_schools)
        df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
        print(f"\n✅ Saved {len(all_schools)} schools to {OUTPUT_FILE}")
        print(f"   Columns: {list(df.columns)}")
        print(f"\n   Preview:")
        print(df.head().to_string())
    else:
        print("\n⚠️  No schools scraped. See notes above to fix selectors/API path.")


# ──────────────────────────────────────────────
# RUN
# ──────────────────────────────────────────────
if __name__ == "__main__":
    asyncio.run(main())