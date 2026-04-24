"""Check for embedded data in page."""
import asyncio
from playwright.async_api import async_playwright

async def check_embedded_data():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto("https://yellowslate.com/schools/mumbai", wait_until="networkidle", timeout=60000)
        
        # Check for __NEXT_DATA__
        next_data = await page.evaluate("""() => {
            const script = document.getElementById('__NEXT_DATA__');
            return script ? script.textContent : 'NOT FOUND';
        }""")
        
        print("__NEXT_DATA__:", next_data[:500] if len(next_data) > 500 else next_data)
        
        # Check for school data in page source
        content = await page.content()
        if 'schoolList' in content or 'schools' in content.lower():
            print("\nSchool data found in page")
        
        # Count school cards
        count = await page.evaluate("""() => {
            return document.querySelectorAll('a[href^="/school/"]').length;
        }""")
        print(f"\nSchool links on page: {count}")
        
        await browser.close()

asyncio.run(check_embedded_data())