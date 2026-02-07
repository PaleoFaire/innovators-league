/**
 * SEC EDGAR Filings Fetcher
 * Fetches recent SEC filings for tracked companies
 *
 * Usage: node scripts/fetch-sec.js
 *
 * API: SEC EDGAR (free, no auth required)
 * Rate Limit: 10 requests/second
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

// Companies to track (CIK numbers for public companies)
const TRACKED_COMPANIES = {
  'Palantir Technologies': { cik: '1321655', ticker: 'PLTR' },
  'Rocket Lab': { cik: '1819994', ticker: 'RKLB' },
  'Joby Aviation': { cik: '1819479', ticker: 'JOBY' },
  'Archer Aviation': { cik: '1819928', ticker: 'ACHR' },
  'Planet Labs': { cik: '1836935', ticker: 'PL' },
  'Intuitive Machines': { cik: '1881438', ticker: 'LUNR' },
  'NVIDIA': { cik: '1045810', ticker: 'NVDA' }
};

// Form types to track
const FORM_TYPES = ['8-K', '10-K', '10-Q', 'S-1', 'DEF 14A', 'SC 13D', 'SC 13G'];

function httpsGet(url) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, {
      headers: { 'User-Agent': 'InnovatorsLeague/1.0 (contact@innovatorsleague.com)' }
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          resolve(data);
        }
      });
    });
    req.on('error', reject);
  });
}

async function fetchCompanyFilings(company, cik) {
  const url = `https://data.sec.gov/submissions/CIK${cik.padStart(10, '0')}.json`;

  try {
    const data = await httpsGet(url);

    if (!data.filings || !data.filings.recent) {
      console.log(`  No filings found for ${company}`);
      return [];
    }

    const recent = data.filings.recent;
    const filings = [];

    for (let i = 0; i < Math.min(recent.form.length, 50); i++) {
      const form = recent.form[i];

      if (FORM_TYPES.includes(form)) {
        const filingDate = recent.filingDate[i];
        const accessionNumber = recent.accessionNumber[i];
        const primaryDoc = recent.primaryDocument[i];

        // Only include filings from last 90 days
        const daysDiff = (Date.now() - new Date(filingDate)) / (1000 * 60 * 60 * 24);
        if (daysDiff > 90) continue;

        filings.push({
          company,
          form,
          date: filingDate,
          description: recent.primaryDocDescription?.[i] || form,
          url: `https://www.sec.gov/Archives/edgar/data/${cik}/${accessionNumber.replace(/-/g, '')}/${primaryDoc}`,
          accessionNumber
        });
      }
    }

    return filings;
  } catch (error) {
    console.error(`  Error fetching ${company}: ${error.message}`);
    return [];
  }
}

async function fetchAllFilings() {
  console.log('Fetching SEC filings...\n');

  const allFilings = [];

  for (const [company, info] of Object.entries(TRACKED_COMPANIES)) {
    console.log(`Fetching: ${company} (${info.ticker})`);
    const filings = await fetchCompanyFilings(company, info.cik);
    allFilings.push(...filings);

    // Rate limit: wait 100ms between requests
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  // Sort by date descending
  allFilings.sort((a, b) => new Date(b.date) - new Date(a.date));

  console.log(`\nTotal filings found: ${allFilings.length}`);

  return allFilings;
}

async function main() {
  const filings = await fetchAllFilings();

  // Format for data.js
  const output = `// Auto-generated SEC filings - ${new Date().toISOString()}
const SEC_FILINGS_LIVE = ${JSON.stringify(filings.slice(0, 20), null, 2)};
`;

  // Write to temp file (will be merged by compile script)
  const outputPath = path.join(__dirname, '../temp/sec-filings.json');
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, JSON.stringify(filings, null, 2));

  console.log(`\nWritten to: ${outputPath}`);
  console.log('\nSample output:');
  console.log(JSON.stringify(filings.slice(0, 3), null, 2));
}

main().catch(console.error);
