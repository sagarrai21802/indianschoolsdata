import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright

from scraper import YellowScraper


async def test() -> None:
    scraper = YellowScraper(cities=["delhi"])

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://yellowslate.com/schools/delhi", wait_until="networkidle", timeout=120000)
        await page.wait_for_selector(".hover-card, .card", timeout=120000)

        seen_pages = [await scraper._get_active_page_number(page)]
        while seen_pages[-1] < 82:
            current_page = seen_pages[-1]
            snapshot = await scraper._get_pagination_snapshot(page, current_page)
            visible_last = snapshot["max_visible_page"]
            if current_page == 80:
                print(f"Page 80 snapshot: {snapshot}")
                assert visible_last and visible_last >= 145, f"Expected to still see page 145 from page 80, got {visible_last}"
                assert snapshot["has_exact_next"], "Expected exact next page 81 to be available from page 80"

            moved = await scraper._go_to_next_page(page, current_page)
            assert moved, f"Failed to move from page {current_page}"
            next_page = await scraper._get_active_page_number(page)
            assert next_page == current_page + 1, f"Expected page {current_page + 1}, got {next_page}"
            seen_pages.append(next_page)

        print(f"Sequential pages reached: {seen_pages[-5:]}")

        last_page_link = page.locator(".pagination .page-link", has_text="145")
        assert await last_page_link.count() > 0, "Expected explicit last-page link 145 to be visible"
        await last_page_link.first.click()
        await page.wait_for_timeout(2000)
        last_page = await scraper._get_active_page_number(page)
        assert last_page == 145, f"Expected jump to page 145, got {last_page}"
        print(f"Reached explicit last page: {last_page}")

        await browser.close()

    output_dir = Path("/tmp/yellowslate_test_output")
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
    city_scraper = YellowScraper(output_dir=str(output_dir), cities=["delhi"], max_pages=3)
    city_result = await city_scraper.scrape_city_listing("delhi")
    print(json.dumps({
        "total_schools": city_result["total_schools"],
        "cross_city_skips": city_result["cross_city_skips"],
        "missing_slug_skips": city_result["missing_slug_skips"],
        "pages_scraped": city_result["pages_scraped"],
        "validation_passed": city_result["validation_passed"],
    }, indent=2))
    assert city_result["validation_passed"], city_result["validation_errors"]
    assert city_result["cross_city_skips"] >= 0
    assert city_result["missing_slug_skips"] >= 0


asyncio.run(test())
