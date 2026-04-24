"""Capture API calls from YellowSlate."""
import asyncio
from playwright.async_api import async_playwright

async def capture_api():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Capture all requests
        requests = []
        
        def handle_request(request):
            url = request.url
            if 'yellowslate' in url or 'digitaloceanspaces' in url:
                requests.append({
                    'url': url,
                    'method': request.method
                })
        
        page.on("request", handle_request)
        
        print("Loading https://yellowslate.com/schools/mumbai...")
        await page.goto("https://yellowslate.com/schools/mumbai", wait_until="networkidle", timeout=60000)
        
        # Scroll
        for _ in range(3):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
        
        # Filter API calls
        api_calls = [r for r in requests if '/api/' in r['url'] or 'cityId' in r['url'] or 'page=' in r['url']]
        
        print(f"\nTotal requests: {len(requests)}")
        print(f"API calls: {len(api_calls)}")
        
        for r in api_calls[:20]:
            print(f"  {r['method']} {r['url'][:100]}")
        
        await browser.close()

asyncio.run(capture_api())