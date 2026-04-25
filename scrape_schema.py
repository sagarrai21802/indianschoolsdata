import argparse
import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


class SchemaScraper:
    def __init__(self, output_dir: str = "scraped_data", cities: Optional[List[str]] = None):
        self.base_url = "https://yellowslate.com"
        self.output_dir = Path(output_dir)
        self.cities = cities
        self.stats = {
            "total_schools": 0,
            "processed": 0,
            "failed": 0,
            "skipped": 0,
            "start_time": None,
            "end_time": None,
        }

    def _get_all_schools(self) -> List[tuple]:
        schools = []
        if self.cities:
            city_dirs = [self.output_dir / city for city in self.cities]
        else:
            city_dirs = [d for d in self.output_dir.iterdir() if d.is_dir() and not d.name.startswith("_")]

        for city_dir in city_dirs:
            if not city_dir.is_dir():
                continue
            city_slug = city_dir.name
            for school_folder in city_dir.iterdir():
                if not school_folder.is_dir() or school_folder.name.startswith("_"):
                    continue
                about_file = school_folder / "about.json"
                if about_file.exists():
                    schools.append((city_slug, school_folder))
        return schools

    def _extract_json_ld(self, html: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        schema_data = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                schema_data.append(data)
            except (json.JSONDecodeError, TypeError):
                continue
        return schema_data

    def _parse_breadcrumb(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if data.get("@type") != "BreadcrumbList":
            return None
        items = data.get("itemListElement", [])
        breadcrumb = {"items": []}
        for item in items:
            breadcrumb["items"].append({
                "position": item.get("position"),
                "name": item.get("name"),
                "url": item.get("item"),
            })
        return breadcrumb

    def _parse_localbusiness(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if data.get("@type") != "LocalBusiness":
            return None
        parsed = {
            "name": data.get("name"),
            "image": data.get("image"),
            "url": data.get("url"),
            "telephone": data.get("telephone"),
            "address": data.get("address"),
            "geo": data.get("geo"),
        }
        return parsed

    def _parse_review_schema(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
            parsed_review = {
                "school_name": item_reviewed.get("name"),
                "school_address": item_reviewed.get("address"),
                "school_url": item_reviewed.get("url"),
                "aggregate_rating": item_reviewed.get("aggregateRating", {}),
                "author": author.get("name"),
                "date_published": review.get("datePublished"),
                "rating_value": rating.get("ratingValue"),
                "best_rating": rating.get("bestRating"),
                "worst_rating": rating.get("worstRating"),
                "review_body": review.get("reviewBody"),
                "publisher": review.get("publisher", {}).get("name"),
            }
            reviews.append(parsed_review)
        return {
            "number_of_items": data.get("numberOfItems"),
            "reviews": reviews,
        }

    def _process_schema_data(self, schema_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        result = {
            "breadcrumbs": [],
            "local_business": None,
            "reviews": None,
        }
        for schema in schema_list:
            breadcrumb = self._parse_breadcrumb(schema)
            if breadcrumb:
                result["breadcrumbs"] = breadcrumb["items"]

            local_business = self._parse_localbusiness(schema)
            if local_business:
                result["local_business"] = local_business

            review_schema = self._parse_review_schema(schema)
            if review_schema:
                result["reviews"] = review_schema
        return result

    async def scrape_school_schema(self, browser, school_folder: Path, city_slug: str) -> Optional[Dict[str, Any]]:
        about_file = school_folder / "about.json"
        try:
            about_data = json.loads(about_file.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            return None

        slug = about_data.get("slug", "")
        if not slug:
            return None

        detail_url = f"{self.base_url}{slug}"
        if detail_url.endswith("/"):
            detail_url = detail_url[:-1]

        page = await browser.new_page()
        try:
            response = await page.goto(detail_url, wait_until="domcontentloaded", timeout=60000)
            if response and response.status != 200:
                print(f"  Failed to load {detail_url}: HTTP {response.status}")
                return None

            await page.wait_for_timeout(2000)
            html = await page.content()
            schema_list = self._extract_json_ld(html)

            if not schema_list:
                print(f"  No JSON-LD schema found for {school_folder.name}")
                return None

            processed = self._process_schema_data(schema_list)
            processed["url"] = detail_url
            processed["scraped_at"] = datetime.now().isoformat()

            return processed

        except Exception as e:
            print(f"  Error scraping {detail_url}: {str(e)}")
            return None
        finally:
            await page.close()

    async def run(self) -> Dict[str, Any]:
        self.stats["start_time"] = datetime.now().isoformat()
        schools = self._get_all_schools()
        self.stats["total_schools"] = len(schools)

        print(f"Found {len(schools)} schools to process")

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)

            for city_slug, school_folder in schools:
                school_name = school_folder.name
                print(f"Processing: {city_slug}/{school_name}")

                schema_data = await self.scrape_school_schema(browser, school_folder, city_slug)

                if schema_data:
                    schema_file = school_folder / "schema.json"
                    schema_file.write_text(json.dumps(schema_data, indent=2, ensure_ascii=False))
                    self.stats["processed"] += 1
                    print(f"  Saved schema.json")
                else:
                    self.stats["failed"] += 1
                    print(f"  Failed to get schema data")

            await browser.close()

        self.stats["end_time"] = datetime.now().isoformat()

        print(f"\n{'=' * 60}")
        print("SCHEMA SCRAPE SUMMARY")
        print(f"{'=' * 60}")
        print(f"Total schools: {self.stats['total_schools']}")
        print(f"Processed: {self.stats['processed']}")
        print(f"Failed: {self.stats['failed']}")
        print(f"{'=' * 60}")

        return self.stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="YellowSlate schema scraper")
    parser.add_argument("--cities", nargs="+", help="Cities to process")
    parser.add_argument("--output-dir", default="scraped_data", help="Directory with scraped data")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    scraper = SchemaScraper(output_dir=args.output_dir, cities=args.cities)
    await scraper.run()


if __name__ == "__main__":
    asyncio.run(main())