"""
Yellow Slate - Direct DOM Scraper
Extracts school data from the rendered page using Playwright.
"""

import asyncio
import json
import csv
import pandas as pd
from playwright.async_api import async_playwright


async def scrape_schools(city: str = "hyderabad"):
    """Scrape schools from Yellow Slate using Playwright."""
    schools = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Navigate to school listing
        url = f"https://yellowslate.com/schools/{city}"
        print(f"Loading: {url}")
        
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        
        # Wait for page to fully render
        await page.wait_for_timeout(5000)
        
        # First, let's see what elements are on the page
        print("\n[Debug] Looking for school links...")
        
        # Try to find any links that look like school pages
        all_links = await page.query_selector_all("a[href*='/school/']")
        print(f"  Found {len(all_links)} school links")
        
        # Also look for school cards - try common patterns
        card_selectors = [
            "div[class*='school-card']",
            "article",
            "div[class*='Card']",
            "div[class*='card']",
            "[data-testid*='school']"
        ]
        
        for sel in card_selectors:
            cards = await page.query_selector_all(sel)
            if cards:
                print(f"  Selector '{sel}' found {len(cards)} elements")
        
        # Let's try to get page content and look for school data
        print("\n[Debug] Extracting page content...")
        
        # Get the full page text
        content = await page.content()
        
        # Look for patterns like school data in the HTML
        # Try to find JSON data embedded in the page
        json_matches = await page.evaluate("""() => {
            const scripts = document.querySelectorAll('script');
            let results = [];
            scripts.forEach(s => {
                if (s.textContent.includes('school') || s.textContent.includes('School')) {
                    results.push(s.textContent.substring(0, 500));
                }
            });
            return results;
        }""")
        
        if json_matches:
            print(f"  Found {len(json_matches)} scripts with 'school' content")
        
        # Let's use a more direct approach - look for links to individual schools
        # and get data from hovering/clicking
        print("\n[Scraping] Extracting school data from links...")
        
        for link in all_links[:10]:  # Limit to first 10 for demo
            try:
                school_data = {}
                
                # Get href
                href = await link.get_attribute("href")
                if href:
                    school_data["url"] = "https://yellowslate.com" + href if href.startswith("/") else href
                
                # Try to get the school name from nearby elements
                # Try parent element
                parent = await link.query_selector("xpath=ancestor::*[1]")
                if parent:
                    # Try to get text from the parent or nearby
                    text = await parent.inner_text()
                    if text:
                        school_data["text"] = text[:200]
                
                # Also check for title attribute
                title = await link.get_attribute("title")
                if title:
                    school_data["title"] = title
                
                if school_data:
                    schools.append(school_data)
            except Exception as e:
                pass
        
        # Also look for data in a different way - search for school cards with specific structure
        print("\n[Scraping] Alternative method - search for school listings...")
        
        # Look for elements containing school names - common heading tags
        headings = await page.query_selector_all("h1, h2, h3, h4, h5, h6")
        
        school_names = []
        for h in headings:
            try:
                text = await h.inner_text()
                # Filter for likely school names (not page titles)
                if text and len(text) > 3 and len(text) < 150:
                    # Check if it has school-like content
                    if not any(w in text.lower() for w in ['school in', 'best school', 'list of']):
                        school_names.append(text)
            except:
                pass
        
        # Now let's get more structured data from the page using JS
        print("\n[Scraping] Getting data from page with JavaScript...")
        
        # Get all text content in a structured way
        page_text = await page.evaluate("""() => {
            // Get all clickable elements that might be schools
            const links = Array.from(document.querySelectorAll('a'));
            const schoolLinks = links.filter(a => 
                a.href && a.href.includes('/school/') && !a.href.includes('yellowslate.com/schools')
            );
            
            return schoolLinks.map(a => ({
                href: a.href,
                text: a.textContent?.trim().substring(0, 100),
                title: a.title || '',
            }));
        }""")
        
        print(f"  Found {len(page_text)} school links via JS")
        
        for item in page_text:
            if item['href'] and item['text']:
                schools.append(item)
        
        # Get page title to verify we have the right data
        title = await page.title()
        print(f"\nPage title: {title}")
        
        await browser.close()
    
    return schools


async def main():
    print("=" * 60)
    print(" Yellow Slate Direct Scraper")
    print("=" * 60)
    
    # Try for Hyderabad first
    schools = await scrape_schools("hyderabad")
    
    print(f"\n{'='*60}")
    print(f"Total schools found: {len(schools)}")
    
    # Show first few
    for i, s in enumerate(schools[:5]):
        print(f"\n{i+1}. {s}")
    
    # Save to JSON
    if schools:
        with open("scraped_schools.json", "w") as f:
            json.dump(schools, f, indent=2)
        print(f"\nSaved to scraped_schools.json")


if __name__ == "__main__":
    asyncio.run(main())