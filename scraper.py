import argparse
import asyncio
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


class YellowScraper:
    def __init__(
        self,
        output_dir: str = "scraped_data",
        cities: Optional[List[str]] = None,
        cities_file: str = "cities_to_scrape.txt",
        max_pages: Optional[int] = None,
    ):
        self.base_url = "https://yellowslate.com"
        self.output_dir = Path(output_dir)
        self.cities = cities or self._load_cities(cities_file)
        self.max_pages = max_pages
        self.stats = {
            "total_cities": len(self.cities),
            "processed_cities": 0,
            "total_schools": 0,
            "total_pages": 0,
            "start_time": None,
            "end_time": None,
        }

    def _load_cities(self, cities_file: str) -> List[str]:
        path = Path(cities_file)
        if path.exists():
            cities = [line.strip().lower() for line in path.read_text().splitlines() if line.strip()]
            print(f"Loaded {len(cities)} cities from {cities_file}")
            return cities

        default_cities = [
            "delhi",
            "mumbai",
            "bangalore",
            "hyderabad",
            "chennai",
            "kolkata",
            "pune",
            "ahmedabad",
            "surat",
            "jaipur",
            "lucknow",
            "kanpur",
        ]
        print(f"{cities_file} not found, using default cities")
        return default_cities

    def _slugify(self, value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug or "school"

    def extract_school_id_from_slug(self, slug: str, fallback_name: str = "") -> str:
        cleaned = slug.strip("/")
        if cleaned:
            return cleaned.split("/")[-1]
        return self._slugify(fallback_name)

    def extract_city_from_slug(self, slug: str) -> str:
        match = re.match(r"^/school/([^/]+)/", slug.strip())
        return match.group(1).lower() if match else ""

    def parse_monetary_value(self, text: str) -> Dict[str, Any]:
        result = {"min": None, "max": None, "currency": "INR", "period": "annually"}
        if not text:
            return result

        numbers = [int(match.replace(",", "")) for match in re.findall(r"\d[\d,]*", text) if match]
        numbers = [number for number in numbers if number > 0]
        if numbers:
            result["min"] = min(numbers)
            result["max"] = max(numbers)

        text_lower = text.lower()
        if "month" in text_lower or "monthly" in text_lower or "per month" in text_lower:
            result["period"] = "monthly"
        elif "quarter" in text_lower:
            result["period"] = "quarterly"
        elif "term" in text_lower or "semester" in text_lower:
            result["period"] = "semester"

        return result

    def parse_school_card(self, card, city_slug: str, page_number: int, position_on_page: int) -> Dict[str, Any]:
        school = {
            "id": "",
            "name": "",
            "slug": "",
            "city": city_slug,
            "page_number": page_number,
            "position_on_page": position_on_page,
            "address": "",
            "locality": "",
            "board": "",
            "medium": "English",
            "school_type": "",
            "established": "",
            "grades": "",
            "fees": {"min": None, "max": None, "currency": "INR", "period": "annually"},
            "fees_text": "",
            "contact": {"phone": "", "email": "", "website": ""},
            "facilities": [],
            "admission": {"status": "unknown"},
            "rating": None,
            "reviews_count": None,
            "images": [],
            "listing_only": True,
            "listing_page": f"{self.base_url}/schools/{city_slug}",
            "scraped_at": datetime.now().isoformat(),
        }

        name_elem = card.find(class_=re.compile(r"title|name|school-name", re.I))
        if not name_elem:
            for tag in ["h1", "h2", "h3", "h4", "h5"]:
                name_elem = card.find(tag)
                if name_elem:
                    break
        if name_elem:
            school["name"] = re.sub(rf"\s*-\s*{re.escape(city_slug)}\s*$", "", name_elem.get_text(strip=True), flags=re.I)
            school["name"] = re.sub(r"\s*-\s*$", "", school["name"]).strip()

        link_elem = card.find("a", href=True)
        if link_elem:
            href = link_elem.get("href", "").strip()
            if href.startswith("/school/"):
                school["slug"] = href
            elif href.startswith("http"):
                match = re.match(r"https?://[^/]+(/school/.*)", href)
                if match:
                    school["slug"] = match.group(1)

        school["id"] = self.extract_school_id_from_slug(school["slug"], school["name"])

        address_elem = card.find(class_=re.compile(r"address|location|locality|card-text", re.I))
        if address_elem:
            school["address"] = address_elem.get_text(" ", strip=True)
            school["locality"] = school["address"]

        board_elem = card.find(class_=re.compile(r"board|curriculum|badge", re.I))
        if board_elem:
            school["board"] = board_elem.get_text(" ", strip=True)

        fee_elem = card.find(class_=re.compile(r"fee|amount|price|fees", re.I))
        if fee_elem:
            school["fees_text"] = fee_elem.get_text(" ", strip=True)
            school["fees"] = self.parse_monetary_value(school["fees_text"])

        rating_elem = card.find(class_=re.compile(r"rating|review-score", re.I))
        if rating_elem:
            ratings = re.findall(r"[\d.]+", rating_elem.get_text(" ", strip=True))
            if ratings:
                school["rating"] = float(ratings[0])

        review_elem = card.find(class_=re.compile(r"review|rating-count", re.I))
        if review_elem:
            counts = re.findall(r"[\d,]+", review_elem.get_text(" ", strip=True))
            if counts:
                school["reviews_count"] = int(counts[0].replace(",", ""))

        category_elem = card.find(class_=re.compile(r"category|type|school-type", re.I))
        if category_elem:
            school["school_type"] = category_elem.get_text(" ", strip=True)

        phone_elem = card.find("a", href=re.compile(r"^tel:", re.I))
        if phone_elem:
            school["contact"]["phone"] = phone_elem.get("href", "").replace("tel:", "").strip()

        email_elem = card.find("a", href=re.compile(r"^mailto:", re.I))
        if email_elem:
            school["contact"]["email"] = email_elem.get("href", "").replace("mailto:", "").strip()

        website_elem = card.find("a", href=re.compile(r"^https?://", re.I))
        if website_elem:
            href = website_elem.get("href", "").strip()
            if "yellowslate" not in href:
                school["contact"]["website"] = href

        return school

    async def _get_active_page_number(self, page) -> int:
        return await page.evaluate(
            """
            () => {
              const active = Array.from(document.querySelectorAll('.pagination .page-link'))
                .find((el) => el.className.includes('bg-primary') && /^\d+$/.test(el.textContent.trim()));
              return active ? Number(active.textContent.trim()) : 1;
            }
            """
        )

    async def _get_pagination_snapshot(self, page, current_page: Optional[int] = None) -> Dict[str, Any]:
        return await page.evaluate(
            """
            (currentPage) => {
              const links = Array.from(document.querySelectorAll('.pagination .page-link'));
              const active = links.find((el) => el.className.includes('bg-primary') && /^\d+$/.test(el.textContent.trim()));
              const activePage = active ? Number(active.textContent.trim()) : 1;
              const visibleNumbers = Array.from(
                new Set(
                  links
                    .map((el) => el.textContent.trim())
                    .filter((text) => /^\d+$/.test(text))
                    .map((text) => Number(text))
                )
              ).sort((a, b) => a - b);
              const effectiveCurrentPage = currentPage ?? activePage;
              return {
                active_page: activePage,
                visible_numbers: visibleNumbers,
                max_visible_page: visibleNumbers.length ? Math.max(...visibleNumbers) : null,
                has_exact_next: visibleNumbers.includes(effectiveCurrentPage + 1),
              };
            }
            """,
            arg=current_page,
        )

    async def _get_visible_last_page_number(self, page) -> Optional[int]:
        snapshot = await self._get_pagination_snapshot(page)
        return snapshot["max_visible_page"]

    async def _go_to_next_page(self, page, current_page: int) -> bool:
        next_page = current_page + 1
        numeric_link = page.locator(
            ".pagination .page-link",
            has_text=re.compile(rf"^{next_page}$"),
        )
        if await numeric_link.count() == 0:
            return False

        await numeric_link.first.click()

        try:
            await page.wait_for_function(
                """
                ({ previousPage, expectedPage }) => {
                  const active = Array.from(document.querySelectorAll('.pagination .page-link'))
                    .find((el) => el.className.includes('bg-primary') && /^\d+$/.test(el.textContent.trim()));
                  return active
                    && Number(active.textContent.trim()) !== previousPage
                    && Number(active.textContent.trim()) === expectedPage;
                }
                """,
                arg={"previousPage": current_page, "expectedPage": next_page},
                timeout=60000,
            )
        except Exception:
            return False

        await page.wait_for_timeout(1200)
        return True

    def _extract_cards(self, soup: BeautifulSoup, city_slug: str):
        cards = soup.find_all(class_="hover-card")
        if not cards:
            cards = soup.find_all(class_="card")
        if not cards:
            for card_class in ["school-card", "listing-card", "result-card", "school-listing"]:
                cards = soup.find_all(class_=card_class)
                if cards:
                    break
        if not cards:
            school_links = soup.find_all("a", href=re.compile(rf"/school/{re.escape(city_slug)}/"))
            seen_containers = set()
            cards = []
            for link in school_links:
                parent = link.find_parent(["div", "li", "article"])
                if parent and id(parent) not in seen_containers:
                    seen_containers.add(id(parent))
                    cards.append(parent)
        return cards

    def _reset_city_output(self, city_slug: str) -> Path:
        city_dir = self.output_dir / city_slug
        if city_dir.exists():
            shutil.rmtree(city_dir)
        city_dir.mkdir(parents=True, exist_ok=True)
        return city_dir

    def _count_saved_school_folders(self, city_dir: Path) -> int:
        return sum(1 for path in city_dir.iterdir() if path.is_dir())

    def _save_school_about(self, city_slug: str, school: Dict[str, Any]) -> None:
        school_folder = self.output_dir / city_slug / self.extract_school_id_from_slug(school.get("slug", ""), school.get("name", ""))
        school_folder.mkdir(parents=True, exist_ok=True)
        about_file = school_folder / "about.json"
        about_file.write_text(json.dumps(school, indent=2, ensure_ascii=False))

    def _save_run_summary(self, cities: Dict[str, Dict[str, Any]]) -> None:
        summary = {
            "statistics": self.stats,
            "cities": cities,
        }
        (self.output_dir / "_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    def _validate_city_run(
        self,
        city_slug: str,
        scraped_pages: List[int],
        highest_visible_page: Optional[int],
        stop_reason: str,
        page_stats: List[Dict[str, Any]],
        non_sequential_transition: Optional[Dict[str, int]],
        repeated_signature: Optional[Dict[str, int]],
        saved_school_folder_count: int,
        total_schools: int,
        max_pages_limited: bool,
    ) -> List[str]:
        errors: List[str] = []

        if not scraped_pages:
            errors.append(f"{city_slug}: no pages were scraped")
            return errors

        expected_pages = list(range(1, scraped_pages[-1] + 1))
        if scraped_pages != expected_pages:
            errors.append(f"{city_slug}: visited pages were not contiguous from 1 to {scraped_pages[-1]}")

        if non_sequential_transition:
            errors.append(
                f"{city_slug}: navigation jumped from page {non_sequential_transition['from_page']} to {non_sequential_transition['to_page']}"
            )

        if repeated_signature:
            errors.append(
                f"{city_slug}: page {repeated_signature['page']} repeated the same school set as page {repeated_signature['matches_page']}"
            )

        if saved_school_folder_count != total_schools:
            errors.append(
                f"{city_slug}: saved folder count {saved_school_folder_count} did not match unique schools {total_schools}"
            )

        pages_with_no_cards = [stat["page"] for stat in page_stats if stat["cards_found"] == 0]
        if pages_with_no_cards:
            errors.append(f"{city_slug}: pages with no cards found: {pages_with_no_cards}")

        pages_with_zero_new_schools = [stat["page"] for stat in page_stats if stat["new_schools_saved"] == 0]
        if pages_with_zero_new_schools:
            errors.append(f"{city_slug}: pages with zero new schools saved: {pages_with_zero_new_schools}")

        if not max_pages_limited:
            if stop_reason == "next_page_unavailable" and highest_visible_page and scraped_pages[-1] < highest_visible_page:
                errors.append(
                    f"{city_slug}: stopped at page {scraped_pages[-1]} even though pagination showed page {highest_visible_page}"
                )
            if stop_reason == "next_page_click_failed":
                errors.append(f"{city_slug}: click on exact next page failed before reaching the end")
            if stop_reason == "non_sequential_page":
                errors.append(f"{city_slug}: page navigation became non-sequential")
            if stop_reason == "no_cards_found":
                errors.append(f"{city_slug}: scraper hit a page without cards before a confirmed end state")

        return errors

    async def scrape_city_listing(self, city_slug: str) -> Dict[str, Any]:
        print(f"\n{'=' * 60}")
        print(f"Scraping city listings: {city_slug}")
        print(f"{'=' * 60}")

        city_dir = self._reset_city_output(city_slug)

        all_schools: List[Dict[str, Any]] = []
        seen_school_keys = set()
        page_signatures: Dict[tuple, int] = {}
        scraped_pages: List[int] = []
        page_stats: List[Dict[str, Any]] = []
        city_url = f"{self.base_url}/schools/{city_slug}"
        highest_visible_page: Optional[int] = None
        duplicate_hits = 0
        non_sequential_transition: Optional[Dict[str, int]] = None
        repeated_signature: Optional[Dict[str, int]] = None
        stop_reason = "unknown"

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(city_url, wait_until="networkidle", timeout=120000)
            await page.wait_for_selector(".hover-card, .card", timeout=120000)

            initial_visible_last_page = await self._get_visible_last_page_number(page)
            if initial_visible_last_page:
                highest_visible_page = initial_visible_last_page
                print(f"Detected at least {initial_visible_last_page} pages for {city_slug}")

            while True:
                current_page = await self._get_active_page_number(page)
                pagination_snapshot = await self._get_pagination_snapshot(page, current_page)
                if pagination_snapshot["max_visible_page"]:
                    highest_visible_page = max(highest_visible_page or 0, pagination_snapshot["max_visible_page"])

                if current_page in scraped_pages:
                    stop_reason = "repeated_page"
                    print(f"Page {current_page} was already visited, stopping")
                    break

                if scraped_pages and current_page != scraped_pages[-1] + 1:
                    non_sequential_transition = {
                        "from_page": scraped_pages[-1],
                        "to_page": current_page,
                    }
                    stop_reason = "non_sequential_page"
                    print(f"Unexpected page jump from {scraped_pages[-1]} to {current_page}, stopping")
                    break

                scraped_pages.append(current_page)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1500)

                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")
                cards = self._extract_cards(soup, city_slug)
                print(f"Page {current_page}: found {len(cards)} cards")

                page_school_keys = set()
                new_schools_on_page = 0
                duplicate_hits_on_page = 0
                cross_city_skips_on_page = 0
                missing_slug_skips_on_page = 0
                for position, card in enumerate(cards, start=1):
                    school = self.parse_school_card(card, city_slug, current_page, position)
                    if not school.get("name"):
                        continue

                    slug = school.get("slug", "")
                    if not slug:
                        missing_slug_skips_on_page += 1
                        continue

                    slug_city = self.extract_city_from_slug(slug)
                    if slug_city != city_slug:
                        cross_city_skips_on_page += 1
                        continue

                    dedupe_key = slug
                    page_school_keys.add(dedupe_key)
                    if dedupe_key in seen_school_keys:
                        duplicate_hits += 1
                        duplicate_hits_on_page += 1
                        continue

                    seen_school_keys.add(dedupe_key)
                    all_schools.append(school)
                    self._save_school_about(city_slug, school)
                    new_schools_on_page += 1

                page_signature = tuple(sorted(page_school_keys))
                signature_seen_on_page = None
                if page_signature and page_signature in page_signatures:
                    signature_seen_on_page = page_signatures[page_signature]
                    if signature_seen_on_page != current_page:
                        repeated_signature = {
                            "page": current_page,
                            "matches_page": signature_seen_on_page,
                        }
                else:
                    page_signatures[page_signature] = current_page

                page_stats.append(
                    {
                        "page": current_page,
                        "cards_found": len(cards),
                        "unique_schools_found": len(page_school_keys),
                        "new_schools_saved": new_schools_on_page,
                        "duplicate_hits": duplicate_hits_on_page,
                        "cross_city_skips": cross_city_skips_on_page,
                        "missing_slug_skips": missing_slug_skips_on_page,
                        "visible_numbers": pagination_snapshot["visible_numbers"],
                        "visible_last_page": pagination_snapshot["max_visible_page"],
                        "has_exact_next": pagination_snapshot["has_exact_next"],
                        "signature_seen_on_page": signature_seen_on_page,
                    }
                )

                if cross_city_skips_on_page:
                    print(f"Page {current_page}: skipped {cross_city_skips_on_page} cards from other cities")
                if missing_slug_skips_on_page:
                    print(f"Page {current_page}: skipped {missing_slug_skips_on_page} cards without school slugs")

                self.stats["total_pages"] += 1
                print(f"Page {current_page}: saved {new_schools_on_page} new schools | total {len(all_schools)}")

                if repeated_signature:
                    stop_reason = "repeated_page_content"
                    print(
                        f"Page {current_page} repeated the same school set as page {repeated_signature['matches_page']}, stopping"
                    )
                    break

                if self.max_pages and current_page >= self.max_pages:
                    stop_reason = "max_pages_reached"
                    print(f"Reached max_pages={self.max_pages}, stopping early")
                    break

                if not pagination_snapshot["has_exact_next"]:
                    if pagination_snapshot["max_visible_page"] and current_page >= pagination_snapshot["max_visible_page"]:
                        stop_reason = "reached_end"
                    else:
                        stop_reason = "next_page_unavailable"
                    print(f"No exact next page available after page {current_page}")
                    break

                moved = await self._go_to_next_page(page, current_page)
                if not moved:
                    stop_reason = "next_page_click_failed"
                    print(f"Failed to move from page {current_page} to page {current_page + 1}")
                    break

            await browser.close()

        self.stats["processed_cities"] += 1
        self.stats["total_schools"] += len(all_schools)

        saved_school_folder_count = self._count_saved_school_folders(city_dir)
        max_pages_limited = stop_reason == "max_pages_reached"
        validation_errors = self._validate_city_run(
            city_slug=city_slug,
            scraped_pages=scraped_pages,
            highest_visible_page=highest_visible_page,
            stop_reason=stop_reason,
            page_stats=page_stats,
            non_sequential_transition=non_sequential_transition,
            repeated_signature=repeated_signature,
            saved_school_folder_count=saved_school_folder_count,
            total_schools=len(all_schools),
            max_pages_limited=max_pages_limited,
        )
        validation_passed = not validation_errors

        city_result = {
            "city": city_slug,
            "total_schools": len(all_schools),
            "pages_scraped": len(scraped_pages),
            "listing_only": True,
            "scraped_at": datetime.now().isoformat(),
            "stop_reason": stop_reason,
            "completed": stop_reason == "reached_end" and validation_passed,
            "max_pages_limited": max_pages_limited,
            "validation_passed": validation_passed,
            "validation_errors": validation_errors,
            "pages_visited": scraped_pages,
            "highest_visible_page_seen": highest_visible_page,
            "pages_with_zero_new_schools": [stat["page"] for stat in page_stats if stat["new_schools_saved"] == 0],
            "duplicate_hits": duplicate_hits,
            "cross_city_skips": sum(stat["cross_city_skips"] for stat in page_stats),
            "missing_slug_skips": sum(stat["missing_slug_skips"] for stat in page_stats),
            "saved_school_folders": saved_school_folder_count,
            "page_stats": page_stats,
        }
        (city_dir / "_city.json").write_text(json.dumps(city_result, indent=2, ensure_ascii=False))

        if validation_passed:
            print(f"Completed {city_slug}: {city_result['total_schools']} schools from {city_result['pages_scraped']} pages")
        else:
            print(f"Validation failed for {city_slug}")
            for error in validation_errors:
                print(f"  - {error}")

        return city_result

    async def run(self) -> Dict[str, Dict[str, Any]]:
        self.stats["start_time"] = datetime.now().isoformat()
        self.output_dir.mkdir(parents=True, exist_ok=True)

        city_results: Dict[str, Dict[str, Any]] = {}
        try:
            for city in self.cities:
                city_results[city] = await self.scrape_city_listing(city)
                if not city_results[city].get("validation_passed", False):
                    first_error = city_results[city].get("validation_errors", ["unknown validation failure"])[0]
                    raise RuntimeError(f"{city} scrape failed validation: {first_error}")
            return city_results
        finally:
            self.stats["end_time"] = datetime.now().isoformat()
            self._save_run_summary(city_results)

            print(f"\n{'=' * 60}")
            print("LISTING SCRAPE SUMMARY")
            print(f"{'=' * 60}")
            print(f"Cities processed: {self.stats['processed_cities']}/{self.stats['total_cities']}")
            print(f"Total pages scraped: {self.stats['total_pages']}")
            print(f"Total schools saved: {self.stats['total_schools']}")
            print(f"Output directory: {self.output_dir}")
            print(f"{'=' * 60}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="YellowSlate listing scraper")
    parser.add_argument("--cities", nargs="+", help="Cities to scrape. Defaults to cities_to_scrape.txt")
    parser.add_argument("--output-dir", default="scraped_data", help="Directory to save scraped output")
    parser.add_argument("--max-pages", type=int, help="Optional page limit for testing")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    scraper = YellowScraper(output_dir=args.output_dir, cities=args.cities, max_pages=args.max_pages)
    await scraper.run()


if __name__ == "__main__":
    asyncio.run(main())
