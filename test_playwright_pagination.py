import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto('https://yellowslate.com/schools/mumbai', wait_until='networkidle', timeout=60000)
        school_titles = set()
        page_num = 1
        while True:
            print(f'Processing page {page_num}')
            # Scroll to the bottom to load all schools on the current page
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(2)
            # Extract the school titles on the current page
            titles = await page.evaluate('''
                () => {
                    const cards = Array.from(document.querySelectorAll('.hover-card, .card'));
                    return cards.map(card => {
                        const titleElem = card.querySelector('.card-title');
                        return titleElem ? titleElem.textContent.trim() : '';
                    }).filter(title => title);
                }
            ''')
            new_titles = 0
            for title in titles:
                if title not in school_titles:
                    school_titles.add(title)
                    new_titles += 1
            print(f'  Found {len(titles)} titles, {new_titles} new')
            # Try to click the next page button
            next_button = await page.query_selector('button:has-text("Next"), a:has-text("Next"), .pagination .next, .pagination [aria-label="Next"]')
            if not next_button:
                # Try to find the next page number
                # Suppose we are on page X, we look for a link with page X+1
                # We'll try to find the active page and then look for the next sibling
                active_page = await page.query_selector('.pagination .active')
                if active_page:
                    # Get the text of the active page
                    active_text = await active_page.inner_text()
                    # Try to find a link with the text of active_text + 1
                    try:
                        next_page_num = int(active_text) + 1
                        next_button = await page.query_selector(f'.pagination a:has-text("{next_page_num}")')
                    except:
                        pass
            if next_button:
                print(f'  Clicking next page button')
                await next_button.click()
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)
                page_num += 1
            else:
                print(f'  No next page button found')
                break
        print(f'Total unique school titles: {len(school_titles)}')
        await browser.close()

asyncio.run(test())
