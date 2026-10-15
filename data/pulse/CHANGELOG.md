# The Build-Out Pulse — method changelog

Every change to how the number is made is logged here with a date and a version. Printed values are never silently restated; revisions are listed in `revisions.json` with the first print beside the revised value.

## v1.2.1 — 15 October 2026 (coverage, no method change)
- **Board registry.** The hard-coded board lists in `fetch_jobs.py` (198 boards, 114 of them dead 404s after companies changed ATS) are replaced by `data/pulse/job_boards.json`, one source of truth shared by the fetcher and discovery. Every entry carries the company name as data.js spells it, the platform, the slug, the date it last returned jobs and how it was found.
- **Verification before use.** A board is accepted when it is linked or embedded on the company's own careers page, or when the board itself names the company (organisation field, posting text or domain) and, for one-word matches, lists postings where the company is. Three boards that had been feeding the page under the wrong name (Govini→Air is a rebrand and stays; Newspace Research→Sonja Inc. and Thea Energy→Laboratoires Théa are not) are now rejected with the reason logged.
- **Eleven more platforms** fetched through keyless public endpoints: SmartRecruiters, Workday, Recruitee, Personio, Breezy, Pinpoint, Teamtailor, JazzHR and iCIMS join Greenhouse, Lever, Ashby, Workable, Rippling and BambooHR. Discovery now reads script embeds, iframes and JSON-LD JobPosting markup, follows the careers link from the homepage nav, includes public companies and re-checks companies whose board returns nothing.
- Pulse panels are unaffected until the next monthly compute; the board-change guard will flag any company whose count jumps because its board was re-found.

## v1.2 — 28 September 2026 (pre-publication audit)
- **US-only universe.** The Pulse describes the *American* build-out, but the database holds 364 non-US companies and several (Halter, ICEYE, Destinus, Isar Aerospace, The Exploration Company, Humanoid) were on the hiring panel. The universe is now private · active · **US-headquartered** · in-lane. Every month is recomputed and the revisions are logged.
- **Dedupe by posting id**, not by (company, title, location): a company hiring five technicians in one plant now counts five. Effect ≈0.5% of postings.
- **Board-change guard extended to the three-month lists** in the intelligence layer: a fall from ≥20 to ≤3 over three months is listed as a board check, never as runway stress.
- Revision reasons now state the method versions compared and what changed.
- A `verification` line ships inside every intel file: lists are signals; "none on record" means our feeds hold no dated round; verify each name before external use.

## v1.1 — 26 September 2026
- **Title taxonomy v1.1** (`scripts/pulse_taxonomy.py`): five classes — software, manufacturing, commercial, hardware, other — one classifier shared by every Pulse script. **Atoms/bits is now (manufacturing + hardware-engineering titles) ÷ software titles.** v1.0 counted only production and technician titles as "atoms" and left 62% of titles unclassified; v1.1 classifies 84%.
- **Board-change guard:** a company whose count collapses from ≥20 roles to ≤3 (or jumps the reverse way) is excluded from that month's panel and listed in `board_checks_<month>.json` until a human confirms it as a real contraction in `board_checks_confirmed.json`. Prevents a feed failure from printing as a layoff.
- **Bootstrap 90% interval** on the hiring diffusion (2,000 resamples of the panel), printed beside the number.
- **Breadth split** published: share up / flat / down, ISM-style.
- **Panel composition** published each month: by bucket, funding stage, founding year and state.
- **Revisions log** (`revisions.json`): any month whose recomputed diffusion differs from its first print is recorded with the reason.
- Rippling and BambooHR job boards added to the jobs feed (272 and 17 discovered boards respectively).

## v1.0 — 25 September 2026
- First build. Hiring diffusion on a constant panel from month-end git snapshots of the job-board feed (Greenhouse, Lever, Ashby, Workable); ±10% or ±3 roles; postings older than 365 days treated as ghosts; dedupe on (company, title, location).
- Capital events merged from the deals feed, SEC Form D, VC portfolio first-funded dates and company announcements; federal awards from USAspending; covered-panel breadth (+3 months / −12 months).
- Milestones and footprint from confirmed manual files; unconfirmed extractions to a review queue.
- Company Pulse scores, factory-coming flags, roles by state, cohort mortality, first prints kept.
- Backfill April–September 2026.
