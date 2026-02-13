# The Innovators League

**Frontier tech intelligence you can use tomorrow.**

500 companies across defense, space, energy, biotech, and robotics — ranked, tracked, and explained.

## Data Pipeline Status

| Workflow | Status | Frequency |
|----------|--------|-----------|
| News Sync | ![News](https://github.com/PaleoFaire/innovators-league/actions/workflows/hourly-news-sync.yml/badge.svg) | Every 4 hours |
| Daily Sync | ![Daily](https://github.com/PaleoFaire/innovators-league/actions/workflows/daily-data-sync.yml/badge.svg) | Daily at 6 AM UTC |
| Data Refresh | ![Refresh](https://github.com/PaleoFaire/innovators-league/actions/workflows/data-refresh.yml/badge.svg) | Every 6 hours |
| Weekly Patents | ![Patents](https://github.com/PaleoFaire/innovators-league/actions/workflows/weekly-patent-sync.yml/badge.svg) | Sundays 8 AM UTC |
| Data Pipeline | ![Pipeline](https://github.com/PaleoFaire/innovators-league/actions/workflows/weekly-update.yml/badge.svg) | Daily/Weekly/Monthly |

## Data Sources

| Source | Type | Update Frequency |
|--------|------|------------------|
| Companies | Manual + Automated | Daily |
| News Signals | RSS Aggregation | Every 4 hours |
| SEC Filings | SEC EDGAR API | Daily |
| Gov Contracts | USAspending.gov | Daily |
| Patents | USPTO PatentsView | Weekly |
| Funding Rounds | Press + Crunchbase | Daily |

## API Keys Required

| Key | Purpose | Status |
|-----|---------|--------|
| `FMP_API_KEY` | Market cap updates | Configured |
| `SAM_API_KEY` | Government contracts | Optional |

## Quick Links

- **Live Site**: https://paleofaire.github.io/innovators-league/
- **Investors**: https://paleofaire.github.io/innovators-league/investors.html
- **Visualizations**: https://paleofaire.github.io/innovators-league/visualizations.html

## Monitoring

Check workflow runs: [Actions](https://github.com/PaleoFaire/innovators-league/actions)

Last data update is shown on the site with the freshness indicator.

---

Built by the [Rational Optimist Society](https://www.rationaloptimistsociety.com)
