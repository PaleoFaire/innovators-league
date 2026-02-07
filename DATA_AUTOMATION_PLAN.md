# Innovators League - Automated Data Refresh Plan

## Overview

This document outlines the strategy for automatically refreshing data across all intelligence features. The goal is to keep the platform current without manual intervention, justifying premium subscription pricing.

---

## Data Sources & Refresh Frequencies

### 1. **SEC EDGAR Filings** (Already Implemented)
- **Data**: 8-K, 10-K, 10-Q, DEF 14A, Form D filings
- **API**: SEC EDGAR REST API (free, no auth required)
- **Refresh**: Every 15 minutes during market hours
- **Implementation**: `SEC_FILINGS_LIVE` array in data.js
- **Endpoint**: `https://efts.sec.gov/LATEST/search-index`

```javascript
// Example API call
fetch('https://efts.sec.gov/LATEST/search-index?q=*&dateRange=custom&startdt=2024-01-01&forms=8-K,10-K')
```

### 2. **Government Contracts (SAM.gov)**
- **Data**: Federal contract awards, modifications, opportunities
- **API**: SAM.gov Entity/Opportunities API
- **Auth**: Requires API key (free registration)
- **Refresh**: Daily at 6 AM EST
- **Cost**: Free

```javascript
// SAM.gov API endpoint
const SAM_API = 'https://api.sam.gov/opportunities/v2/search';
// Requires API key from sam.gov
```

### 3. **Stock Prices (Public Companies)**
- **Data**: PLTR, RKLB, JOBY, ACHR, PL, LUNR, NVDA
- **API Options**:
  - Yahoo Finance API (unofficial, free)
  - Alpha Vantage (free tier: 5 calls/min)
  - Polygon.io (free tier: 5 calls/min)
  - IEX Cloud (free tier: 50k messages/month)
- **Refresh**: Every 5 minutes during market hours
- **Cost**: Free to $50/month depending on volume

```javascript
// Alpha Vantage example
const ALPHA_API = 'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=PLTR&apikey=YOUR_KEY';
```

### 4. **News & Press Releases**
- **Data**: Company announcements, funding news, product launches
- **API Options**:
  - NewsAPI.org (free tier: 100 requests/day)
  - GNews API (free tier: 100 requests/day)
  - Bing News Search API (free tier: 1000 calls/month)
- **Refresh**: Every 30 minutes
- **Cost**: Free to $50/month

### 5. **Funding Rounds (Crunchbase/PitchBook Alternative)**
- **Data**: New funding rounds, valuations, investors
- **API Options**:
  - Crunchbase Basic API ($99/month for 200 calls/day)
  - Dealroom API (enterprise pricing)
  - Manual scraping of press releases
- **Refresh**: Daily
- **Cost**: $99-500/month or free with scraping

### 6. **Patent Data (USPTO)**
- **Data**: Patent filings, grants, assignments
- **API**: USPTO Open Data Portal (free)
- **Refresh**: Weekly (patents publish Tuesdays)
- **Cost**: Free

```javascript
// USPTO PatentsView API
const USPTO_API = 'https://api.patentsview.org/patents/query';
```

### 7. **Job Postings / Hiring Signals**
- **Data**: Open positions, hiring velocity
- **API Options**:
  - LinkedIn API (requires partnership)
  - Indeed API (deprecated)
  - Greenhouse/Lever APIs (per-company)
  - Scraping job boards (legal gray area)
  - Theirstack.com API (aggregator)
- **Refresh**: Daily
- **Cost**: $200-1000/month for quality data

### 8. **Secondary Market Data**
- **Data**: Private share prices, transaction volume
- **Sources**:
  - Forge Global (partnership required)
  - EquityZen (partnership required)
  - Carta (API not public)
  - Manual data entry from reports
- **Refresh**: Weekly
- **Cost**: Partnership/enterprise agreements

---

## Implementation Architecture

### Option A: GitHub Actions (Recommended for MVP)

**Pros**: Free, simple, integrates with repo
**Cons**: Limited to 6 hours runtime, public repos have limits

```yaml
# .github/workflows/data-refresh.yml
name: Refresh Data

on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:  # Manual trigger

jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Fetch SEC Filings
        run: node scripts/fetch-sec.js
        env:
          SEC_API_KEY: ${{ secrets.SEC_API_KEY }}

      - name: Fetch Stock Prices
        run: node scripts/fetch-stocks.js
        env:
          ALPHA_API_KEY: ${{ secrets.ALPHA_API_KEY }}

      - name: Fetch News
        run: node scripts/fetch-news.js
        env:
          NEWS_API_KEY: ${{ secrets.NEWS_API_KEY }}

      - name: Fetch Gov Contracts
        run: node scripts/fetch-contracts.js
        env:
          SAM_API_KEY: ${{ secrets.SAM_API_KEY }}

      - name: Update data.js
        run: node scripts/compile-data.js

      - name: Commit and Push
        run: |
          git config user.name "Data Bot"
          git config user.email "bot@innovatorsleague.com"
          git add data.js
          git commit -m "chore: Auto-refresh data $(date +%Y-%m-%d)" || exit 0
          git push
```

### Option B: Serverless Functions (Vercel/Netlify)

**Pros**: More flexible, can handle webhooks
**Cons**: Requires hosting changes, monthly costs

```javascript
// api/refresh-data.js (Vercel serverless function)
export default async function handler(req, res) {
  // Verify cron secret
  if (req.headers.authorization !== `Bearer ${process.env.CRON_SECRET}`) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  // Fetch all data sources
  const [sec, stocks, news, contracts] = await Promise.all([
    fetchSECFilings(),
    fetchStockPrices(),
    fetchNews(),
    fetchGovContracts()
  ]);

  // Update data store (could be GitHub, database, or KV store)
  await updateDataStore({ sec, stocks, news, contracts });

  return res.json({ success: true, updated: new Date().toISOString() });
}
```

### Option C: External Cron Service + GitHub API

**Pros**: Most reliable, real-time capable
**Cons**: Additional service dependency

Services: Cron-job.org (free), EasyCron ($12/mo), Pipedream (free tier)

---

## Data Fetch Scripts

### `/scripts/fetch-sec.js`
```javascript
const fetch = require('node-fetch');
const fs = require('fs');

const COMPANIES = ['SpaceX', 'Palantir', 'Anduril', 'OpenAI', /* ... */];

async function fetchSECFilings() {
  const filings = [];

  for (const company of COMPANIES) {
    const response = await fetch(
      `https://efts.sec.gov/LATEST/search-index?q=${encodeURIComponent(company)}&dateRange=custom&startdt=${getLastWeek()}`
    );
    const data = await response.json();

    filings.push(...data.hits.hits.map(hit => ({
      company,
      form: hit._source.form,
      date: hit._source.file_date,
      description: hit._source.display_names?.[0],
      url: `https://www.sec.gov/Archives/edgar/data/${hit._source.ciks[0]}/${hit._source.adsh.replace(/-/g, '')}/${hit._source.file_num}`
    })));
  }

  return filings;
}

module.exports = { fetchSECFilings };
```

### `/scripts/fetch-stocks.js`
```javascript
const TICKERS = ['PLTR', 'RKLB', 'JOBY', 'ACHR', 'PL', 'LUNR', 'NVDA'];

async function fetchStockPrices() {
  const prices = [];

  for (const ticker of TICKERS) {
    const response = await fetch(
      `https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=${ticker}&apikey=${process.env.ALPHA_API_KEY}`
    );
    const data = await response.json();
    const quote = data['Global Quote'];

    prices.push({
      ticker,
      price: parseFloat(quote['05. price']),
      change: quote['10. change percent'],
      volume: parseInt(quote['06. volume']),
      updated: new Date().toISOString()
    });

    // Rate limit: 5 calls per minute
    await sleep(12000);
  }

  return prices;
}
```

### `/scripts/fetch-contracts.js`
```javascript
async function fetchGovContracts() {
  const keywords = ['autonomous', 'AI', 'drone', 'satellite', 'defense', 'nuclear'];
  const contracts = [];

  for (const keyword of keywords) {
    const response = await fetch(
      `https://api.sam.gov/opportunities/v2/search?api_key=${process.env.SAM_API_KEY}&keywords=${keyword}&postedFrom=${getLastMonth()}&limit=100`
    );
    const data = await response.json();

    contracts.push(...data.opportunitiesData.map(opp => ({
      title: opp.title,
      agency: opp.department,
      value: opp.award?.amount,
      awardee: opp.award?.awardee?.name,
      date: opp.postedDate,
      type: opp.type,
      naicsCode: opp.naicsCode
    })));
  }

  return contracts;
}
```

---

## Cost Estimates

| Service | Free Tier | Paid Tier | Notes |
|---------|-----------|-----------|-------|
| SEC EDGAR | Unlimited | N/A | Always free |
| Alpha Vantage | 5/min, 500/day | $50/mo unlimited | Good for stocks |
| NewsAPI | 100/day | $450/mo | Or use GNews |
| SAM.gov | Unlimited | N/A | Requires registration |
| USPTO | Unlimited | N/A | Always free |
| GitHub Actions | 2000 min/mo | $4/1000 min | More than enough |
| **Total (MVP)** | **$0** | - | Free tier sufficient |
| **Total (Pro)** | - | **~$100-200/mo** | More API calls |

---

## Recommended Implementation Phases

### Phase 1: Free APIs (Week 1)
- [ ] Set up GitHub Actions workflow
- [ ] Implement SEC EDGAR fetcher
- [ ] Implement USPTO patent fetcher
- [ ] Implement SAM.gov contract fetcher
- [ ] Auto-commit daily updates

### Phase 2: Stock & News (Week 2)
- [ ] Add Alpha Vantage integration for stock prices
- [ ] Add NewsAPI or GNews for news feed
- [ ] Update MARKET_PULSE with live data
- [ ] Update NEWS_FEED with live data

### Phase 3: Advanced Data (Week 3-4)
- [ ] Research job posting APIs
- [ ] Set up secondary market data partnerships
- [ ] Add Crunchbase for funding data (if budget allows)
- [ ] Implement data validation and error handling

### Phase 4: Real-Time (Month 2)
- [ ] Move to serverless for faster updates
- [ ] Implement webhook receivers for real-time alerts
- [ ] Add email/Slack notification delivery
- [ ] Build admin dashboard for data monitoring

---

## Data Validation Rules

```javascript
// Validate incoming data before updating
function validateCompanyData(data) {
  const errors = [];

  if (!data.name || data.name.length < 2) {
    errors.push('Invalid company name');
  }

  if (data.valuation && !data.valuation.match(/^\$[\d.]+[BMK]?\+?$/)) {
    errors.push('Invalid valuation format');
  }

  if (data.fundingStage && !VALID_STAGES.includes(data.fundingStage)) {
    errors.push('Invalid funding stage');
  }

  return errors.length === 0 ? { valid: true } : { valid: false, errors };
}
```

---

## Monitoring & Alerts

Set up monitoring to detect data issues:

1. **Data Freshness**: Alert if data is >24 hours old
2. **API Failures**: Alert on 3+ consecutive failures
3. **Data Anomalies**: Alert on >50% change in key metrics
4. **Quota Usage**: Alert at 80% of API quota

```yaml
# Example: Alert on stale data
- name: Check Data Freshness
  run: |
    LAST_UPDATE=$(jq -r '.lastUpdated' data.js)
    HOURS_OLD=$(( ($(date +%s) - $(date -d "$LAST_UPDATE" +%s)) / 3600 ))
    if [ $HOURS_OLD -gt 24 ]; then
      echo "::error::Data is $HOURS_OLD hours old"
      exit 1
    fi
```

---

## Security Considerations

1. **API Keys**: Store in GitHub Secrets, never in code
2. **Rate Limiting**: Respect all API rate limits
3. **Data Validation**: Sanitize all external data
4. **Access Control**: Use fine-grained tokens
5. **Audit Logging**: Log all data updates

---

## Next Steps

1. Create `/scripts` directory with fetch modules
2. Set up GitHub Actions workflow
3. Register for free API keys (Alpha Vantage, NewsAPI, SAM.gov)
4. Test locally before enabling automation
5. Monitor first week of automated updates

---

*Last Updated: 2026-02-07*
*Author: Claude (Data Automation Planning)*
