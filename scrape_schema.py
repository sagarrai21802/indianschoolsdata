import asyncio
import json
import re
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright


BASE_URL = "https://yellowslate.com"
DEFAULT_OUTPUT_DIR = Path("scraped_data")


def get_all_schools(output_dir: Path, cities=None):
    schools = []
    for city_dir in output_dir.iterdir():
        if not city_dir.is_dir() or city_dir.name.startswith("_"):
            continue
        city_slug = city_dir.name
        if cities and city_slug not in cities:
            continue
        
        for school_folder in city_dir.iterdir():
            if not school_folder.is_dir() or school_folder.name.startswith("_"):
                continue
            
            about_file = school_folder / "about.json"
            if not about_file.exists():
                continue
            
            try:
                about_data = json.loads(about_file.read_text())
                if about_data.get("slug"):
                    schools.append({
                        "city": city_slug,
                        "folder": school_folder.name,
                        "slug": about_data["slug"],
                        "name": about_data.get("name", "")
                    })
            except (json.JSONDecodeError, FileNotFoundError):
                continue
    
    return schools


def extract_json_ld(html: str):
    schema_data = []
    pattern = r'<script[^>]*type="application/ld\+json"[^>]*>([\s\S]*?)</script>'
    for match in re.finditer(pattern, html, re.IGNORECASE):
        try:
            data = json.loads(match.group(1))
            schema_data.append(data)
        except json.JSONDecodeError:
            continue
    return schema_data


def parse_breadcrumb(data):
    if data.get("@type") != "BreadcrumbList":
        return None
    items = data.get("itemListElement", [])
    return {
        "items": [
            {"position": item.get("position"), "name": item.get("name"), "url": item.get("item")}
            for item in items
        ]
    }


def parse_localbusiness(data):
    if data.get("@type") != "LocalBusiness":
        return None
    return {
        "name": data.get("name"),
        "image": data.get("image"),
        "url": data.get("url"),
        "telephone": data.get("telephone"),
        "address": data.get("address"),
        "geo": data.get("geo"),
    }


def parse_review_schema(data):
    if data.get("@type") != "Review":
        return None
    item_list = data.get("itemListElement", [])
    reviews = []
    for review in item_list:
        if review.get("@type") != "Review":
            continue
        item_reviewed = review.get("itemReviewed", {})
        author = review.get("author", {})
        rating = review.get("reviewRating", {})
        reviews.append({
            "school_name": item_reviewed.get("name"),
            "school_address": item_reviewed.get("address"),
            "school_url": item_reviewed.get("url"),
            "aggregate_rating": item_reviewed.get("aggregateRating"),
            "author": author.get("name"),
            "date_published": review.get("datePublished"),
            "rating_value": rating.get("ratingValue"),
            "best_rating": rating.get("bestRating"),
            "worst_rating": rating.get("worstRating"),
            "review_body": review.get("reviewBody"),
            "publisher": review.get("publisher", {}).get("name"),
        })
    return {"number_of_items": data.get("numberOfItems"), "reviews": reviews}


def process_schema_data(schema_list):
    result = {"breadcrumbs": [], "local_business": None, "reviews": None}
    
    for schema in schema_list:
        if isinstance(schema, list):
            for item in schema:
                breadcrumb = parse_breadcrumb(item)
                if breadcrumb:
                    result["breadcrumbs"] = breadcrumb["items"]
                
                local_business = parse_localbusiness(item)
                if local_business:
                    result["local_business"] = local_business
                
                review_schema = parse_review_schema(item)
                if review_schema:
                    result["reviews"] = review_schema
        else:
            breadcrumb = parse_breadcrumb(schema)
            if breadcrumb:
                result["breadcrumbs"] = breadcrumb["items"]
            
            local_business = parse_localbusiness(schema)
            if local_business:
                result["local_business"] = local_business
            
            review_schema = parse_review_schema(schema)
            if review_schema:
                result["reviews"] = review_schema
    
    return result


async def scrape_school_schema(browser, school):
    slug = school.get("slug")
    name = school.get("name")
    if not slug:
        return None
    
    detail_url = f"{BASE_URL}{slug}"
    page = await browser.new_page()
    
    try:
        await page.goto(detail_url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(2000)
        
        html = await page.content()
        schema_list = extract_json_ld(html)
        
        if not schema_list:
            print(f"  No JSON-LD schema found for {name}")
            return None
        
        processed = process_schema_data(schema_list)
        processed["url"] = detail_url
        processed["scraped_at"] = datetime.now().isoformat()
        
        return processed
    except Exception as e:
        print(f"  Error scraping {detail_url}: {e}")
        return None
    finally:
        await page.close()


async def run(args):
    output_dir = Path(args.get("output_dir", DEFAULT_OUTPUT_DIR))
    city_filter = args.get("city")
    limit = args.get("limit")
    
    print("Finding schools to process...")
    schools = get_all_schools(output_dir, city_filter)
    print(f"Found {len(schools)} schools")
    
    if limit:
        schools = schools[:limit]
        print(f"Limited to {limit} schools")
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        
        processed = 0
        failed = 0
        
        for school in schools:
            print(f"Processing: {school['city']}/{school['folder']}")
            
            schema_data = await scrape_school_schema(browser, school)
            
            if schema_data:
                schema_path = output_dir / school["city"] / school["folder"] / "schema.json"
                schema_path.write_text(json.dumps(schema_data, indent=2, ensure_ascii=False))
                processed += 1
                print(f"  Saved schema.json")
            else:
                failed += 1
                print(f"  Failed to get schema data")
        
        await browser.close()
    
    print(f"\n{'=' * 60}")
    print("SCHEMA SCRAPE SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total schools: {len(schools)}")
    print(f"Processed: {processed}")
    print(f"Failed: {failed}")
    print(f"{'=' * 60}")


def parse_args():
    args = {"output_dir": DEFAULT_OUTPUT_DIR, "city": None, "limit": None}
    
    for arg in __import__("sys").argv[1:]:
        if arg.startswith("--output-dir="):
            args["output_dir"] = arg.split("=")[1]
        elif arg.startswith("--city="):
            cities_str = arg.split("=")[1]
            args["city"] = set(c.strip().lower() for c in cities_str.split(",") if c.strip())
        elif arg.startswith("--limit="):
            try:
                args["limit"] = int(arg.split("=")[1])
            except ValueError:
                pass
    
    return args


if __name__ == "__main__":
    asyncio.run(run(parse_args()))