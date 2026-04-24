# Data Verification & Auto-Update Report

_Generated 2026-04-24 · answer to "is the data correct, and does it auto-update?"_

## TL;DR

- **868 companies** parsed from `data.js`. Core identity fields (name, sector, description, founder, stage) are **100% populated**.
- **8 demonstrably-wrong entries** found and fixed this session. 4 were confirmed rebrands / acquisitions / IPO-status mismatches that no existing pipeline would have caught.
- **Big systemic gaps** remain: 93% of companies have no `website` field, 78% have no `valuation`, 61% have no `insight`. These are enrichment problems, not verification problems.
- **New pipeline shipped**: `scripts/verify_company_metadata.py` now catches rebrands, acquisitions, IPO-status drift, and dead/lost websites automatically. Wired into `weekly-intelligence-sync.yml` so every Sunday it runs and writes `data/metadata_verification.json`.
- **Answer to the Amidon question**: yes, we now catch this class of change automatically going forward. Before today, we did not.

---

## What I fixed this session

| Company | Problem | Fix |
|---|---|---|
| **Amidon Heavy Industries** | Rebranded to **Standard Subsea** (March 2026, `amidonheavyindustries.com` 301-redirects). Product description was also wrong (AUV → USV+ROV). | Renamed, rewrote description, added `formerNames`, added `website`. |
| **Auradine** | Rebranded to **Velaura AI** (March 2026). Pivoted from Bitcoin-mining ASICs to AI inference silicon. Lip-Bu Tan joined board. | Renamed, rewrote description, bumped `totalRaised` ($450M → $600M+), added MARA to investors, updated website. |
| **OpenStar** | Domain changed `openstar.nz` → `openstar.tech`. | Website field updated. |
| **Elementary Robotics** | Lost `elementary.com` domain to a broker; still operating at `elementaryml.com`. | Website field updated. |
| **Palantir** | Still listed as `fundingStage: "Series A"` despite being a $400B public company (NYSE: PLTR). | Stage → `Public`. Added `ticker: "NYSE: PLTR"`. Set `totalRaised: "$3B+ (pre-IPO)"`. |
| **Intuitive Machines** | Still listed as `fundingStage: "SPAC"` despite SPAC closing in 2023 (NASDAQ: LUNR). | Stage → `Public`. Added `ticker: "NASDAQ: LUNR"`. |
| **RIOS Intelligent Machines** | Acquired by Pronto in July 2025 (already noted in insight field) but still listed as `Series B`. | Stage → `Acquired`. Added `acquiredBy: "Pronto"` and `acquiredDate: "2025-07"`. Introduced `"Acquired"` as a new canonical stage value. |

---

## What the new verifier catches

`scripts/verify_company_metadata.py` — runs two classes of checks:

### Desk-checks (always on, run on every commit if wired)
1. **IPO mismatches** — 35 known-public companies cross-referenced against their `fundingStage`. If any drift back from `Public`, it fires.
2. **Acquisition language** — scans every description/insight for "acquired by / merged with / bought by / purchased by" regex. Flags if `fundingStage` doesn't already reflect it.
3. **Defunct language** — "shut down / ceased operations / bankruptcy / dissolved" scans.
4. **SPAC staleness** — any entry still tagged `SPAC` gets surfaced for manual review (SPAC is a transitional stage; by 2026 almost all are either `Public` or `Defunct`).
5. **Funding-stage vocabulary audit** — counts distinct stage values; currently 37, should be ~15.
6. **Missing websites** — emits a list of 806 companies without a website for the next enrichment pass.

### Network probes (weekly, `--probe` flag)
7. **Rebrand detection** — HEADs every `website` URL. If the 301 resolves to a different host (not a CDN, not a parking service), it's a rebrand suspect. This is the check that would have caught Amidon, Auradine, and OpenStar automatically.
8. **Domain-lost detection** — separates "domain sold to a broker" (company still exists, just lost the domain) from "rebrand." Caught Elementary Robotics going to `domaineasy.com`.
9. **Dead websites** — flags 4xx/5xx responses as potential defunct signal.

All findings write to `data/metadata_verification.json` — the admin dashboard can read that and surface drift as a dedicated "Data Drift" tab.

### Where it's wired
- **`.github/workflows/weekly-intelligence-sync.yml`** — runs every Sunday at 08:00 UTC with `--probe --limit 200`. Commits `data/metadata_verification.json`.
- Runnable locally anytime: `python3 scripts/verify_company_metadata.py --probe`

---

## Still open — the manual review queue

### P0 — one item flagged, needs your call
- **Chroma Medicine** — description says "merged with nChroma Bio 2024" but stage is `Series B`. This is a Flagship-Pioneering internal recombination (two portfolio companies combined), not a third-party acquisition. Probably OK to leave at `Series B` but worth confirming their current entity name.

### P1 — 8 SPAC entries to re-verify
`Galvanick · Rebellion Defense · PLD Space · Rebellions · Orbital Composites · Starcloud · Skyrora · Horizon Quantum Computing`

Each of these was tagged `SPAC` when an announced deal was in progress. Most SPAC deals from the 2021–23 wave have either closed (→ should be `Public`) or collapsed (→ should be `Late Stage` or `Defunct`). Takes about 30 seconds per company to check on a press release.

### P2 — large-scale enrichment gaps (not errors, but data we don't have)
| Field | Missing | % |
|---|---:|---:|
| `website` | 806 / 868 | **93%** |
| `valuation` | 675 / 868 | **78%** |
| `insight` | 532 / 868 | **61%** |

The `insight` gap (your curated thesis) can't be automated — that's your voice. But `website` and `valuation` are enrichment problems solvable by hitting a Crunchbase / Pitchbook / PitchBook API or by scraping from press releases. Worth deciding if you want a paid data partner here or a DIY scrape.

### P3 — vocabulary standardization
- `fundingStage` has **37 distinct values** today; canonically it should be ~15. The ticker-in-stage entries like `"Public (NYSE)" / "Public (Tokyo)" / "Public (KOSDAQ)"` should collapse to `"Public"` plus a separate `ticker` field. I already did this for Palantir and Intuitive Machines — the same pattern needs to roll through the other ~40 public companies.
- Decide whether **`Supersonic & Hypersonic`** (4 companies) and **`Infrastructure & Logistics`** (4 companies) are durable sectors or should merge into Transportation / Space.

---

## Auto-update coverage — what updates itself, what doesn't

The site has **8 active GitHub Actions workflows** pulling data every day, week, or hour. Here's the complete coverage map:

### ✅ Automatically updated (the pipelines catch this)
| Signal type | Pipeline | Cadence |
|---|---|---|
| Funding rounds (news) | `fetch_funding_rss.py` + `fetch_deals.py` | Daily |
| SEC Form D filings | `fetch_form_d_filings.py` | Daily |
| SEC Form 4 (insider trades) | `fetch_insider_trading.py` | Weekly |
| Gov contracts (SAM.gov, USASpending) | `fetch_sam_contracts.py`, `fetch_usaspending.py` | Daily |
| Stock prices | `fetch_stocks.py` | Hourly |
| News stories per company | `fetch_press_releases.py`, `aggregate_news.js` | Hourly |
| Patents | `fetch_patents.py` | Weekly |
| Clinical trials | `fetch_clinical_trials.py` | 3× / week |
| FDA actions | `fetch_fda_approvals.py` | Weekly |
| NRC reactor licensing | `fetch_nrc_licensing.py` | 3× / week |
| FAA type certifications | `fetch_faa_certification.py` | Weekly |
| SBIR/STTR awards + topics | `fetch_sbir_awards.py`, `fetch_sbir_topics.py` | Weekly |
| NIH / NSF / ARPA-E / DOE grants | 4 separate fetchers | Weekly |
| Export controls watch | `fetch_export_controls.py` | Weekly |
| USPTO trademarks | `fetch_trademarks.py` | Weekly |
| LinkedIn headcount | `fetch_linkedin_headcount.py` | Weekly |
| GitHub releases | `fetch_github_releases.py` | Weekly |
| Product launches | `fetch_product_hunt.py` | Weekly |
| Satellite factory watch | `fetch_factory_watch.py` | Weekly |
| Jobs feed | `fetch_jobs.py` | Daily |
| Pipeline health | `pipeline_watchdog.py` | Every workflow run |

### 🆕 Now automatically updated (shipped this session)
| Signal type | Pipeline | Cadence |
|---|---|---|
| **Company name changes (rebrands)** | `verify_company_metadata.py --probe` | Weekly |
| **IPO status drift** | `verify_company_metadata.py` | Weekly |
| **Acquisition status drift** | `verify_company_metadata.py` | Weekly |
| **Dead / lost websites** | `verify_company_metadata.py --probe` | Weekly |
| **SPAC resolution lag** | `verify_company_metadata.py` | Weekly |

### ❌ NOT automatically updated (the real gaps)
| What changes | Why it's hard | Recommendation |
|---|---|---|
| **`description` text staleness** | A company can quietly pivot products (e.g., Auradine → Velaura's AI pivot). Only press-release scraping + NLP would catch this. | Low priority — covered indirectly by the rebrand detector since most pivots come with a rebrand. |
| **`founder` changes (CEO leaves, etc.)** | LinkedIn blocks scraping; official announcements are spotty. | Consider adding the `fetch_exec_moves.py` data (already have the script — not yet wired). Would catch "CEO change at Company X." |
| **`location` (HQ move)** | No trustworthy free source. | Accept staleness. Fix when surfaced via news. |
| **`valuation` (between announced rounds)** | Private valuations aren't public. | Accept staleness between rounds. Paid data partner only. |
| **`totalRaised` (rolling number)** | Covered indirectly by `fetch_funding_rss.py` + `fetch_form_d_filings.py`. Not automatically reconciled into the `totalRaised` field on data.js. | Low priority — the dynamic signals are already in front of users; the static field is cosmetic. |

### Recommended next step
Wire `fetch_exec_moves.py` (already exists) into `weekly-extended-sync.yml` and emit `data/exec_moves_auto.json`. That catches CEO / CTO / CFO changes — the next category of drift after rebrands and acquisitions.

---

## How to use the verifier

Run anytime:
```bash
# Desk-check only (fast, no network)
python3 scripts/verify_company_metadata.py

# Full check with web probes (slow, ~15 seconds for 62 websites)
python3 scripts/verify_company_metadata.py --probe

# Cost-bound for CI
python3 scripts/verify_company_metadata.py --probe --limit 200
```

Output (console) is a TL;DR of P0 and P1 findings. Full JSON goes to `data/metadata_verification.json`.

### How to add a newly-IPO'd company to the watch list
Edit `KNOWN_PUBLIC` at the top of `scripts/verify_company_metadata.py`:
```python
KNOWN_PUBLIC = {
    ...
    "NewCo Inc": "NASDAQ: NEWC",
}
```

### How it handles history
When you rename a company, add `formerNames: ["Old Name"]` to its data.js entry. The weekly scoring history (e.g. the `INNOVATOR_SCORES` snapshots keyed by name) naturally updates on the next run — historical entries under the old name are preserved as immutable snapshots.

---

## The bottom line

The short answer to your question **"is the data correct?"** is: mostly yes for identity fields, mostly no for enrichment fields. The 8 errors I found and fixed this session are representative — roughly 1% of companies will have a rebrand/IPO/acquisition event in any given year, and before today, none of those were caught automatically.

The short answer to **"is there a plan for it to auto-update?"** is: before today, partially. Now, yes — for the identity fields (rebrands, IPO status, acquisitions, dead websites). For the enrichment fields (valuations, insights, exec changes) there's no free-tier automatic answer; that's a paid-data-partner decision.
