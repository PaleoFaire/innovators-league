# The Build-Out Pulse — method v0 (shadow)

A monthly diffusion index of the private US hard-tech cohort tracked by The Innovators League. 50 = neutral; above 50 more companies are expanding than contracting.

**Universe.** Private (no ticker), status active, sectors inside the build-out (nuclear, power and grid, defence, space and aerospace, chips and quantum, autonomy and robotics, manufacturing and materials). Biotech, pure software and consumer companies are tracked but excluded from the headline. Dead and acquired companies stay in the history and leave the panel.

**Hiring (live).** Open roles per company from public job boards (Greenhouse, Lever, Ashby, Workable), month-end snapshots. Constant panel: only companies with a count in both the current and the prior month. Up = +10% or +3 roles; down = −10% or −3 roles. Diffusion = 50 + (share up − share down) × 50. Also reported: total open roles on the panel, month-on-month change, and the atoms/bits ratio — manufacturing, technician and production titles divided by software, data and product titles.

**Capital (live, covered panel).** Capital events from the deals feed and SEC Form D filings. On the panel of companies with any event on record: positive = an event in the trailing three months; negative = none in the trailing twelve. Also the all-cohort rate of companies with an event in the trailing three months, per 100.

**Contracts (live, covered panel).** New federal awards from USAspending/SAM on the same rules.

**Milestones and footprint (manual, from the Ladder).** `milestones.json` and `footprint.json` in this folder: `[{"company", "date": "YYYY-MM-DD", "direction": "up"|"down", "evidence": url}]`. Confirmed events only. Counted when present.

**Composite.** Weights hiring 30, capital 20, contracts 20, milestones 20, footprint 10, renormalised over the components that are live in a given month; `components_live` says which. The official composite starts when milestones are being logged. Until then `pulse_hiring` is the headline and `pulse_v0_composite` is for internal use.

**Revisions.** The current month is a nowcast (`is_nowcast = true`) and is recomputed at month-end; earlier months are recomputed from the same git snapshots and should not change. Any change to a printed month is logged here with the reason.

**Buckets.** A bucket is marked `sufficient` only with a panel of 20 or more.

**Never included.** Stock prices, news-mention counts, anything a company paid for. Every founder's own benchmark is free.

Files: `pulse_history.csv` (the series), `pulse_buckets.csv`, `movers_<month>.json`, `snapshots/<month>.json` (per-company counts), `pulse_latest.json`, and `../pulse_auto.js` for the site. Coverage is expanded by `scripts/discover_job_boards.py`, whose high-confidence finds are picked up automatically by `scripts/fetch_jobs.py`.
