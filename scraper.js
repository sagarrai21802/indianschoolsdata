const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');

// Listing-scrape configuration
const CITIES = [
  'mumbai', 'delhi', 'hyderabad', 'bangalore', 'chennai', 'kolkata',
  'pune', 'ahmedabad', 'surat', 'jaipur', 'lucknow', 'kanpur',
  'nagpur', 'indore', 'thane', 'bhopal', 'patna', 'vadodara',
  'ghaziabad', 'ludhiana', 'agra', 'nashik', 'pune', 'rajkot'
];

const BASE_URL = 'https://yellowslate.com';
const DEFAULT_SCRAPED_DATA_DIR = path.join(process.cwd(), 'scraped_data');

function parseArgs(argv = process.argv.slice(2)) {
  const args = {
    details: false,
    limit: null,
    cityFilter: null,
    schoolFilter: null,
    outputDir: DEFAULT_SCRAPED_DATA_DIR,
    failOnErrors: false,
  };

  for (const arg of argv) {
    if (arg === '--details') {
      args.details = true;
    } else if (arg === '--fail-on-errors') {
      args.failOnErrors = true;
    } else if (arg.startsWith('--limit=')) {
      const value = parseInt(arg.split('=')[1], 10);
      args.limit = Number.isFinite(value) && value > 0 ? value : null;
    } else if (arg.startsWith('--city=')) {
      args.cityFilter = new Set(
        arg
          .split('=')[1]
          .split(',')
          .map((value) => value.trim().toLowerCase())
          .filter(Boolean)
      );
    } else if (arg.startsWith('--school=')) {
      args.schoolFilter = new Set(
        arg
          .split('=')[1]
          .split(',')
          .map((value) => value.trim().toLowerCase())
          .filter(Boolean)
      );
    } else if (arg.startsWith('--output-dir=')) {
      const value = arg.split('=')[1].trim();
      if (value) {
        args.outputDir = path.resolve(value);
      }
    }
  }

  return args;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function randomDelay(minMs = 1500, maxMs = 3000) {
  return Math.floor(Math.random() * (maxMs - minMs + 1)) + minMs;
}

function decodeJsonEscapedString(value) {
  if (typeof value !== 'string') {
    return value;
  }

  try {
    return JSON.parse(`"${value}"`);
  } catch (_error) {
    return value;
  }
}

function uniqueStrings(values) {
  return [...new Set(values.filter(Boolean))];
}

function getMetaContent(html, attrName, attrValue) {
  const regex = new RegExp(
    `<meta[^>]+${attrName}=["']${attrValue.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}["'][^>]+content=["']([\\s\\S]*?)["']`,
    'i'
  );
  return decodeJsonEscapedString((html.match(regex) || [])[1] || null);
}

function getLinkHref(html, rel) {
  const regex = new RegExp(
    `<link[^>]+rel=["']${rel.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}["'][^>]+href=["']([\\s\\S]*?)["']`,
    'i'
  );
  return decodeJsonEscapedString((html.match(regex) || [])[1] || null);
}

function flattenStructuredBlock(block) {
  if (Array.isArray(block)) {
    return block.flatMap(flattenStructuredBlock);
  }
  return block && typeof block === 'object' ? [block] : [];
}

function parseJsonCandidate(raw) {
  if (!raw || typeof raw !== 'string') {
    return [];
  }

  const trimmed = raw.trim();
  if (!(trimmed.startsWith('{') || trimmed.startsWith('['))) {
    return [];
  }

  try {
    return flattenStructuredBlock(JSON.parse(trimmed));
  } catch (_error) {
    return [];
  }
}

function extractStructuredData(html) {
  const blocks = [];
  const seen = new Set();

  const directRegex = /<script[^>]+type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi;
  for (const match of html.matchAll(directRegex)) {
    for (const block of parseJsonCandidate(match[1])) {
      const key = JSON.stringify(block);
      if (!seen.has(key)) {
        seen.add(key);
        blocks.push(block);
      }
    }
  }

  const escapedRegex = /dangerouslySetInnerHTML\":\{\"__html\":\"((?:\\.|[^"\\])*)\"\}/g;
  for (const match of html.matchAll(escapedRegex)) {
    const decoded = decodeJsonEscapedString(match[1]);
    for (const block of parseJsonCandidate(decoded)) {
      const key = JSON.stringify(block);
      if (!seen.has(key)) {
        seen.add(key);
        blocks.push(block);
      }
    }
  }

  const byType = {};
  for (const block of blocks) {
    const types = Array.isArray(block['@type']) ? block['@type'] : [block['@type'] || 'Unknown'];
    for (const type of types) {
      if (!byType[type]) {
        byType[type] = [];
      }
      byType[type].push(block);
    }
  }

  return { raw_blocks: blocks, by_type: byType };
}

function extractEmbeddedSchoolProfile(html) {
  const match = html.match(/\\"isUnclaimedSchool\\":(false|true),\\"other\\":(false|true),\\"isClient\\":(false|true),\\"isClaimed\\":(false|true),\\"nearClient\\":\\"([^\\"]+)\\",\\"sub_source\\":\\"([^\\"]+)\\",.*?\\"schoolName\\":\\"([^\\"]+)\\",\\"id\\":(\d+),\\"phone\\":\\"([^\\"]+)\\",\\"enableNavItems\\":\{\\"about\\":(false|true),\\"fee\\":(false|true),\\"gallery\\":(false|true),\\"videos\\":(false|true),\\"location\\":(false|true),\\"faculty\\":(false|true),\\"sports\\":(false|true),\\"reviews\\":(false|true)\}/s);

  if (!match) {
    return null;
  }

  return {
    is_unclaimed_school: match[1] === 'true',
    other: match[2] === 'true',
    is_client: match[3] === 'true',
    is_claimed: match[4] === 'true',
    near_client: decodeJsonEscapedString(match[5]),
    sub_source: decodeJsonEscapedString(match[6]),
    school_name: decodeJsonEscapedString(match[7]),
    school_id: Number(match[8]),
    phone: decodeJsonEscapedString(match[9]),
    enable_nav_items: {
      about: match[10] === 'true',
      fee: match[11] === 'true',
      gallery: match[12] === 'true',
      videos: match[13] === 'true',
      location: match[14] === 'true',
      faculty: match[15] === 'true',
      sports: match[16] === 'true',
      reviews: match[17] === 'true',
    },
  };
}

function extractInstagramPosts(html) {
  const posts = [];
  const postRegex = /\{\\"id\\":(\d+),\\"media_url\\":\\"([^\\"]+)\\",\\"thumbnail_url\\":\\"([^\\"]+)\\",\\"video_url\\":(null|\\"[^\\"]*\\"),\\"instagram_url\\":\\"([^\\"]+)\\",\\"description\\":\\"(.*?)\\",\\"media_type\\":\\"([^\\"]+)\\",\\"source_type\\":\\"([^\\"]+)\\",\\"like_count\\":(\d+),\\"comments_count\\":(\d+),\\"instagram_post_id\\":\\"([^\\"]+)\\",\\"instagram_timestamp\\":\\"([^\\"]+)\\",\\"created_at\\":\\"([^\\"]+)\\"/gs;

  for (const match of html.matchAll(postRegex)) {
    const rawVideo = match[4] === 'null' ? null : match[4].slice(2, -2);
    const videoUrl = rawVideo && !rawVideo.startsWith('$') ? decodeJsonEscapedString(rawVideo) : null;
    posts.push({
      id: Number(match[1]),
      media_url: decodeJsonEscapedString(match[2]),
      thumbnail_url: decodeJsonEscapedString(match[3]),
      video_url: videoUrl,
      instagram_url: decodeJsonEscapedString(match[5]),
      description: decodeJsonEscapedString(match[6]),
      media_type: decodeJsonEscapedString(match[7]),
      source_type: decodeJsonEscapedString(match[8]),
      like_count: Number(match[9]),
      comments_count: Number(match[10]),
      instagram_post_id: decodeJsonEscapedString(match[11]),
      instagram_timestamp: decodeJsonEscapedString(match[12]),
      created_at: decodeJsonEscapedString(match[13]),
    });
  }

  return posts;
}

function extractGalleryImagesFromHtml(html) {
  const urls = [];
  for (const match of html.matchAll(/https:\/\/[^"'\s<>]+/g)) {
    const url = match[0].replace(/\\u0026/g, '&').replace(/\\/g, '');
    if (/\.(jpg|jpeg|png|webp)(\?|$)/i.test(url) && !url.includes('/api/instastories/media/')) {
      urls.push(url);
    }
  }
  return uniqueStrings(urls);
}

function extractApiUrlSamples(html) {
  const urls = [];
  for (const match of html.matchAll(/https:\/\/[^"'\s<>]+/g)) {
    const url = match[0].replace(/\\u0026/g, '&').replace(/\\/g, '');
    if (url.includes('/api/') || url.includes('crm-api.yellowslate.com')) {
      urls.push(url);
    }
  }
  return uniqueStrings(urls).slice(0, 50);
}

function extractPhoneLinks(html) {
  return uniqueStrings([...html.matchAll(/href=["']tel:([^"']+)["']/gi)].map((match) => match[1]));
}

function extractEmails(html) {
  return uniqueStrings([...html.matchAll(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi)].map((match) => match[0]));
}

function extractWebsites(html) {
  const urls = [];
  for (const match of html.matchAll(/https?:\/\/[^"'\s<>]+/gi)) {
    const url = match[0];
    if (!url.includes('yellowslate.com') && !url.includes('instagram.com') && !url.includes('facebook.com')) {
      urls.push(url.replace(/\\u0026/g, '&').replace(/\\/g, ''));
    }
  }
  return uniqueStrings(urls);
}

function extractBoardFromStructuredData(structuredData, about) {
  const breadcrumb = structuredData.by_type.BreadcrumbList?.[0];
  const boardCrumb = breadcrumb?.itemListElement?.find((item) => item?.position === 4)?.name;
  if (boardCrumb) {
    return boardCrumb;
  }

  const localBusinessName = structuredData.by_type.LocalBusiness?.[0]?.name;
  if (localBusinessName && /\b(CBSE|ICSE|IB|IGCSE)\b/i.test(localBusinessName)) {
    return localBusinessName.match(/\b(CBSE|ICSE|IB|IGCSE)\b/i)[1].toUpperCase();
  }

  const metaDescription = structuredData.meta_description;
  if (metaDescription) {
    const boardMatch = metaDescription.match(/,\s*(CBSE|ICSE|IB|IGCSE|State Board)\s*,/i);
    if (boardMatch) {
      return boardMatch[1].toUpperCase();
    }
  }

  return about.board || null;
}

function extractAddress(structuredData, about, metaDescription) {
  const localBusiness = structuredData.by_type.LocalBusiness?.[0];
  const structuredAddress = localBusiness?.address?.streetAddress || localBusiness?.address?.Address || localBusiness?.address?.address || null;
  if (structuredAddress) {
    return structuredAddress;
  }

  if (metaDescription) {
    const match = metaDescription.match(/,\s*(CBSE|ICSE|IB|IGCSE|State Board)\s*,\s*(.*?)\s*,\s*Reviews,\s*Gallery,\s*Fees\./i);
    if (match) {
      return match[2].trim();
    }
  }

  return about.address || null;
}

function extractAggregateRating(structuredData) {
  const aggregateBlocks = structuredData.by_type.AggregateRating || [];
  if (aggregateBlocks.length > 0) {
    return aggregateBlocks[0];
  }

  const reviewContainer = structuredData.by_type.Review?.[0];
  return reviewContainer?.itemListElement?.[0]?.itemReviewed?.aggregateRating || null;
}

function buildRenderingAssessment(signals) {
  if (signals.next_flight_stream) {
    return 'Returns HTML from a Next.js page with embedded React flight data in script tags, not a standalone JSON API response.';
  }
  if (signals.next_data_script) {
    return 'Returns HTML with embedded Next.js data scripts.';
  }
  return 'Returns HTML and requires page parsing rather than a direct JSON endpoint.';
}

function buildContentSummary(profile, structuredData) {
  const localBusiness = structuredData.by_type.LocalBusiness?.length || 0;
  const reviews = structuredData.by_type.Review?.length || 0;
  const sections = profile?.enable_nav_items ? Object.entries(profile.enable_nav_items).filter(([, enabled]) => enabled).map(([name]) => name) : [];
  return `This page exposes detail-page data beyond about.json, including ${localBusiness ? 'LocalBusiness schema' : 'structured schema'}, ${reviews ? 'review schema' : 'page metadata'}, and ${sections.length ? `enabled sections (${sections.join(', ')})` : 'embedded page state'}.`;
}

function buildDetailsPayload({ about, sourceUrl, response, html, structuredData, pageHead, profile, instagramPosts }) {
  structuredData.meta_description = pageHead.meta_description;

  const localBusiness = structuredData.by_type.LocalBusiness?.[0] || null;
  const reviewSchema = structuredData.by_type.Review?.[0] || null;
  const breadcrumb = structuredData.by_type.BreadcrumbList?.[0] || null;
  const aggregateRating = extractAggregateRating(structuredData);
  const phoneLinks = extractPhoneLinks(html);
  const emailCandidates = extractEmails(html);
  const websiteCandidates = extractWebsites(html);
  const mobile = profile?.phone || phoneLinks[0] || about.contact?.phone || null;
  const telephone = localBusiness?.telephone || null;

  const frameworkSignals = {
    next_static_chunks: html.includes('/_next/static/'),
    next_flight_stream: html.includes('self.__next_f.push'),
    next_data_script: html.includes('__NEXT_DATA__'),
    client_render_bailout: html.includes('BAILOUT_TO_CLIENT_SIDE_RENDERING'),
  };

  return {
    id: about.id,
    name: about.name,
    slug: about.slug,
    city: about.city,
    source_url: sourceUrl,
    detail_page: {
      response: {
        status_code: response?.status() || null,
        content_type: response?.headers()?.['content-type'] || null,
        final_url: response?.url() || sourceUrl,
        html_length: html.length,
      },
      url_analysis: {
        page_type: 'school detail page',
        framework_signals: frameworkSignals,
        rendering_assessment: buildRenderingAssessment(frameworkSignals),
      },
      page_head: {
        title: pageHead.title,
        canonical_url: pageHead.canonical_url,
        meta_description: pageHead.meta_description,
        meta_keywords: pageHead.meta_keywords,
        meta_robots: pageHead.meta_robots,
        open_graph: {
          title: pageHead.og_title,
          description: pageHead.og_description,
          url: pageHead.og_url,
          image: pageHead.og_image,
        },
      },
      structured_data: {
        raw_blocks: structuredData.raw_blocks,
        by_type: structuredData.by_type,
        breadcrumb,
        local_business: localBusiness,
        reviews_schema: reviewSchema,
      },
      extracted_school_details: {
        board: extractBoardFromStructuredData(structuredData, about),
        address: extractAddress(structuredData, about, pageHead.meta_description),
        telephone,
        mobile,
        email: localBusiness?.email || emailCandidates[0] || about.contact?.email || null,
        website: localBusiness?.url || websiteCandidates[0] || about.contact?.website || null,
        geo: localBusiness?.geo || null,
        phone_links: phoneLinks,
        aggregate_rating: aggregateRating,
        embedded_school_profile: profile,
        available_sections: profile?.enable_nav_items ? Object.entries(profile.enable_nav_items).filter(([, enabled]) => enabled).map(([name]) => name) : [],
      },
      embedded_media: {
        instagram_posts_count: instagramPosts.length,
        instagram_posts: instagramPosts,
        gallery_images: extractGalleryImagesFromHtml(html),
        videos: instagramPosts.filter((post) => post.video_url).map((post) => post.video_url),
        api_url_samples: extractApiUrlSamples(html),
      },
      content_assessment: {
        detail_page_has_more_than_about_json: true,
        extraction_warnings: [],
        summary: buildContentSummary(profile, structuredData),
      },
    },
    scraped_at: new Date().toISOString(),
  };
}

async function discoverSchoolFolders(args) {
  const entries = [];
  const cityDirs = await fs.readdir(args.outputDir, { withFileTypes: true });

  for (const cityDir of cityDirs) {
    if (!cityDir.isDirectory() || cityDir.name.startsWith('.') || cityDir.name.startsWith('_')) {
      continue;
    }

    const city = cityDir.name.toLowerCase();
    if (args.cityFilter && !args.cityFilter.has(city)) {
      continue;
    }

    const cityPath = path.join(args.outputDir, cityDir.name);
    const schoolDirs = await fs.readdir(cityPath, { withFileTypes: true });

    for (const schoolDir of schoolDirs) {
      if (!schoolDir.isDirectory() || schoolDir.name.startsWith('.') || schoolDir.name.startsWith('_')) {
        continue;
      }

      const schoolId = schoolDir.name.toLowerCase();
      if (args.schoolFilter && !args.schoolFilter.has(schoolId)) {
        continue;
      }

      const folderPath = path.join(cityPath, schoolDir.name);
      const aboutPath = path.join(folderPath, 'about.json');

      try {
        await fs.access(aboutPath);
        entries.push({ city, schoolId, folderPath, aboutPath });
      } catch (_error) {
        // Ignore folders without about.json
      }
    }
  }

  entries.sort((a, b) => a.city.localeCompare(b.city) || a.schoolId.localeCompare(b.schoolId));
  return args.limit ? entries.slice(0, args.limit) : entries;
}

async function loadAboutRecord(aboutPath) {
  const raw = await fs.readFile(aboutPath, 'utf8');
  return JSON.parse(raw);
}

function buildSchoolDetailUrl(about) {
  if (about.source_url) {
    return about.source_url;
  }
  if (typeof about.slug === 'string' && about.slug.startsWith('/')) {
    return `${BASE_URL}${about.slug}`;
  }
  throw new Error(`Missing usable slug/source_url for ${about.id || about.name || about.slug || 'unknown school'}`);
}

async function writeDetailsFile(folderPath, payload) {
  const tempPath = path.join(folderPath, 'details.json.tmp');
  const finalPath = path.join(folderPath, 'details.json');
  await fs.writeFile(tempPath, `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
  await fs.rename(tempPath, finalPath);
}

async function scrapeSchoolDetail(page, about) {
  const sourceUrl = buildSchoolDetailUrl(about);
  const response = await page.goto(sourceUrl, { waitUntil: 'networkidle2', timeout: 60000 });
  const html = await page.content();
  const structuredData = extractStructuredData(html);
  const profile = extractEmbeddedSchoolProfile(html);
  const instagramPosts = extractInstagramPosts(html);

  const titleMatch = html.match(/<title>([\s\S]*?)<\/title>/i);
  const pageHead = {
    title: decodeJsonEscapedString(titleMatch ? titleMatch[1].trim() : null),
    canonical_url: getLinkHref(html, 'canonical'),
    meta_description: getMetaContent(html, 'name', 'description'),
    meta_keywords: getMetaContent(html, 'name', 'keywords'),
    meta_robots: getMetaContent(html, 'name', 'robots'),
    og_title: getMetaContent(html, 'property', 'og:title'),
    og_description: getMetaContent(html, 'property', 'og:description'),
    og_url: getMetaContent(html, 'property', 'og:url'),
    og_image: getMetaContent(html, 'property', 'og:image'),
  };

  return buildDetailsPayload({ about, sourceUrl, response, html, structuredData, pageHead, profile, instagramPosts });
}

async function scrapeSchoolWithRetries(page, entry, retries = 3) {
  const about = await loadAboutRecord(entry.aboutPath);

  for (let attempt = 1; attempt <= retries; attempt += 1) {
    try {
      const payload = await scrapeSchoolDetail(page, about);
      await writeDetailsFile(entry.folderPath, payload);
      return { status: 'success', payload };
    } catch (error) {
      if (attempt === retries) {
        return { status: 'failed', error: error.message };
      }
      await sleep(5000 * attempt);
    }
  }

  return { status: 'failed', error: 'Unknown scrape failure' };
}

async function runDetailBackfill(args) {
  const entries = await discoverSchoolFolders(args);
  console.log(`Starting detail backfill for ${entries.length} schools`);

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  let page = await browser.newPage();
  await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36');

  const totals = {
    processed: 0,
    success: 0,
    failed: 0,
  };

  try {
    for (const entry of entries) {
      totals.processed += 1;
      console.log(`[${totals.processed}/${entries.length}] ${entry.city}/${entry.schoolId}`);

      const result = await scrapeSchoolWithRetries(page, entry);
      if (result.status === 'success') {
        totals.success += 1;
        console.log(`  ✓ wrote ${path.join(entry.folderPath, 'details.json')}`);
      } else {
        totals.failed += 1;
        console.log(`  ✗ failed ${entry.city}/${entry.schoolId}: ${result.error}`);
        try {
          await page.close();
        } catch (_error) {
          // no-op
        }
        page = await browser.newPage();
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36');
      }

      await sleep(randomDelay());
    }
  } finally {
    await browser.close();
  }

  console.log('Detail backfill completed');
  console.log(`Processed: ${totals.processed}`);
  console.log(`Success: ${totals.success}`);
  console.log(`Failed: ${totals.failed}`);
  return totals;
}

async function scrapeCity(citySlug) {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');

  try {
    const url = `${BASE_URL}/schools/${citySlug}`;
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });

    const paginationData = await page.evaluate(() => {
      const paginationText = document.querySelector('.pagination .page-item.active')?.textContent;
      const totalItemsText = document.querySelector('.pt-3')?.textContent;
      return {
        paginationText,
        totalItemsText
      };
    });

    let totalPages = 1;
    if (paginationData.paginationText) {
      const match = paginationData.paginationText.match(/(\d+)$/);
      if (match) totalPages = parseInt(match[1], 10);
    }

    console.log(`Processing ${citySlug}: ${totalPages} pages total`);

    const allSchools = [];

    for (let pageNum = 1; pageNum <= totalPages; pageNum += 1) {
      console.log(`  Page ${pageNum}/${totalPages}`);

      if (pageNum > 1) {
        await page.goto(`${url}?page=${pageNum}`, { waitUntil: 'networkidle2', timeout: 60000 });
      }

      const pageSchools = await page.evaluate(() => {
        const schools = [];
        const cards = document.querySelectorAll('.hover-card');

        cards.forEach((card) => {
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

            const footerLinks = card.querySelectorAll('.card-footer a');
            footerLinks.forEach((link) => {
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

async function runListingScrape() {
  console.log('Starting school data extraction...');
  console.log(`Cities to process: ${CITIES.length}`);

  const results = {};

  for (const city of CITIES) {
    try {
      const cityData = await scrapeCity(city);
      results[city] = cityData;

      await fs.mkdir('scraped_data', { recursive: true });
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

  await fs.mkdir('scraped_data', { recursive: true });
  await fs.writeFile(
    path.join('scraped_data', 'all_cities.json'),
    JSON.stringify(results, null, 2)
  );

  console.log('Scraping completed!');
  console.log(`Total cities processed: ${Object.keys(results).length}`);
  console.log(`Total schools found: ${Object.values(results).reduce((sum, city) => sum + (city.schools?.length || 0), 0)}`);
}

async function main() {
  const args = parseArgs();
  if (args.details) {
    const totals = await runDetailBackfill(args);
    if (args.failOnErrors && totals.failed > 0) {
      process.exitCode = 1;
    }
    return;
  }
  await runListingScrape();
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
