"""
Yellow Slate — Quick API Sniffer
==================================
Run this FIRST. It opens a real browser, navigates to Yellow Slate,
and prints every API call the frontend makes so you can see the
exact endpoint + params to use.

Install: pip install playwright && playwright install chromium
Run:     python sniff_api.py
"""

import asyncio
import json
from playwright.async_api import async_playwright


async def sniff():
    api_hits = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # headless=False so you can watch
        context = await browser.new_context()
        page = await context.new_page()

        # ── Capture every response that returns JSON ──
        async def on_response(response):
            url = response.url
            content_type = response.headers.get("content-type", "")

            if "json" in content_type and (
                "yellowslate.com" in url or "_next" in url
            ):
                try:
                    body = await response.json()
                    entry = {"url": url, "status": response.status, "body": body}
                    api_hits.append(entry)
                    print(f"\n🔵 {response.status} {url}")
                    print(f"   Keys: {list(body.keys()) if isinstance(body, dict) else type(body).__name__}")
                    preview = str(body)[:300]
                    print(f"   Preview: {preview}")
                except Exception:
                    pass

        page.on("response", on_response)

        # Navigate to school listing
        city = "hyderabad"
        print(f"Opening yellowslate.com/schools/{city} ...")
        await page.goto(f"https://yellowslate.com/schools/{city}", wait_until="networkidle")
        await page.wait_for_timeout(4000)

        # Also try scrolling to trigger lazy load
        await page.keyboard.press("End")
        await page.wait_for_timeout(2000)

        # Print next.js build ID
        build_id = await page.evaluate("() => window.__NEXT_DATA__?.buildId || 'NOT FOUND'")
        next_data = await page.evaluate("() => JSON.stringify(window.__NEXT_DATA__ || {})")
        
        print(f"\n\n{'='*60}")
        print(f"Next.js Build ID: {build_id}")
        print(f"\n__NEXT_DATA__ preview:")
        next_json = json.loads(next_data)
        print(json.dumps(next_json, indent=2)[:2000])

        print(f"\n\n{'='*60}")
        print(f"Total JSON responses captured: {len(api_hits)}")
        for h in api_hits:
            print(f"\n  URL: {h['url']}")
            print(f"  Body preview: {str(h['body'])[:200]}")

        # Save everything
        with open("sniffed_calls.json", "w") as f:
            json.dump(api_hits, f, indent=2, default=str)

        with open("next_data.json", "w") as f:
            json.dump(next_json, f, indent=2, default=str)

        print("\n💾 Saved sniffed_calls.json and next_data.json")
        print("   → Check next_data.json to see the school data structure")
        print("   → Check sniffed_calls.json to see all API calls made")

        await browser.close()


asyncio.run(sniff())