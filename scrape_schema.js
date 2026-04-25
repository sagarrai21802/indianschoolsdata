const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');

const BASE_URL = 'https://yellowslate.com';
const DEFAULT_SCRAPED_DATA_DIR = path.join(process.cwd(), 'scraped_data');

async function getAllSchools(outputDir = DEFAULT_SCRAPED_DATA_DIR, cities = null) {
  const schools = [];
  const outputPath = path.resolve(outputDir);
  
  let cityDirs = await fs.readdir(outputPath, { withFileTypes: true });
  cityDirs = cityDirs.filter(d => d.isDirectory() && !d.name.startsWith('_'));
  
  for (const cityDir of cityDirs) {
    const citySlug = cityDir.name;
    if (cities && !cities.includes(citySlug)) continue;
    
    const cityPath = path.join(outputPath, citySlug);
    const entries = await fs.readdir(cityPath, { withFileTypes: true });
    
    for (const entry of entries) {
      if (!entry.isDirectory() || entry.name.startsWith('_')) continue;
      
      const aboutPath = path.join(cityPath, entry.name, 'about.json');
      try {
        const aboutData = JSON.parse(await fs.readFile(aboutPath, 'utf-8'));
        if (aboutData.slug) {
          schools.push({ city: citySlug, folder: entry.name, slug: aboutData.slug, name: aboutData.name });
        }
      } catch (e) {
        // Skip files that can't be read
      }
    }
  }
  return schools;
}

function extractJsonLd(html) {
  const schemaData = [];
  const scriptRegex = /<script[^>]*type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/gi;
  let match;
  
  while ((match = scriptRegex.exec(html)) !== null) {
    try {
      const data = JSON.parse(match[1]);
      schemaData.push(data);
    } catch (e) {
      // Skip invalid JSON
    }
  }
  return schemaData;
}

function parseBreadcrumb(data) {
  if (data['@type'] !== 'BreadcrumbList') return null;
  const items = data.itemListElement || [];
  return {
    items: items.map(item => ({
      position: item.position,
      name: item.name,
      url: item.item
    }))
  };
}

function parseLocalBusiness(data) {
  if (data['@type'] !== 'LocalBusiness') return null;
  return {
    name: data.name,
    image: data.image,
    url: data.url,
    telephone: data.telephone,
    address: data.address,
    geo: data.geo
  };
}

function parseReviewSchema(data) {
  if (data['@type'] !== 'Review') return null;
  const itemList = data.itemListElement || [];
  const reviews = itemList.map(review => {
    const itemReviewed = review.itemReviewed || {};
    const author = review.author || {};
    const rating = review.reviewRating || {};
    return {
      school_name: itemReviewed.name,
      school_address: itemReviewed.address,
      school_url: itemReviewed.url,
      aggregate_rating: itemReviewed.aggregateRating,
      author: author.name,
      date_published: review.datePublished,
      rating_value: rating.ratingValue,
      best_rating: rating.bestRating,
      worst_rating: rating.worstRating,
      review_body: review.reviewBody,
      publisher: review.publisher?.name
    };
  });
  return {
    number_of_items: data.numberOfItems,
    reviews
  };
}

function processSchemaData(schemaList) {
  const result = {
    breadcrumbs: [],
    local_business: null,
    reviews: null
  };
  
  for (const schema of schemaList) {
    if (Array.isArray(schema)) {
      for (const item of schema) {
        const breadcrumb = parseBreadcrumb(item);
        if (breadcrumb) result.breadcrumbs = breadcrumb.items;
        
        const localBusiness = parseLocalBusiness(item);
        if (localBusiness) result.local_business = localBusiness;
        
        const reviewSchema = parseReviewSchema(item);
        if (reviewSchema) result.reviews = reviewSchema;
      }
    } else {
      const breadcrumb = parseBreadcrumb(schema);
      if (breadcrumb) result.breadcrumbs = breadcrumb.items;
      
      const localBusiness = parseLocalBusiness(schema);
      if (localBusiness) result.local_business = localBusiness;
      
      const reviewSchema = parseReviewSchema(schema);
      if (reviewSchema) result.reviews = reviewSchema;
    }
  }
  return result;
}

async function scrapeSchoolSchema(browser, school) {
  const { slug, name } = school;
  if (!slug) return null;
  
  const detailUrl = `${BASE_URL}${slug}`;
  const page = await browser.newPage();
  
  try {
    await page.goto(detailUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(2000);
    
    const html = await page.content();
    const schemaList = extractJsonLd(html);
    
    if (!schemaList.length) {
      console.log(`  No JSON-LD schema found for ${name}`);
      return null;
    }
    
    const processed = processSchemaData(schemaList);
    processed.url = detailUrl;
    processed.scraped_at = new Date().toISOString();
    
    return processed;
  } catch (e) {
    console.log(`  Error scraping ${detailUrl}: ${e.message}`);
    return null;
  } finally {
    await page.close();
  }
}

async function run(args = {}) {
  const outputDir = args.outputDir || DEFAULT_SCRAPED_DATA_DIR;
  const cityFilter = args.city || null;
  const limit = args.limit || null;
  
  console.log('Finding schools to process...');
  const schools = await getAllSchools(outputDir, cityFilter);
  console.log(`Found ${schools.length} schools`);
  
  if (limit) {
    schools.splice(limit);
    console.log(`Limited to ${limit} schools`);
  }
  
  const browser = await puppeteer.launch({ headless: true });
  
  let processed = 0;
  let failed = 0;
  
  for (const school of schools) {
    console.log(`Processing: ${school.city}/${school.folder}`);
    
    const schemaData = await scrapeSchoolSchema(browser, school);
    
    if (schemaData) {
      const schemaPath = path.join(outputDir, school.city, school.folder, 'schema.json');
      await fs.writeFile(schemaPath, JSON.stringify(schemaData, null, 2));
      processed++;
      console.log(`  Saved schema.json`);
    } else {
      failed++;
      console.log(`  Failed to get schema data`);
    }
  }
  
  await browser.close();
  
  console.log('\n' + '='.repeat(60));
  console.log('SCHEMA SCRAPE SUMMARY');
  console.log('='.repeat(60));
  console.log(`Total schools: ${schools.length}`);
  console.log(`Processed: ${processed}`);
  console.log(`Failed: ${failed}`);
  console.log('='.repeat(60));
}

function parseArgs() {
  const args = {
    outputDir: DEFAULT_SCRAPED_DATA_DIR,
    city: null,
    limit: null
  };
  
  for (const arg of process.argv.slice(2)) {
    if (arg.startsWith('--output-dir=')) {
      args.outputDir = arg.split('=')[1];
    } else if (arg.startsWith('--city=')) {
      args.city = arg.split('=')[1].split(',').map(c => c.trim().toLowerCase()).filter(Boolean);
    } else if (arg.startsWith('--limit=')) {
      args.limit = parseInt(arg.split('=')[1], 10) || null;
    }
  }
  
  return args;
}

run(parseArgs()).catch(console.error);