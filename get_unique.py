"""Get all unique school URLs from Mumbai page."""
import asyncio
from playwright.async_api import async_playwright

async def get_unique_schools():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto("https://yellowslate.com/schools/mumbai", wait_until="networkidle", timeout=60000)
        
        # Scroll
        for _ in range(5):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
        
        # Get unique URLs
        schools = await page.evaluate("""() => {
            const links = Array.from(document.querySelectorAll('a[href^="/school/mumbai/"]'));
            const unique = [...new Set(links.map(a => a.href))];
            return unique;
        }""")
        
        print(f"Total unique schools: {len(schools)}")
        for s in schools:
            print(f"  {s}")
        
        await browser.close()

asyncio.run(get_unique_schools())