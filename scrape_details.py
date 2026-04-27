"""Comprehensive Detail Scraper — captures all media types.

Extracts from each school detail page:
- Images: <img> tags with CDN URLs
- Videos: <video> tags, YouTube/Vimeo iframes
- Instagram posts: embedded Instagram content
- Structured data: JSON-LD (LocalBusiness, School, etc.)
- All text fields: rating, reviews, phone, board, fees, about, etc.

Usage:
    python3 scrape_details_comprehensive.py --city=bengaluru --limit=10
"""

import asyncio
import json
import re
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright

BASE_URL = "https://yellowslate.com"
CHECKPOINT_FILE = "scraped_data/details_checkpoint.json"
RESULTS_DIR = Path("scraped_data")


def load_checkpoint() -> Dict[str, Any]:
    if Path(CHECKPOINT_FILE).exists():
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_checkpoint(data: Dict[str, Any]):
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def extract_json_ld(html: str) -> List[Dict[str, Any]]:
    """Extract all JSON-LD structured data blocks."""
    import re
    blocks = []
    pattern = r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>([\s\S]*?)</script>'
    for m in re.finditer(pattern, html, re.I):
        try:
            raw = m.group(1).strip()
            # Handle escaped JSON
            if raw.startswith('\\"') or '\\"' in raw[:100]:
                try:
                    raw = json.loads(f'"{raw}"')
                except Exception:
                    pass
            data = json.loads(raw)
            if isinstance(data, list):
                blocks.extend(data)
            else:
                blocks.append(data)
        except Exception:
            pass
    return blocks


def extract_instagram_posts(html: str) -> List[Dict[str, Any]]:
    """Extract embedded Instagram posts from page HTML."""
    posts = []
    # Match Instagram post JSON embedded in page
    pattern = r'\{"id":(\d+),"media_url":"([^"]+)","thumbnail_url":"([^"]+)","video_url":(null|"[^"]*"),"instagram_url":"([^"]+)","description":"([^"]+?)","media_type":"([^"]+?)","source_type":"([^"]+?)","like_count":(\d+),"comments_count":(\d+),"instagram_post_id":"([^"]+?)","instagram_timestamp":"([^"]+?)","created_at":"([^"]+?)"\}'


    for m in re.finditer(pattern, html):
        try:
            raw_video = m.group(4)
            video_url = None
            if raw_video and raw_video != 'null':
                video_url = json.loads(raw_video)

            posts.append({
                "id": int(m.group(1)),
                "media_url": m.group(2),
                "thumbnail_url": m.group(3),
                "video_url": video_url,
                "instagram_url": m.group(5),
                "description": m.group(6).strip(),
                "media_type": m.group(7),
                "source_type": m.group(8),
                "like_count": int(m.group(9)),
                "comments_count": int(m.group(10)),
                "instagram_post_id": m.group(11),
                "instagram_timestamp": m.group(12),
                "created_at": m.group(13),
            })
        except Exception:
            continue
    return posts


def extract_all_image_urls(html: str) -> List[str]:
    """Extract all image URLs from img tags, srcset, background images, and JSON data."""
    urls = []

    # 1. Standard <img src="">
    for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.I):
        url = m.group(1)
        # Decode URL-encoded Next.js image proxy
        if '/_next/image?' in url and 'url=' in url:
            import urllib.parse
            if u := re.search(r'url=([^&]+)', url):
                decoded = urllib.parse.unquote(u.group(1))
                if decoded.startswith('http'):
                    urls.append(decoded)
                    continue
        if url.startswith('http'):
            urls.append(url)

    # 2. srcset attribute (responsive images)
    for m in re.finditer(r'srcset=["\']([^"\']+)["\']', html, re.I):
        srcset = m.group(1)
        for src in srcset.split(','):
            src = src.strip().split(' ')[0]  # get URL before descriptor
            if src.startswith('http'):
                urls.append(src)

    # 3. Background-image in style attributes
    for m in re.finditer(r'background-image\s*:\s*url\(["\']?([^)"\']+)["\']?\)', html, re.I):
        url = m.group(1)
        if url.startswith('http'):
            urls.append(url)

    # 4. Data URLs in JSON blobs (Instagram images, gallery JSON)
    for m in re.finditer(r'"image"\s*:\s*"([^"]+)"', html):
        url = m.group(1)
        if url.startswith('http'):
            urls.append(url.replace('\\/', '/'))

    # 5. og:image meta tag
    for m in re.finditer(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I):
        url = m.group(1)
        if url.startswith('http'):
            urls.append(url)

    # 6. From structured data JSON (LocalBusiness.image, etc.)
    for m in re.finditer(r'"image"\s*:\s*"([^"]+)"', html):
        url = m.group(1)
        if url.startswith('http'):
            urls.append(url.replace('\\/', '/'))

    # Deduplicate
    unique = []
    seen = set()
    for url in urls:
        # Normalize: remove query params from DigitalOcean spaces
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if clean not in seen:
            seen.add(clean)
            unique.append(url)

    return unique


def extract_video_urls(html: str) -> List[Dict[str, str]]:
    """Extract video URLs from <video> tags and YouTube/Vimeo iframes."""
    videos = []

    # <video> tags
    for m in re.finditer(r'<video[^>]*>.*?<source[^>]+src=["\']([^"\']+)["\']', html, re.I | re.DOTALL):
        videos.append({"url": m.group(1), "type": "video/mp4"})

    # YouTube iframes
    for m in re.finditer(r'<iframe[^>]+src=["\']https?://www\.youtube\.com/embed/([^"\']+)["\']', html, re.I):
        videos.append({"url": f"https://www.youtube.com/watch?v={m.group(1)}", "type": "youtube"})

    # Vimeo iframes
    for m in re.finditer(r'<iframe[^>]+src=["\']https?://player\.vimeo\.com/video/([^"\']+)["\']', html, re.I):
        videos.append({"url": f"https://vimeo.com/{m.group(1)}", "type": "vimeo"})

    return videos


def extract_emails(html: str) -> List[str]:
    return list(set(re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', html)))


def extract_websites(html: str) -> List[str]:
    urls = set()
    for m in re.finditer(r'https?://[^\s<>"\']+', html):
        url = m.group(0)
        if 'yellowslate.com' not in url and 'instagram.com' not in url and 'facebook.com' not in url:
            urls.add(url)
    return list(urls)


def parse_school_text(text: str) -> Dict[str, Any]:
    """Parse school details from raw page text."""
    data = {
        "rating": None,
        "views": None,
        "reviews_count": None,
        "phone": None,
        "locality": None,
        "board": None,
        "established": None,
        "category": None,
        "classes": None,
        "gender": None,
        "fees_range": None,
        "about": None,
    }

    if m := re.search(r'(\d+\.?\d*)/5\s*Rating', text):
        data["rating"] = m.group(1)

    if m := re.search(r'([\d,]+)\s*Views', text):
        data["views"] = m.group(1).replace(",", "")

    if m := re.search(r'([\d,]+)\s*Reviews', text):
        data["reviews_count"] = m.group(1).replace(",", "")

    if m := re.search(r'(\+\d{10,})', text):
        data["phone"] = m.group(1)

    if m := re.search(r'Board\s*[:\-]\s*([A-Za-z0-9,\s]+)', text, re.I):
        data["board"] = m.group(1).strip()
    elif m := re.search(r'\b(CBSE|ICSE|IB|IGCSE|State Board|Cambridge)\b', text, re.I):
        data["board"] = m.group(1).upper()

    if m := re.search(r'(Established|Since)\s*[:\-]\s*(\d{4})', text, re.I):
        data["established"] = m.group(2)

    if m := re.search(r'Category\s*[:\-]\s*([^\n]+)', text, re.I):
        data["category"] = m.group(1).strip()

    if m := re.search(r'(Nursery\s*-\s*\d+|\d+\s*-\s*\d+)', text):
        data["classes"] = m.group(1)

    if "Co-Education" in text or "Co-ed" in text:
        data["gender"] = "Co-Education"
    elif re.search(r'\bGirls\b', text, re.I):
        data["gender"] = "Girls"
    elif re.search(r'\bBoys\b', text, re.I):
        data["gender"] = "Boys"

    if m := re.search(r'[Ff]ee\s*[Rr]ange\s*[:-]\s*[₹\u20b9]?\s*([\d,]+)\s*-\s*([\d,]+)', text):
        data["fees_range"] = f"{m.group(1)}-{m.group(2)}"

    if m := re.search(r'About\s+[^:\n]+([^\n].*?)(?:\nEnquire Now|\nShow more|\n\n|$)', text, re.DOTALL | re.I):
        about_raw = m.group(0)
        about_clean = re.sub(r'.*About\s+', '', about_raw, flags=re.I)
        about_clean = re.sub(r'\nShow more.*', '', about_clean)
        about_clean = re.sub(r'\nEnquire Now.*', '', about_clean)
        data["about"] = about_clean.strip()[:1000]

    return data


async def scrape_school_detail(page, slug: str, city: str) -> Dict[str, Any]:
    """Scrape comprehensive detail page data."""
    url = f"{BASE_URL}{slug}"
    result = {
        "slug": slug,
        "url": url,
        "city": city,
        "name": None,
        "scraped_at": datetime.now().isoformat(),
    }

    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
    except Exception as e:
        print(f"    Error loading page: {e}")
        result["error"] = str(e)
        return result

    # Wait for content to settle
    await asyncio.sleep(1)

    # Get raw HTML for structured extraction
    try:
        html = await page.content()
        result["html_length"] = len(html)

        # Structured data (JSON-LD)
        result["structured_data"] = extract_json_ld(html)

        # Instagram posts
        result["instagram_posts"] = extract_instagram_posts(html)
        result["instagram_posts_count"] = len(result["instagram_posts"])

        # Extract all media
        result["all_images"] = extract_all_image_urls(html)
        result["videos"] = extract_video_urls(html)
        result["email_candidates"] = extract_emails(html)
        result["website_urls"] = extract_websites(html)

    except Exception as e:
        print(f"    Warning extracting structured data: {e}")

    # Get school name
    try:
        result["name"] = await page.locator("h1").first.inner_text()
    except Exception:
        pass

    # Get all page text (for regex parsing)
    try:
        full_text = await page.locator("body").inner_text()
        parsed = parse_school_text(full_text)
        result.update(parsed)
    except Exception as e:
        print(f"    Warning parsing text: {e}")

    # Extract locality from name if format "Name - Locality"
    if result.get("name"):
        if m := re.search(r'-\s*([^-\n]+)\s*$', result["name"]):
            result["locality"] = m.group(1).strip()

    # Deduplicate and categorize images
    result["images"] = list(set(result.get("all_images", [])))
    result["images"] = result["images"][:50]  # limit 50
    result["videos"] = result.get("videos", [])[:20]  # limit 20

    # Cleanup temporary fields
    result.pop("all_images", None)

    return result


def discover_school_folders(city_filter: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Find all school folders with about.json but no details.json."""
    entries = []
    cities_to_scan = [city_filter] if city_filter else sorted([d.name for d in RESULTS_DIR.iterdir() if d.is_dir() and not d.name.startswith('_')])

    for city in cities_to_scan:
        city_dir = RESULTS_DIR / city
        if not city_dir.exists():
            continue
        city_entries = []
        for school_dir in city_dir.iterdir():
            if not school_dir.is_dir() or school_dir.name.startswith('_'):
                continue
            about_path = school_dir / "about.json"
            details_path = school_dir / "details.json"
            if about_path.exists() and not details_path.exists():
                city_entries.append({
                    "city": city,
                    "school_id": school_dir.name,
                    "folder_path": str(school_dir),
                    "about_path": str(about_path)
                })

        if limit:
            city_entries = city_entries[:limit]
        entries.extend(city_entries)

    return entries


async def scrape_details(entries: List[Dict[str, Any]], delay_min: float = 1.5, delay_max: float = 3.0) -> int:
    """Scrape detail pages. Returns exit code (0 = success, 1 = failures)."""
    total = len(entries)
    print(f"Starting detail backfill for {total} schools")
    print(f"Delay: {delay_min}s–{delay_max}s between requests\n")

    checkpoint = load_checkpoint()
    scraped_count = 0
    skipped_count = 0
    failed_count = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for i, entry in enumerate(entries, 1):
            city = entry["city"]
            school_id = entry["school_id"]
            key = f"{city}/{school_id}"

            if key in checkpoint:
                print(f"[{i:4d}/{total}] ✓ already done: {city}/{school_id}")
                skipped_count += 1
                continue

            print(f"[{i:4d}/{total}] Scraping: {city}/{school_id}", end=" ")

            try:
                # Load about.json to get slug
                with open(entry["about_path"], "r", encoding="utf-8") as f:
                    about = json.load(f)

                slug = about.get("slug")
                if not slug:
                    print(f"\n    ⚠ Skipping: no slug")
                    failed_count += 1
                    continue

                result = await scrape_school_detail(page, slug, city)

                # Save details.json
                details_file = Path(entry["folder_path"]) / "details.json"
                with open(details_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)

                checkpoint[key] = {
                    "scraped_at": result.get("scraped_at"),
                    "url": result.get("url"),
                    "name": result.get("name"),
                }
                save_checkpoint(checkpoint)

                scraped_count += 1
                print(f"✓ {result.get('name','')[:35]}")
                if result.get("instagram_posts_count", 0) > 0:
                    print(f"    └─ {result['instagram_posts_count']} Instagram posts")

            except Exception as e:
                print(f"\n    ✗ error: {e}")
                failed_count += 1

            import random
            await asyncio.sleep(random.uniform(delay_min, delay_max))

        await browser.close()

    print(f"\n{'='*60}")
    print(f"DETAIL BACKFILL SUMMARY")
    print(f"{'='*60}")
    print(f"Total schools:        {total:6d}")
    print(f"Already completed:    {skipped_count:6d}")
    print(f"Newly scraped:        {scraped_count:6d}")
    print(f"Failed:               {failed_count:6d}")
    print(f"Checkpoint file:      {CHECKPOINT_FILE}")
    print(f"{'='*60}")

    if failed_count > 0:
        print(f"\n⚠  {failed_count} school(s) failed. Re-run with --resume to retry.")
        return 1
    return 0


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="YellowSlate Detail Backfill — All Media Types")
    parser.add_argument("--city", type=str, help="Scrape only this city (default: all cities)")
    parser.add_argument("--limit", type=int, help="Limit number of schools to scrape (testing only)")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint (skip already done)")
    parser.add_argument("--delay-min", type=float, default=1.5, help="Min delay between requests (seconds)")
    parser.add_argument("--delay-max", type=float, default=3.0, help="Max delay between requests (seconds)")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("YellowSlate Detail Backfill — Phase 2")
    print("=" * 60)
    if args.city:
        print(f"City filter: {args.city}")
    if args.limit:
        print(f"Limit: {args.limit} schools")
    print()

    entries = discover_school_folders(city_filter=args.city, limit=args.limit)

    if args.resume:
        checkpoint = load_checkpoint()
        entries = [e for e in entries if f"{e['city']}/{e['school_id']}" not in checkpoint]
        print(f"Resuming — {len(entries)} schools remaining\n")
    else:
        print(f"Found {len(entries)} schools needing detail scraping\n")

    if not entries:
        print("✓ No schools to scrape. All done!")
        return

    exit_code = await scrape_details(entries, delay_min=args.delay_min, delay_max=args.delay_max)
    exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
