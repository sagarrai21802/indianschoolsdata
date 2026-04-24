import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def test():
    url = "https://yellowslate.com/schools/mumbai"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=30) as response:
                if response.status == 200:
                    html = await response.text()
                    print(f"Fetched {len(html)} characters")
                    soup = BeautifulSoup(html, 'html.parser')
                    cards = soup.find_all(class_='hover-card')
                    print(f"Found {len(cards)} hover-card elements")
                    if not cards:
                        cards = soup.find_all(class_='card')
                        print(f"Found {len(cards)} card elements")
                    if cards:
                        card = cards[0]
                        title = card.find(class_='card-title')
                        print(f"First card title: {title.text.strip() if title else 'None'}")
                else:
                    print(f"Failed to fetch {url}: Status {response.status}")
        except Exception as e:
            print(f"Error fetching {url}: {e}")

if __name__ == "__main__":
    asyncio.run(test())
