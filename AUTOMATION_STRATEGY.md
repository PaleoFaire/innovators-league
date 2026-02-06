# The Innovators League: Grand Data Automation Strategy

## Vision
Transform The Innovators League from a manually-updated database into a **living intelligence platform** that automatically ingests, processes, and surfaces real-time data across all tracked companies.

---

## Data Categories & Automation Sources

### 1. 💰 FUNDING ROUNDS & VALUATIONS

| Data Type | Source | API/Method | Update Frequency | Cost |
|-----------|--------|------------|------------------|------|
| Funding rounds | [Crunchbase API](https://data.crunchbase.com/) | REST API | Daily | $49-99/mo Pro |
| VC investments | [OpenVC](https://www.openvc.app/) | Community + scrape | Weekly | Free |
| Valuations | SEC EDGAR (S-1, 8-K) | [sec-api.io](https://sec-api.io/) | Real-time | $50/mo starter |
| Secondary market | PitchBook | Manual or partnership | Weekly | $$$ |

**Automation Approach:**
```yaml
# GitHub Action: .github/workflows/funding-sync.yml
name: Sync Funding Rounds
on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM UTC
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Fetch Crunchbase data
        run: python scripts/fetch_funding.py
      - name: Update data.js
        run: python scripts/merge_funding.py
      - name: Commit changes
        run: |
          git config user.name "TIL Bot"
          git add data.js
          git commit -m "Auto-update: Funding rounds $(date +%Y-%m-%d)" || exit 0
          git push
```

---

### 2. 📋 GOVERNMENT CONTRACTS

| Data Type | Source | API/Method | Update Frequency | Cost |
|-----------|--------|------------|------------------|------|
| Federal contracts | [USAspending.gov API](https://api.usaspending.gov/) | REST API | Daily | **FREE** |
| DoD contracts | SAM.gov | Bulk download | Weekly | **FREE** |
| SBIR/STTR awards | SBIR.gov | Scrape/API | Monthly | **FREE** |

**Automation Approach:**
```python
# scripts/fetch_gov_contracts.py
import requests

# Query USAspending for our tracked companies
TRACKED_COMPANIES = ['Anduril', 'Palantir', 'SpaceX', 'Shield AI', ...]

for company in TRACKED_COMPANIES:
    response = requests.post(
        'https://api.usaspending.gov/api/v2/search/spending_by_award/',
        json={
            'filters': {
                'recipient_search_text': [company],
                'time_period': [{'start_date': '2024-01-01'}]
            }
        }
    )
    # Process and merge into GOV_CONTRACTS
```

---

### 3. 📜 PATENT FILINGS

| Data Type | Source | API/Method | Update Frequency | Cost |
|-----------|--------|------------|------------------|------|
| Patent grants | [PatentsView API](https://patentsview.org/apis/purpose) | REST API | Weekly | **FREE** |
| Patent applications | USPTO PEDS | REST API | Weekly | **FREE** |
| Patent tracking | [USPTO Open Data Portal](https://data.uspto.gov/) | REST API | Weekly | **FREE** |

**Automation Approach:**
```yaml
# GitHub Action: .github/workflows/patent-sync.yml
name: Sync Patent Data
on:
  schedule:
    - cron: '0 8 * * 0'  # Weekly on Sunday
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Fetch patents for tracked companies
        run: python scripts/fetch_patents.py
```

---

### 4. 📰 NEWS & SIGNALS

| Data Type | Source | API/Method | Update Frequency | Cost |
|-----------|--------|------------|------------------|------|
| Tech news | TechCrunch, The Information | RSS Feeds | Hourly | Free |
| Defense news | Defense News, Breaking Defense | RSS Feeds | Hourly | Free |
| Company news | Google News API | REST API | Hourly | Limited free |
| Press releases | PR Newswire, Business Wire | RSS Feeds | Hourly | Free |

**RSS Feeds to Monitor:**
```javascript
const NEWS_FEEDS = [
  // Tech
  'https://techcrunch.com/feed/',
  'https://feeds.arstechnica.com/arstechnica/technology-lab',

  // Defense
  'https://www.defensenews.com/arc/outboundfeeds/rss/',
  'https://breakingdefense.com/feed/',

  // Space
  'https://spacenews.com/feed/',
  'https://arstechnica.com/science/feed/',

  // Energy
  'https://www.greentechmedia.com/feed/',

  // AI
  'https://venturebeat.com/category/ai/feed/',
  'https://www.wired.com/feed/category/artificial-intelligence/latest/rss'
];
```

**Automation with GitHub Actions:**
```yaml
name: News Aggregation
on:
  schedule:
    - cron: '0 */4 * * *'  # Every 4 hours
jobs:
  aggregate:
    runs-on: ubuntu-latest
    steps:
      - name: Fetch RSS feeds
        run: node scripts/aggregate_news.js
      - name: Filter for tracked companies
        run: node scripts/filter_company_mentions.js
      - name: Update NEWS_FEED in data.js
        run: node scripts/update_news.js
```

---

### 5. 📊 SEC FILINGS (IPO, 8-K, 10-K)

| Data Type | Source | API/Method | Update Frequency | Cost |
|-----------|--------|------------|------------------|------|
| 8-K filings | [SEC EDGAR](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) | REST API | Real-time | **FREE** |
| S-1 (IPO) filings | [sec-api.io](https://sec-api.io/) | REST API | Real-time | $50/mo |
| 10-K/10-Q reports | SEC EDGAR | REST API | Quarterly | **FREE** |

**Real-time SEC Filing Monitor:**
```python
# scripts/sec_monitor.py
from sec_api import QueryApi

queryApi = QueryApi(api_key="YOUR_KEY")

# Monitor for filings from our tracked public companies
TRACKED_TICKERS = ['PLTR', 'RKLB', 'ASTS', 'LUNR', 'SMR', ...]

query = {
    "query": {
        "query_string": {
            "query": f"ticker:({' OR '.join(TRACKED_TICKERS)})"
        }
    },
    "from": "0",
    "size": "50",
    "sort": [{"filedAt": {"order": "desc"}}]
}

filings = queryApi.get_filings(query)
```

---

### 6. 👔 HIRING & TEAM SIGNALS

| Data Type | Source | API/Method | Update Frequency | Cost |
|-----------|--------|------------|------------------|------|
| Job postings | LinkedIn Jobs | Scrape (careful!) | Weekly | Risky |
| Hiring signals | [Otta API](https://otta.com/) | Partnership | Weekly | $$ |
| Team changes | Crunchbase | API | Weekly | Included |
| Executive moves | SEC Form 4, 8-K | EDGAR API | Real-time | **FREE** |

**Alternative: Track job board URLs directly:**
```javascript
const JOB_BOARDS = {
  'Anduril Industries': 'https://www.anduril.com/careers',
  'SpaceX': 'https://www.spacex.com/careers',
  'Anthropic': 'https://www.anthropic.com/careers',
  // ...
};
// Scrape job count changes weekly
```

---

### 7. 🎤 EXPERT INSIGHTS

| Data Type | Source | API/Method | Update Frequency | Cost |
|-----------|--------|------------|------------------|------|
| Expert transcripts | Tegus, AlphaSense | Partnership | As available | $$$ |
| Podcast mentions | Listen Notes API | REST API | Weekly | Free tier |
| Conference talks | YouTube API | REST API | Weekly | Free |
| Twitter/X threads | X API | REST API | Daily | $100/mo |

**Community-Sourced Expert Takes:**
```javascript
// Allow community submissions via GitHub Issues
// Moderate and merge into EXPERT_TAKES array

// GitHub Action to process approved expert takes
name: Process Expert Submissions
on:
  issues:
    types: [labeled]
jobs:
  process:
    if: contains(github.event.issue.labels.*.name, 'expert-take-approved')
    steps:
      - name: Extract and add to data.js
        run: node scripts/add_expert_take.js "${{ github.event.issue.body }}"
```

---

## Recommended Implementation Phases

### Phase 1: FREE Data Sources (Week 1-2)
1. ✅ SEC EDGAR filings (already partially done!)
2. USAspending.gov government contracts
3. USPTO PatentsView API
4. RSS news aggregation
5. GitHub Actions automation

### Phase 2: Low-Cost APIs (Week 3-4)
1. Crunchbase Pro API ($49/mo)
2. sec-api.io for real-time filings ($50/mo)
3. Enhanced news filtering with AI

### Phase 3: AI Enhancement (Week 5-6)
1. GPT-4 for news summarization
2. AI-powered signal detection
3. Automated expert insight extraction

### Phase 4: Premium Data (Month 2+)
1. Evaluate PitchBook/Dealroom partnerships
2. Tegus/AlphaSense for expert transcripts
3. Real-time valuation tracking

---

## Proposed GitHub Actions Schedule

```yaml
# .github/workflows/data-automation.yml
name: Data Automation Pipeline

on:
  schedule:
    # Funding & Valuations - Daily at 6 AM UTC
    - cron: '0 6 * * *'

  workflow_dispatch:  # Manual trigger

jobs:
  # Job 1: SEC Filings (already exists, enhance it)
  sec-filings:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python scripts/fetch_sec_filings.py

  # Job 2: Government Contracts (NEW)
  gov-contracts:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python scripts/fetch_usaspending.py

  # Job 3: News Aggregation (NEW)
  news-aggregation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: node scripts/aggregate_news.js

  # Job 4: Patent Tracking (NEW - weekly)
  patent-tracking:
    runs-on: ubuntu-latest
    if: github.event.schedule == '0 8 * * 0'  # Only on Sunday
    steps:
      - uses: actions/checkout@v4
      - run: python scripts/fetch_patents.py

  # Final: Commit all changes
  commit-changes:
    needs: [sec-filings, gov-contracts, news-aggregation]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: |
          git config user.name "TIL Bot"
          git config user.email "bot@innovatorsleague.com"
          git add data.js
          git diff --staged --quiet || git commit -m "Auto-update: $(date +%Y-%m-%d)"
          git push
```

---

## Data Quality & Verification

### Automated Validation
```javascript
// scripts/validate_data.js
function validateCompany(company) {
  const errors = [];

  // Required fields
  if (!company.name) errors.push('Missing name');
  if (!company.sector) errors.push('Missing sector');
  if (!SECTORS[company.sector]) errors.push('Invalid sector');

  // Coordinate validation
  if (company.lat && (company.lat < -90 || company.lat > 90)) {
    errors.push('Invalid latitude');
  }

  // Funding validation
  if (company.totalRaised && !company.totalRaised.match(/\$[\d.]+[BMK]?\+?/)) {
    errors.push('Invalid funding format');
  }

  return errors;
}
```

### Change Detection & Alerts
```javascript
// Detect significant changes and alert
const ALERT_THRESHOLDS = {
  valuation_change: 0.20,  // 20% change triggers alert
  funding_round: true,     // Any new funding
  gov_contract: 10000000,  // $10M+ contracts
  patent_grant: true       // Any patent grant
};
```

---

## Cost Estimate

| Service | Monthly Cost | Data Provided |
|---------|-------------|---------------|
| Crunchbase Pro | $49 | Funding, investors, team |
| sec-api.io | $50 | Real-time SEC filings |
| GitHub Actions | Free | CI/CD automation |
| USPTO APIs | Free | Patent data |
| USAspending.gov | Free | Government contracts |
| RSS Feeds | Free | News aggregation |
| OpenAI API | ~$20 | AI summarization |
| **TOTAL** | **~$120/mo** | Core automation |

---

## Files to Create

```
innovators-league/
├── .github/
│   └── workflows/
│       ├── sec-filings.yml      ✅ (exists, enhance)
│       ├── gov-contracts.yml    🆕
│       ├── news-aggregation.yml 🆕
│       ├── patent-tracking.yml  🆕
│       └── data-validation.yml  🆕
├── scripts/
│   ├── fetch_sec_filings.py     ✅ (exists)
│   ├── fetch_usaspending.py     🆕
│   ├── fetch_patents.py         🆕
│   ├── aggregate_news.js        🆕
│   ├── filter_companies.js      🆕
│   ├── merge_to_datajs.py       🆕
│   └── validate_data.js         🆕
└── data.js                       ✅ (auto-updated)
```

---

## Next Steps

1. **Immediate (This Week):**
   - Set up USAspending.gov contract sync
   - Add RSS news aggregation
   - Enhance SEC filing automation

2. **Short Term (Next 2 Weeks):**
   - Add Crunchbase API integration
   - Set up USPTO patent tracking
   - Create data validation pipeline

3. **Medium Term (Month 1-2):**
   - AI-powered news summarization
   - Community expert submission system
   - Real-time signal detection

4. **Long Term (Month 3+):**
   - Evaluate premium data partnerships
   - Build investor dashboard
   - API for members

---

*This strategy positions The Innovators League as a living intelligence platform that compounds value over time through automated data collection and curation.*
