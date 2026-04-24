import asyncio
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import aiohttp
from bs4 import BeautifulSoup
import time
import random
from datetime import datetime

class YellowScraper:
    def __init__(self, output_dir='scraped_data', cities_file='cities_to_scrape.txt'):
        self.base_url = "https://yellowslate.com"
        
        # Read cities from file
        self.cities = []
        if os.path.exists(cities_file):
            with open(cities_file, 'r') as f:
                self.cities = [line.strip() for line in f if line.strip()]
            print(f"Loaded {len(self.cities)} cities from {cities_file}")
        else:
            print(f"{cities_file} not found, using default cities")
            self.cities = ['mumbai', 'delhi', 'hyderabad', 'bangalore', 'chennai',
                           'kolkata', 'pune', 'ahmedabad', 'surat', 'jaipur']
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        self.output_dir = output_dir
        self.session = None
        self.stats = {
            'total_cities': len(self.cities),
            'processed_cities': 0,
            'total_schools': 0,
            'total_pages': 0,
            'failed_schools': 0,
            'start_time': None,
            'end_time': None
        }

    async def create_session(self):
        """Create aiohttp session with proper headers"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=60, connect=30)
            self.session = aiohttp.ClientSession(headers=self.headers, timeout=timeout)

    async def close_session(self):
        """Close aiohttp session"""
        if self.session is not None:
            await self.session.close()
            self.session = None

    async def fetch_page(self, url: str, retries: int = 3) -> Optional[str]:
        """Fetch a page with retry logic and error handling"""
        if self.session is None:
            await self.create_session()
        
        for attempt in range(retries):
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status == 404:
                        print(f"    Page not found: {url}")
                        return None
                    elif response.status == 429:
                        # Rate limited - wait longer
                        wait_time = (attempt + 1) * 10
                        print(f"    Rate limited, waiting {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        print(f"    HTTP {response.status} for {url}")
                        if attempt < retries - 1:
                            await asyncio.sleep((attempt + 1) * 5)
                            continue
                        return None
            except asyncio.TimeoutError:
                print(f"    Timeout on attempt {attempt + 1}/{retries} for {url}")
                if attempt < retries - 1:
                    await asyncio.sleep((attempt + 1) * 5)
                    continue
            except Exception as e:
                print(f"    Error fetching {url}: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep((attempt + 1) * 5)
                    continue
        
        return None

    def extract_school_id_from_slug(self, slug: str) -> str:
        """Extract school ID from slug"""
        # Extract ID from slug like /school/mumbai/school-name-id
        parts = slug.strip('/').split('/')
        if len(parts) >= 3:
            return parts[-1]
        return slug

    def parse_monetary_value(self, text: str) -> Dict[str, Any]:
        """Parse fee text into structured data"""
        if not text:
            return {'min': None, 'max': None, 'currency': 'INR', 'period': 'annually'}
        
        # Find all numbers in the text
        numbers = re.findall(r'[\d,]+', text.replace(',', ''))
        
        result = {'min': None, 'max': None, 'currency': 'INR', 'period': 'annually'}
        
        if numbers:
            nums = [int(n) for n in numbers if int(n) > 0]
            if nums:
                result['min'] = min(nums)
                result['max'] = max(nums)
        
        # Detect period
        text_lower = text.lower()
        if 'month' in text_lower or 'monthly' in text_lower or 'per month' in text_lower:
            result['period'] = 'monthly'
        elif 'term' in text_lower or 'semester' in text_lower:
            result['period'] = 'semester'
        elif 'quarter' in text_lower:
            result['period'] = 'quarterly'
        
        return result

    async def scrape_school_detail(self, slug: str, listing_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Scrape detailed information from a school's individual page"""
        url = f"{self.base_url}{slug}"
        html = await self.fetch_page(url)
        
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        school_id = self.extract_school_id_from_slug(slug)
        
        school = {
            'id': school_id,
            'name': listing_data.get('name', '').replace(' - ', '').strip(),
            'slug': slug,
            'city': listing_data.get('city', ''),
            'locality': listing_data.get('locality', ''),
        }
        
        # Initialize structured data extraction variables
        structured_fees = None
        structured_board = None
        structured_established = None
        structured_grades = None
        structured_category = None
        structured_address = None
        structured_contact = {}
        
        # Extract from Next.js props (__NEXT_DATA__ or similar)
        next_data_script = soup.find('script', id='__NEXT_DATA__')
        if next_data_script:
            try:
                next_data = json.loads(next_data_script.string or '{}')
                
                def find_in_props(obj, keys_to_find):
                    """Recursively find keys in nested dict"""
                    results = {}
                    if isinstance(obj, dict):
                        for key, value in obj.items():
                            if key in keys_to_find:
                                results[key] = value
                            if isinstance(value, (dict, list)):
                                nested = find_in_props(value, keys_to_find)
                                if nested:
                                    results.update(nested)
                    elif isinstance(obj, list):
                        for item in obj:
                            nested = find_in_props(item, keys_to_find)
                            if nested:
                                results.update(nested)
                    return results
                
                props = find_in_props(next_data, ['feeInfoArray', 'schoolData', 'school', 'pageProps'])
                
                # Extract fee info
                if 'feeInfoArray' in props and isinstance(props['feeInfoArray'], list):
                    fees = props['feeInfoArray']
                    if fees and isinstance(fees[0], dict):
                        fee_data = fees[0]
                        structured_fees = {
                            'min': int(fee_data.get('min_fee', 0)) if fee_data.get('min_fee') else None,
                            'max': int(fee_data.get('max_fee', 0)) if fee_data.get('max_fee') else None,
                            'currency': 'INR',
                            'period': 'annually'
                        }
                        if fee_data.get('curriculum'):
                            structured_board = fee_data.get('curriculum')
                
                # Extract school data
                if 'schoolData' in props and isinstance(props['schoolData'], dict):
                    school_data = props['schoolData']
                    if not structured_board and school_data.get('curriculum'):
                        structured_board = school_data.get('curriculum')
                    if school_data.get('address'):
                        structured_address = school_data.get('address')
                    if school_data.get('phone'):
                        structured_contact['phone'] = school_data.get('phone')
                    if school_data.get('email'):
                        structured_contact['email'] = school_data.get('email')
                
                # Extract page props
                if 'pageProps' in props and isinstance(props['pageProps'], dict):
                    page_props = props['pageProps']
                    if not structured_board and page_props.get('curriculum'):
                        structured_board = page_props.get('curriculum')
                    if page_props.get('address'):
                        structured_address = page_props.get('address')
            except:
                pass
        
        # Try to extract address from page
        address_elem = soup.find('div', class_=re.compile(r'address|location', re.I))
        if not address_elem:
            address_elem = soup.find('p', class_=re.compile(r'address|location', re.I))
        if address_elem:
            school['address'] = address_elem.get_text(strip=True)
        elif structured_address:
            school['address'] = structured_address
        elif listing_data.get('address'):
            school['address'] = listing_data['address']
        else:
            school['address'] = school['locality']
        
        # Extract pincode from address
        if school.get('address'):
            pincodes = re.findall(r'\b\d{6}\b', school['address'])
            if pincodes:
                school['pincode'] = pincodes[0]
        
        # Extract board
        board_elem = soup.find(class_=re.compile(r'board|curriculum', re.I))
        if board_elem:
            school['board'] = board_elem.get_text(strip=True)
        elif structured_board:
            school['board'] = structured_board
        elif listing_data.get('board'):
            school['board'] = listing_data['board']
        else:
            school['board'] = ''
        
        # Extract medium
        medium_elem = soup.find(string=re.compile(r'Medium\s*:', re.I))
        if medium_elem:
            parent = medium_elem.parent
            medium_text = parent.get_text() if parent else medium_elem
            mediums = re.findall(r'Medium\s*[:\-]\s*([A-Za-z\s]+)', medium_text)
            if mediums:
                school['medium'] = mediums[0].strip()
            else:
                school['medium'] = 'English'
        else:
            school['medium'] = 'English'
        
        # Extract school type
        school['school_type'] = listing_data.get('category', 'Private')
        
        # Extract established year
        established_elem = soup.find(string=re.compile(r'Established|Founded|Year', re.I))
        if established_elem:
            parent = established_elem.parent
            est_text = parent.get_text() if parent else established_elem
            years = re.findall(r'(?:Established|Founded|Year)[\s:]*(\d{4})', est_text)
            if not years:
                years = re.findall(r'(\d{4})', est_text)
            if years:
                school['established'] = years[0]
        elif structured_established:
            school['established'] = structured_established
        elif listing_data.get('established'):
            school['established'] = listing_data['established']
        else:
            school['established'] = ''
        
        # Extract grades/classes
        class_elem = soup.find(string=re.compile(r'Class|Grade|Grades', re.I))
        if class_elem:
            parent = class_elem.parent
            class_text = parent.get_text() if parent else class_elem
            school['grades'] = class_text.strip()
        elif structured_grades:
            school['grades'] = structured_grades
        elif listing_data.get('classes'):
            school['grades'] = listing_data['classes']
        else:
            school['grades'] = ''
        
        # Extract fees - prefer structured data
        if structured_fees:
            school['fees'] = structured_fees
            school['fees_text'] = f"₹{structured_fees.get('min', '')} - ₹{structured_fees.get('max', '')} lakhs/year" if structured_fees.get('min') else ""
        else:
            fee_elem = soup.find(class_=re.compile(r'fee|amount|price', re.I))
            if fee_elem:
                fee_text = fee_elem.get_text(strip=True)
                school['fees'] = self.parse_monetary_value(fee_text)
                school['fees_text'] = fee_text
            elif listing_data.get('fees'):
                if isinstance(listing_data['fees'], dict):
                    school['fees'] = listing_data['fees']
                else:
                    school['fees'] = self.parse_monetary_value(str(listing_data['fees']))
            else:
                school['fees'] = self.parse_monetary_value(listing_data.get('fees_text', ''))
                school['fees_text'] = listing_data.get('fees_text', '')
        
        # Extract contact info - prefer structured data
        if structured_contact:
            school['contact'] = structured_contact
        else:
            school['contact'] = {}
            phone_elem = soup.find('a', href=re.compile(r'tel:'))
            if phone_elem:
                school['contact']['phone'] = phone_elem.get('href', '').replace('tel:', '').strip()
            elif listing_data.get('phone'):
                school['contact']['phone'] = listing_data['phone']
            
            email_elem = soup.find('a', href=re.compile(r'mailto:'))
            if email_elem:
                school['contact']['email'] = email_elem.get('href', '').replace('mailto:', '').strip()
            
            website_elem = soup.find('a', href=re.compile(r'http'))
            if website_elem and 'yellowslate' not in website_elem.get('href', ''):
                school['contact']['website'] = website_elem.get('href', '').strip()
            elif listing_data.get('website'):
                school['contact']['website'] = listing_data['website']
        
        # Extract facilities/amenities
        facilities = []
        facility_elems = soup.find_all(class_=re.compile(r'facility|amenity|feature|sport', re.I))
        for elem in facility_elems:
            text = elem.get_text(strip=True)
            if text and len(text) < 50:
                facilities.append(text)
        
        # Also look for sports facilities
        sports_section = soup.find(class_=re.compile(r'sport', re.I))
        if sports_section:
            sport_items = sports_section.find_all('div', recursive=False)
            for item in sport_items:
                text = item.get_text(strip=True)
                if text:
                    facilities.append(text)
        
        # Extract from images - look for sports facilities in img alt text
        img_elems = soup.find_all('img', alt=re.compile(r'sport|facility', re.I))
        for img in img_elems:
            alt = img.get('alt', '')
            if alt and alt not in facilities:
                facilities.append(alt)
        
        # Extract from structured data if available
        if 'props' in locals() and isinstance(props, dict):
            # Look for sports/facilities in props
            sports = find_in_props(props, ['sports', 'facilities', 'amenities'])
            if sports:
                for key, value in sports.items():
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, str) and item not in facilities:
                                facilities.append(item)
                    elif isinstance(item, str) and item not in facilities:
                        facilities.append(item)
        
        school['facilities'] = list(set(facilities))[:20]  # Limit to 20 unique facilities
        
        # Extract admission info
        admission_elem = soup.find(class_=re.compile(r'admission', re.I))
        if admission_elem:
            admission_text = admission_elem.get_text(strip=True).lower()
            if 'open' in admission_text:
                school['admission'] = {'status': 'open'}
            elif 'close' in admission_text:
                school['admission'] = {'status': 'closed'}
        else:
            school['admission'] = {'status': 'open'}
        
        # Extract reviews and rating info
        rating_elem = soup.find(class_=re.compile(r'rating|review', re.I))
        if rating_elem:
            rating_text = rating_elem.get_text(strip=True)
            ratings = re.findall(r'[\d.]+', rating_text)
            if ratings:
                school['rating'] = float(ratings[0])
        
        review_count_elem = soup.find(string=re.compile(r'[\d,]+\s*(review|rating)', re.I))
        if review_count_elem:
            review_text = review_count_elem.get_text(strip=True)
            counts = re.findall(r'[\d,]+', review_text)
            if counts:
                school['reviews_count'] = int(counts[0].replace(',', ''))
        
        # If we have data from the listing page, add it
        if listing_data.get('rating'):
            school['rating'] = float(listing_data.get('rating', 0))
        if listing_data.get('reviews_count'):
            school['reviews_count'] = listing_data['reviews_count']
        
        # Extract principal name (not commonly available)
        principal_elem = soup.find(string=re.compile(r'Principal|Headmaster|Director', re.I))
        if principal_elem:
            parent = principal_elem.parent
            principal_text = parent.get_text() if parent else principal_elem
            names = re.findall(r'(?:Principal|Headmaster|Director)[\s:]*([A-Za-z\s]+)', principal_text)
            if names:
                school['principal'] = names[0].strip()
        
        # Extract images
        images = []
        img_elems = soup.find_all('img', src=re.compile(r'yellowslate|school', re.I))
        for img in img_elems[:10]:  # Limit to first 10
            src = img.get('src', '')
            if src and 'yellowslate' in src:
                # Convert next/image URLs to original
                if '_next/image' in src:
                    # Extract URL from next/image format
                    url_match = re.search(r'url=(https?[^&]+)', src)
                    if url_match:
                        src = url_match.group(1)
                images.append(src)
        
        school['images'] = images
        school['scraped_at'] = datetime.now().isoformat()
        
        return school

    async def scrape_city_listing(self, city_slug: str) -> List[Dict[str, Any]]:
        """Scrape all schools from a city listing page (with pagination)"""
        all_schools = []
        seen_school_slugs = set()
        page_num = 1
        max_pages = 50  # Safety limit
        consecutive_empty_pages = 0
        
        while page_num <= max_pages and consecutive_empty_pages < 3:
            url = f"{self.base_url}/schools/{city_slug}"
            if page_num > 1:
                url += f"?page={page_num}"
            
            print(f"    Fetching page {page_num}: {url}")
            html = await self.fetch_page(url)
            
            if not html:
                print(f"    No HTML returned")
                consecutive_empty_pages += 1
                page_num += 1
                continue
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find school cards - try multiple selectors
            cards = []
            
            # Try hover-card class first
            cards = soup.find_all(class_='hover-card')
            if not cards:
                # Try regular card class
                cards = soup.find_all(class_='card')
            if not cards:
                # Try other possible card classes
                for card_class in ['school-card', 'listing-card', 'result-card', 'school-listing']:
                    cards = soup.find_all(class_=card_class)
                    if cards:
                        break
            
            # If still no cards, try finding links to school pages
            if not cards:
                school_links = soup.find_all('a', href=re.compile(rf'/school/{city_slug}/'))
                # Group links by their parent container
                seen_containers = set()
                for link in school_links:
                    # Find parent container
                    parent = link.find_parent(['div', 'li', 'article'])
                    if parent and parent not in seen_containers:
                        seen_containers.add(parent)
                        cards.append(parent)
            
            print(f"    Found {len(cards)} cards on page {page_num}")
            
            if not cards:
                consecutive_empty_pages += 1
                print(f"    No cards found (empty page {consecutive_empty_pages}/3)")
                page_num += 1
                await asyncio.sleep(2)
                continue
            
            # Reset empty page counter since we found cards
            consecutive_empty_pages = 0
            
            # Parse each card
            new_schools_on_page = 0
            for card in cards:
                try:
                    school_data = self.parse_school_card(card, city_slug)
                    if not school_data or not school_data.get('name'):
                        continue
                    
                    # Get slug for deduplication
                    slug = school_data.get('slug', '')
                    school_name = school_data['name']
                    
                    # Create deduplication key
                    dedupe_key = slug if slug else school_name
                    
                    # Check for duplicates
                    if dedupe_key and dedupe_key not in seen_school_slugs:
                        seen_school_slugs.add(dedupe_key)
                        all_schools.append(school_data)
                        new_schools_on_page += 1
                except Exception as e:
                    print(f"    Error parsing card: {e}")
                    continue
            
            print(f"    New schools on page: {new_schools_on_page}")
            print(f"    Total unique schools so far: {len(all_schools)}")
            
            # Check for pagination - look for next page link
            has_more_pages = False
            
            # Strategy 1: Look for next button in pagination
            pagination = soup.find(class_=re.compile(r'pagination|page-nav', re.I))
            if pagination:
                next_btn = pagination.find('a', string=re.compile(r'next|»|›', re.I))
                if not next_btn:
                    # Look for next page number
                    current_active = pagination.find(class_=re.compile(r'active|current', re.I))
                    if current_active:
                        current_page_elem = current_active.find(string=re.compile(r'\d+'))
                        if current_page_elem:
                            current = int(current_page_elem.strip())
                            # Look for next page number link
                            next_num = str(current + 1)
                            for link in pagination.find_all('a'):
                                if link.get_text(strip=True) == next_num:
                                    has_more_pages = True
                                    break
                else:
                    has_more_pages = True
            
            # Strategy 2: Check for next page link specifically
            # Look for pagination links that indicate next page
            if not has_more_pages:
                # Check for numbered page links beyond current page
                page_links = soup.find_all('a', href=re.compile(r'page=\d+'))
                for link in page_links:
                    href = link.get('href', '')
                    page_match = re.search(r'page=(\d+)', href)
                    if page_match:
                        link_page = int(page_match.group(1))
                        if link_page > page_num:
                            has_more_pages = True
                            break
                
                # If no numbered links found, look for "next" text in any link
                if not has_more_pages:
                    next_links = soup.find_all('a', string=re.compile(r'next|\»|›|»', re.I))
                    for link in next_links:
                        href = link.get('href', '')
                        if href and 'disabled' not in link.get('class', []):
                            has_more_pages = True
                            break
            
            # Strategy 3: Check URL pattern - if page 1 has results, try page 2 at least
            if page_num == 1 and len(all_schools) > 0:
                # Try to detect last page by checking if we're on the last pagination item
                pagination_items = pagination.find_all(class_=re.compile(r'page-item', re.I)) if pagination else []
                if pagination_items:
                    # Check structure
                    item_texts = [item.get_text(strip=True) for item in pagination_items]
                    # Look for last page number
                    last_num = None
                    for i, txt in enumerate(item_texts):
                        if txt.isdigit() and i < len(item_texts) - 1:
                            last_num = txt
                    if last_num and str(page_num) == last_num:
                        has_more_pages = False
            
            # Safety: if we're getting way too many schools, there's probably an infinite loop
            if len(all_schools) > 500:
                print(f"    WARNING: Over 500 schools found, stopping pagination")
                break
            
            if has_more_pages:
                page_num += 1
                await asyncio.sleep(random.uniform(2, 4))
            else:
                print(f"    No more pages detected")
                break  # Exit the while loop since there are no more pages
        
        self.stats['total_pages'] += page_num - 1
        print(f"  Completed {city_slug}: {len(all_schools)} schools from {page_num - 1} pages")
        return all_schools

    def parse_school_card(self, card, city_slug: str) -> Dict[str, Any]:
        """Parse individual school card from listing page"""
        school = {
            'name': '',
            'city': city_slug,
            'locality': '',
            'address': '',
            'pincode': '',
            'board': '',
            'medium': 'English',
            'school_type': '',
            'established': '',
            'grades': '',
            'fees': {'min': None, 'max': None, 'currency': 'INR', 'period': 'annually'},
            'fees_text': '',
            'contact': {'phone': '', 'email': '', 'website': ''},
            'facilities': [],
            'admission': {'status': 'open'},
            'rating': None,
            'reviews_count': None,
            'principal': '',
            'images': [],
            'slug': ''
        }
        
        # Extract name
        name_elem = card.find(class_=re.compile(r'title|name|school-name', re.I))
        if not name_elem:
            # Try h2, h3, h4 tags
            for tag in ['h2', 'h3', 'h4', 'h5']:
                name_elem = card.find(tag)
                if name_elem:
                    break
        
        if name_elem:
            school['name'] = name_elem.get_text(strip=True)
            # Clean up name - remove city references
            school['name'] = re.sub(rf'\s*-\s*{city_slug}\s*$', '', school['name'], flags=re.I)
            school['name'] = re.sub(r'\s*-\s*$', '', school['name'])
        
        # Extract link/slug
        link_elem = card.find('a', href=True)
        if link_elem:
            href = link_elem['href']
            if href.startswith('/school/'):
                school['slug'] = href
            elif href.startswith('http'):
                # Extract path from full URL
                path_match = re.match(r'https?://[^/]+(/school/.*)', href)
                if path_match:
                    school['slug'] = path_match.group(1)
        
        # Extract locality/address
        address_elem = card.find(class_=re.compile(r'address|location|locality|card-text', re.I))
        if address_elem:
            school['address'] = address_elem.get_text(strip=True)
            school['locality'] = school['address']
        
        # Extract board
        board_elem = card.find(class_=re.compile(r'board|curriculum|badge', re.I))
        if board_elem:
            school['board'] = board_elem.get_text(strip=True)
        
        # Extract fees
        fee_elem = card.find(class_=re.compile(r'fee|amount|price|fees', re.I))
        if fee_elem:
            fee_text = fee_elem.get_text(strip=True)
            school['fees_text'] = fee_text
            school['fees'] = self.parse_monetary_value(fee_text)
        
        # Extract rating
        rating_elem = card.find(class_=re.compile(r'rating|review-score', re.I))
        if rating_elem:
            rating_text = rating_elem.get_text(strip=True)
            ratings = re.findall(r'[\d.]+', rating_text)
            if ratings:
                school['rating'] = float(ratings[0])
        
        # Extract review count
        review_elem = card.find(class_=re.compile(r'review|rating-count', re.I))
        if review_elem:
            review_text = review_elem.get_text(strip=True)
            counts = re.findall(r'[\d,]+', review_text)
            if counts:
                school['reviews_count'] = int(counts[0].replace(',', ''))
        
        # Extract category/school type
        category_elem = card.find(class_=re.compile(r'category|type|school-type', re.I))
        if category_elem:
            school['school_type'] = category_elem.get_text(strip=True)
        
        return school

    def check_has_next_page(self, soup: BeautifulSoup, current_page: int) -> bool:
        """Check if there are more pages to scrape"""
        # Look for pagination
        pagination = soup.find(class_=re.compile(r'pagination|page-nav|pager', re.I))
        if pagination:
            # Check for next button
            next_btn = pagination.find(string=re.compile(r'next|»|›', re.I))
            if next_btn:
                next_link = next_btn.find_parent('a')
                if next_link and next_link.get('href'):
                    return True
            
            # Check for page numbers beyond current
            page_items = pagination.find_all(class_=re.compile(r'page-item|page-link', re.I))
            if page_items:
                for item in page_items:
                    text = item.get_text(strip=True)
                    if text.isdigit() and int(text) > current_page:
                        return True
            
            # Check if current page is NOT the last
            active = pagination.find(class_=re.compile(r'active|current', re.I))
            if active:
                # Check if there's a non-disabled link after active
                found_active = False
                for sibling in active.find_next_siblings():
                    if sibling.find(class_=re.compile(r'page-link', re.I)):
                        if 'disabled' not in str(sibling.get('class', [])):
                            return True
        
        # Alternative: look for "Showing X of Y" pattern
        showing_text = soup.find(string=re.compile(r'showing|displaying|of \d+', re.I))
        if showing_text:
            text = showing_text.get_text(strip=True)
            # Extract numbers
            nums = re.findall(r'\d+', text)
            if len(nums) >= 2:
                shown = int(nums[0])
                total = int(nums[-1])
                if shown < total:
                    return True
        
        # Check for "Load More" button
        load_more = soup.find(string=re.compile(r'load more|show more', re.I))
        if load_more:
            return True
        
        # Look for school cards - if we see many, there might be more pages
        # But this is unreliable
        
        return False

    async def scrape_city_detailed(self, city_slug: str, listing_schools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Scrape detailed information for each school in a city"""
        detailed_schools = []
        
        for i, listing_data in enumerate(listing_schools, 1):
            slug = listing_data.get('slug')
            if not slug:
                print(f"    [{i}/{len(listing_schools)}] Skipping - no slug")
                continue
            
            print(f"    [{i}/{len(listing_schools)}] Scraping details: {listing_data.get('name', 'Unknown')}")
            
            detailed = await self.scrape_school_detail(slug, listing_data)
            
            if detailed:
                # Merge with listing data
                for key, value in listing_data.items():
                    if key not in detailed or not detailed[key]:
                        detailed[key] = value
                
                detailed_schools.append(detailed)
            else:
                print(f"      Failed to get details, using listing data")
                # Use listing data as fallback
                listing_data['id'] = self.extract_school_id_from_slug(slug)
                listing_data['scraped_at'] = datetime.now().isoformat()
                detailed_schools.append(listing_data)
            
            # Delay between school detail requests
            await asyncio.sleep(random.uniform(1.5, 3))
        
        return detailed_schools

    async def scrape_city(self, city_slug: str) -> Dict[str, Any]:
        """Scrape all schools for a specific city (listing + details)"""
        print(f"\n{'='*60}")
        print(f"Scraping city: {city_slug}")
        print(f"{'='*60}")
        
        city_data = {
            'city': city_slug,
            'total_schools': 0,
            'schools': []
        }
        
        try:
            # Step 1: Scrape listing pages to get all schools
            print(f"  Step 1: Scraping listing pages...")
            listing_schools = await self.scrape_city_listing(city_slug)
            
            if not listing_schools:
                print(f"  No schools found for {city_slug}")
                return city_data
            
            print(f"  Step 2: Scraping detailed info for {len(listing_schools)} schools...")
            
            # Step 2: Scrape detailed info for each school
            detailed_schools = await self.scrape_city_detailed(city_slug, listing_schools)
            
            city_data['schools'] = detailed_schools
            city_data['total_schools'] = len(detailed_schools)
            
            self.stats['total_schools'] += len(detailed_schools)
            self.stats['processed_cities'] += 1
            
            print(f"  ✓ {city_slug}: {len(detailed_schools)} schools scraped")
            
        except Exception as e:
            print(f"  ✗ Error scraping {city_slug}: {e}")
            import traceback
            traceback.print_exc()
        
        return city_data

    async def run(self):
        """Main scraping function"""
        self.stats['start_time'] = datetime.now().isoformat()
        
        # Create output directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(f"{self.output_dir}/schools_by_city", exist_ok=True)
        os.makedirs(f"{self.output_dir}/schools_detailed", exist_ok=True)
        
        all_results = {}
        
        for city in self.cities:
            try:
                city_data = await self.scrape_city(city)
                all_results[city] = city_data
                
                # Save per-city results
                city_file = f"{self.output_dir}/schools_by_city/{city}.json"
                with open(city_file, 'w') as f:
                    json.dump(city_data, f, indent=2)
                print(f"  Saved: {city_file}")
                
                # Save detailed individual school files
                city_detailed_dir = f"{self.output_dir}/schools_detailed/{city}"
                os.makedirs(city_detailed_dir, exist_ok=True)
                
                for school in city_data['schools']:
                    school_slug = school.get('slug', '').strip('/')
                    if school_slug:
                        school_filename = school_slug.split('/')[-1]
                    else:
                        school_filename = f"school_{len(os.listdir(city_detailed_dir))}"
                    
                    school_file = f"{city_detailed_dir}/{school_filename}.json"
                    with open(school_file, 'w') as f:
                        json.dump(school, f, indent=2)
                
                print(f"  Saved {len(city_data['schools'])} detailed school files")
                
            except Exception as e:
                print(f"✗ Error processing {city}: {e}")
                all_results[city] = {'error': str(e), 'schools': []}
                import traceback
                traceback.print_exc()
        
        # Save all results
        all_cities_file = f"{self.output_dir}/all_cities_complete.json"
        with open(all_cities_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"\nSaved: {all_cities_file}")
        
        # Generate summary
        self.stats['end_time'] = datetime.now().isoformat()
        
        summary = {
            'statistics': self.stats,
            'cities_processed': self.stats['processed_cities'],
            'total_schools': self.stats['total_schools'],
            'total_pages_scraped': self.stats['total_pages'],
            'cities': {}
        }
        
        for city, data in all_results.items():
            summary['cities'][city] = {
                'total_schools': data.get('total_schools', 0),
                'status': 'complete' if 'error' not in data else 'error'
            }
        
        summary_file = f"{self.output_dir}/all_cities_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"Saved: {summary_file}")
        
        # Print final summary
        print(f"\n{'='*60}")
        print("SCRAPING SUMMARY")
        print(f"{'='*60}")
        print(f"Total cities processed: {self.stats['processed_cities']}/{self.stats['total_cities']}")
        print(f"Total schools found: {self.stats['total_schools']}")
        print(f"Total pages scraped: {self.stats['total_pages']}")
        print(f"Output directory: {self.output_dir}/")
        print(f"{'='*60}")
        
        await self.close_session()
        return all_results

async def main():
    scraper = YellowScraper()
    await scraper.run()

if __name__ == "__main__":
    asyncio.run(main())
