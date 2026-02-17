#!/usr/bin/env node
/**
 * RSS News Aggregator for The Innovators League
 * Fetches news from multiple RSS feeds and filters for tracked companies.
 * Now using MASTER_COMPANY_LIST for 450+ company coverage.
 */

const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');

// Import the master company list (450+ companies with aliases)
const { MASTER_COMPANY_LIST, mentionsCompany, getAllSearchTerms, getStats } = require('./company_master_list.js');

// RSS feeds to monitor (18 total feeds for comprehensive coverage)
const RSS_FEEDS = [
  // Tech General
  { name: 'TechCrunch', url: 'https://techcrunch.com/feed/', category: 'tech' },
  { name: 'VentureBeat AI', url: 'https://venturebeat.com/category/ai/feed/', category: 'ai' },
  { name: 'Ars Technica', url: 'https://feeds.arstechnica.com/arstechnica/technology-lab', category: 'tech' },
  { name: 'Wired', url: 'https://www.wired.com/feed/rss', category: 'tech' },
  { name: 'MIT Tech Review', url: 'https://www.technologyreview.com/feed/', category: 'tech' },
  { name: 'IEEE Spectrum', url: 'https://spectrum.ieee.org/feeds/feed.rss', category: 'tech' },
  { name: 'The Verge Tech', url: 'https://www.theverge.com/rss/tech/index.xml', category: 'tech' },

  // Defense & Security
  { name: 'Defense News', url: 'https://www.defensenews.com/arc/outboundfeeds/rss/', category: 'defense' },
  { name: 'Breaking Defense', url: 'https://breakingdefense.com/feed/', category: 'defense' },
  { name: 'Defense One', url: 'https://www.defenseone.com/rss/all/', category: 'defense' },
  { name: 'War on the Rocks', url: 'https://warontherocks.com/feed/', category: 'defense' },

  // Space
  { name: 'SpaceNews', url: 'https://spacenews.com/feed/', category: 'space' },
  { name: 'Ars Technica Space', url: 'https://feeds.arstechnica.com/arstechnica/science', category: 'space' },

  // Energy & Climate
  { name: 'Canary Media', url: 'https://www.canarymedia.com/feed', category: 'energy' },
  { name: 'CleanTechnica', url: 'https://cleantechnica.com/feed/', category: 'energy' },
  { name: 'Nuclear Newswire', url: 'https://www.ans.org/news/rss/', category: 'nuclear' },

  // Startups & VC
  { name: 'Crunchbase News', url: 'https://news.crunchbase.com/feed/', category: 'funding' },

  // Future Tech
  { name: 'Next Big Future', url: 'https://www.nextbigfuture.com/feed', category: 'tech' },
];

// Companies are now tracked via MASTER_COMPANY_LIST (450+ companies with aliases)
// This gives us ~6x better coverage than the previous 72 hardcoded companies

// Simple XML parser for RSS
function parseRSS(xml) {
  const items = [];
  const itemRegex = /<item>([\s\S]*?)<\/item>/g;
  let match;

  while ((match = itemRegex.exec(xml)) !== null) {
    const itemXml = match[1];

    const getTag = (tag) => {
      const regex = new RegExp(`<${tag}[^>]*><!\\[CDATA\\[([\\s\\S]*?)\\]\\]><\\/${tag}>|<${tag}[^>]*>([\\s\\S]*?)<\\/${tag}>`);
      const m = itemXml.match(regex);
      return m ? (m[1] || m[2] || '').trim() : '';
    };

    items.push({
      title: getTag('title'),
      link: getTag('link'),
      description: getTag('description').replace(/<[^>]*>/g, '').substring(0, 300),
      pubDate: getTag('pubDate'),
      category: getTag('category')
    });
  }

  return items;
}

// Fetch a single RSS feed
function fetchFeed(feed) {
  return new Promise((resolve, reject) => {
    const url = new URL(feed.url);
    const client = url.protocol === 'https:' ? https : http;

    const options = {
      hostname: url.hostname,
      path: url.pathname + url.search,
      headers: {
        'User-Agent': 'InnovatorsLeague-Bot/1.0 (https://innovatorsleague.com)',
        'Accept': 'application/rss+xml, application/xml, text/xml'
      },
      timeout: 10000
    };

    const req = client.get(options, (res) => {
      // Handle redirects
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        const newFeed = { ...feed, url: res.headers.location };
        fetchFeed(newFeed).then(resolve).catch(reject);
        return;
      }

      if (res.statusCode !== 200) {
        reject(new Error(`HTTP ${res.statusCode}`));
        return;
      }

      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const items = parseRSS(data);
          resolve(items.map(item => ({
            ...item,
            source: feed.name,
            feedCategory: feed.category
          })));
        } catch (e) {
          reject(e);
        }
      });
    });

    req.on('error', reject);
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Timeout'));
    });
  });
}

// Check if article mentions a tracked company (now uses MASTER_COMPANY_LIST with aliases)
function mentionsTrackedCompany(article) {
  const text = `${article.title} ${article.description}`;
  const matches = mentionsCompany(text);

  if (matches.length > 0) {
    // Return the first matched company name
    return matches[0].name;
  }
  return null;
}

// Get all matched companies for an article (for multi-company articles)
function getAllMatchedCompanies(article) {
  const text = `${article.title} ${article.description}`;
  return mentionsCompany(text);
}

// Categorize article type
function categorizeArticle(article) {
  const text = `${article.title} ${article.description}`.toLowerCase();

  if (text.includes('raise') || text.includes('funding') || text.includes('series') || text.includes('valuation')) {
    return 'funding';
  }
  if (text.includes('contract') || text.includes('award') || text.includes('pentagon') || text.includes('dod')) {
    return 'contract';
  }
  if (text.includes('patent') || text.includes('invention')) {
    return 'patent';
  }
  if (text.includes('hire') || text.includes('appoint') || text.includes('ceo') || text.includes('cto')) {
    return 'hire';
  }
  if (text.includes('ipo') || text.includes('public') || text.includes('spac')) {
    return 'ipo';
  }
  if (text.includes('launch') || text.includes('test') || text.includes('milestone')) {
    return 'milestone';
  }
  return 'news';
}

// Estimate impact level
function estimateImpact(article) {
  const text = `${article.title} ${article.description}`.toLowerCase();

  // High impact keywords
  if (text.match(/billion|ipo|acquisition|acquired|major contract|\$\d+b/i)) {
    return 'high';
  }

  // Medium impact keywords
  if (text.match(/million|series [c-z]|partnership|expansion|\$\d+m/i)) {
    return 'medium';
  }

  return 'low';
}

// Format relative time
function formatRelativeTime(dateStr) {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now - date;
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffHours / 24);

  if (diffHours < 1) return 'Just now';
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

async function main() {
  const stats = getStats();
  console.log('='.repeat(60));
  console.log('RSS News Aggregator for The Innovators League');
  console.log('='.repeat(60));
  console.log(`Monitoring ${RSS_FEEDS.length} feeds for ${stats.totalCompanies} companies`);
  console.log(`Search terms: ${stats.totalSearchTerms} (including aliases)`);
  console.log(`Sectors covered: ${stats.sectors.join(', ')}`);
  console.log(`Date: ${new Date().toISOString()}`);
  console.log('='.repeat(60));

  const allArticles = [];
  const errors = [];

  // Fetch all feeds
  for (const feed of RSS_FEEDS) {
    try {
      console.log(`Fetching: ${feed.name}...`);
      const articles = await fetchFeed(feed);
      console.log(`  Found ${articles.length} articles`);
      allArticles.push(...articles);
    } catch (e) {
      console.log(`  Error: ${e.message}`);
      errors.push({ feed: feed.name, error: e.message });
    }
  }

  console.log(`\nTotal articles fetched: ${allArticles.length}`);

  // Filter for tracked companies (now checking 450+ companies with aliases)
  const relevantArticles = [];
  for (const article of allArticles) {
    const matches = getAllMatchedCompanies(article);
    if (matches.length > 0) {
      relevantArticles.push({
        ...article,
        matchedCompany: matches[0].name,
        matchedCompanies: matches.map(m => m.name),
        sectors: [...new Set(matches.map(m => m.sector))],
        type: categorizeArticle(article),
        impact: estimateImpact(article),
        time: formatRelativeTime(article.pubDate)
      });
    }
  }

  console.log(`Relevant articles (mentioning tracked companies): ${relevantArticles.length}`);

  // Sort by date (most recent first)
  relevantArticles.sort((a, b) => new Date(b.pubDate) - new Date(a.pubDate));

  // Save raw data
  const dataDir = path.join(__dirname, '..', 'data');
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }

  fs.writeFileSync(
    path.join(dataDir, 'news_raw.json'),
    JSON.stringify(relevantArticles, null, 2)
  );

  // Generate signals format for COMPANY_SIGNALS
  const signals = relevantArticles.slice(0, 20).map((article, index) => ({
    id: Date.now() + index,
    type: article.type,
    company: article.matchedCompany,
    headline: article.title.substring(0, 120),
    source: article.source,
    time: article.time,
    impact: article.impact,
    unread: index < 5,
    link: article.link
  }));

  // Generate JS snippet
  const jsOutput = `// Auto-generated news signals
// Last updated: ${new Date().toISOString()}
const COMPANY_SIGNALS_AUTO = ${JSON.stringify(signals, null, 2)};
`;

  fs.writeFileSync(
    path.join(dataDir, 'news_signals_auto.js'),
    jsOutput
  );

  console.log(`\nSaved ${signals.length} signals to data/news_signals_auto.js`);
  console.log('='.repeat(60));
  console.log('Done!');
  console.log('='.repeat(60));

  // Output summary
  if (relevantArticles.length > 0) {
    console.log('\nTop 5 Recent Stories:');
    relevantArticles.slice(0, 5).forEach((a, i) => {
      console.log(`${i + 1}. [${a.matchedCompany}] ${a.title.substring(0, 60)}...`);
    });
  }
}

main().catch(console.error);
