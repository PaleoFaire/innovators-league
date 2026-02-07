/**
 * SAM.gov Government Contracts Fetcher
 * Fetches federal contract awards and opportunities
 *
 * Usage: node scripts/fetch-contracts.js
 *
 * API: SAM.gov (requires free API key)
 * Get key at: https://sam.gov/content/entity-information
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

// Keywords to search for relevant contracts
const KEYWORDS = [
  'autonomous systems',
  'artificial intelligence',
  'drone',
  'unmanned',
  'satellite',
  'space launch',
  'nuclear energy',
  'fusion',
  'robotics',
  'counter-UAS',
  'hypersonic',
  'quantum computing'
];

// Defense/Tech agencies to prioritize
const PRIORITY_AGENCIES = [
  'DEPT OF DEFENSE',
  'DEPT OF THE AIR FORCE',
  'DEPT OF THE ARMY',
  'DEPT OF THE NAVY',
  'NATIONAL AERONAUTICS AND SPACE ADMINISTRATION',
  'DEPT OF ENERGY',
  'DEPT OF HOMELAND SECURITY'
];

// Known frontier tech contractors
const KNOWN_CONTRACTORS = [
  'ANDURIL', 'PALANTIR', 'SPACEX', 'SHIELD AI', 'SKYDIO',
  'ROCKET LAB', 'RELATIVITY', 'SCALE AI', 'HADRIAN', 'SARONIC'
];

function httpsGet(url, apiKey) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, {
      headers: {
        'User-Agent': 'InnovatorsLeague/1.0',
        'X-Api-Key': apiKey || process.env.SAM_API_KEY || ''
      }
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

function getDateRange() {
  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - 30); // Last 30 days

  return {
    start: start.toISOString().split('T')[0],
    end: end.toISOString().split('T')[0]
  };
}

async function fetchOpportunities(keyword) {
  const { start, end } = getDateRange();
  const apiKey = process.env.SAM_API_KEY;

  if (!apiKey) {
    console.log('Warning: SAM_API_KEY not set. Using mock data.');
    return [];
  }

  const url = `https://api.sam.gov/opportunities/v2/search?api_key=${apiKey}&keywords=${encodeURIComponent(keyword)}&postedFrom=${start}&postedTo=${end}&limit=100`;

  try {
    const data = await httpsGet(url, apiKey);
    return data.opportunitiesData || [];
  } catch (error) {
    console.error(`Error fetching opportunities for "${keyword}": ${error.message}`);
    return [];
  }
}

async function fetchAllContracts() {
  console.log('Fetching government contracts...\n');

  const allContracts = [];
  const seenIds = new Set();

  for (const keyword of KEYWORDS) {
    console.log(`Searching: "${keyword}"`);
    const opportunities = await fetchOpportunities(keyword);

    for (const opp of opportunities) {
      if (seenIds.has(opp.noticeId)) continue;
      seenIds.add(opp.noticeId);

      // Check if it's a priority agency or known contractor
      const isPriority = PRIORITY_AGENCIES.some(a =>
        opp.department?.toUpperCase().includes(a) ||
        opp.subtierAgency?.toUpperCase().includes(a)
      );

      const isKnownContractor = KNOWN_CONTRACTORS.some(c =>
        opp.award?.awardee?.name?.toUpperCase().includes(c)
      );

      allContracts.push({
        id: opp.noticeId,
        title: opp.title,
        agency: opp.department || opp.subtierAgency || 'Unknown',
        type: opp.type,
        postedDate: opp.postedDate,
        responseDeadline: opp.responseDeadline,
        value: opp.award?.amount,
        awardee: opp.award?.awardee?.name,
        awardDate: opp.award?.date,
        naicsCode: opp.naicsCode,
        setAside: opp.typeOfSetAsideDescription,
        url: opp.uiLink,
        isPriority,
        isKnownContractor,
        keywords: [keyword]
      });
    }

    // Rate limit
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  // Sort by date and priority
  allContracts.sort((a, b) => {
    if (a.isKnownContractor !== b.isKnownContractor) {
      return b.isKnownContractor ? 1 : -1;
    }
    if (a.isPriority !== b.isPriority) {
      return b.isPriority ? 1 : -1;
    }
    return new Date(b.postedDate) - new Date(a.postedDate);
  });

  console.log(`\nTotal contracts found: ${allContracts.length}`);

  return allContracts;
}

async function main() {
  const contracts = await fetchAllContracts();

  // Write to temp file
  const outputPath = path.join(__dirname, '../temp/gov-contracts.json');
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, JSON.stringify(contracts, null, 2));

  console.log(`\nWritten to: ${outputPath}`);
  console.log('\nSample output:');
  console.log(JSON.stringify(contracts.slice(0, 3), null, 2));
}

main().catch(console.error);
