const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');

// Configuration
const CITIES = [
  'mumbai', 'delhi', 'hyderabad', 'bangalore', 'chennai', 'kolkata',
  'pune', 'ahmedabad', 'surat', 'jaipur', 'lucknow', 'kanpur',
  'nagpur', 'indore', 'thane', 'bhopal', 'patna', 'vadodara',
  'ghaziabad', 'ludhiana', 'agra', 'nashik', 'pune', 'rajkot'
];

const BASE_URL = 'https://yellowslate.com';

async function scrapeCity(citySlug) {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
  
  try {
    // Navigate to city page
    const url = `${BASE_URL}/schools/${citySlug}`;
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });
    
    // Get pagination info
    const paginationData = await page.evaluate(() => {
      const paginationText = document.querySelector('.pagination .page-item.active')?.textContent;
      const totalItemsText = document.querySelector('.pt-3')?.textContent;
      return {
        paginationText,
        totalItemsText
      };
    });
    
    // Get total pages
    let totalPages = 1;
    if (paginationData.paginationText) {
      const match = paginationData.paginationText.match(/(\d+)$/);
      if (match) totalPages = parseInt(match[1]);
    }
    
    console.log(`Processing ${citySlug}: ${totalPages} pages total`);
    
    const allSchools = [];
    
    // Process each page
    for (let pageNum = 1; pageNum <= totalPages; pageNum++) {
      console.log(`  Page ${pageNum}/${totalPages}`);
      
      if (pageNum > 1) {
        await page.goto(`${url}?page=${pageNum}`, { waitUntil: 'networkidle2', timeout: 60000 });
      }
      
      // Extract school data
      const pageSchools = await page.evaluate(() => {
        const schools = [];
        const cards = document.querySelectorAll('.hover-card');
        
        cards.forEach(card => {
          try {
            const schoolData = {
              city: window.location.pathname.split('/')[2] || '',
              name: card.querySelector('.card-title')?.textContent.trim(),
              address: card.querySelector('.card-text')?.textContent.trim(),
              fees: card.querySelector('.card-text.small.fw-bold')?.textContent.trim(),
              board: card.querySelector('.bg-primary.rounded-2.text-xs.px-2.py-1')?.textContent.trim(),
              link: card.querySelector('a')?.href,
              phone: null,
              website: null,
              established: null,
              email: null
            };
            
            // Try to get additional details from card footer or other elements
            const footerLinks = card.querySelectorAll('.card-footer a');
            footerLinks.forEach(link => {
              const href = link.href.toLowerCase();
              if (href.includes('tel:')) {
                schoolData.phone = link.textContent.trim();
              } else if (href.includes('mailto:')) {
                schoolData.email = link.textContent.trim();
              }
            });
            
            schools.push(schoolData);
          } catch (error) {
            console.error('Error parsing school card:', error);
          }
        });
        
        return schools;
      });
      
      allSchools.push(...pageSchools);
    }
    
    return {
      city: citySlug,
      totalSchools: allSchools.length,
      schools: allSchools
    };
    
  } catch (error) {
    console.error(`Error scraping ${citySlug}:`, error.message);
    return {
      city: citySlug,
      error: error.message,
      schools: []
    };
  } finally {
    await browser.close();
  }
}

async function main() {
  console.log('Starting school data extraction...');
  console.log(`Cities to process: ${CITIES.length}`);
  
  const results = {};
  
  for (const city of CITIES) {
    try {
      const cityData = await scrapeCity(city);
      results[city] = cityData;
      
      // Save intermediate results
      await fs.writeFile(
        path.join('scraped_data', `${city}.json`),
        JSON.stringify(cityData, null, 2)
      );
      
      console.log(`  ✓ ${city}: ${cityData.schools.length} schools found\n`);
      
    } catch (error) {
      console.error(`  ✗ ${city}: ${error.message}\n`);
      results[city] = { error: error.message, schools: [] };
    }
  }
  
  // Save final results
  await fs.mkdir('scraped_data', { recursive: true });
  await fs.writeFile(
    path.join('scraped_data', 'all_cities.json'),
    JSON.stringify(results, null, 2)
  );
  
  console.log('Scraping completed!');
  console.log(`Total cities processed: ${Object.keys(results).length}`);
  console.log(`Total schools found: ${Object.values(results).reduce((sum, city) => sum + (city.schools?.length || 0), 0)}`);
}

// Run with error handling
main().catch(console.error);
