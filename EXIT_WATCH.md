# Exit Watch — pre-company dealflow

**Live page:** `exitwatch.html`
**Pipeline:** `scripts/fetch_exit_watch.py` → `scripts/build_exit_watch.py`
**Automation:** `.github/workflows/exit-watch.yml` (daily, 06:20 UTC, Mon–Sat)

---

## The question it answers

Every other pipeline in this repo points **inward**: what is happening at the
companies in `COMPANIES`. `fetch_form_d_filings.py` scrapes Form D *"for
companies in our COMPANIES array."* `calc_founder_mafias.py` clusters companies
we already track by founder heritage. `fetch_exec_moves.py` watches C-suite
changes at tracked companies.

Exit Watch points **outward** and asks the opposite question:

> Which company is about to exist that is not in our database yet?

For a fund whose edge is being early, that is the only question that finds
companies **before they exist**.

---

## Why we do not detect departures

The obvious design is to watch when someone leaves SpaceX or Anduril. We
deliberately do not, for three reasons:

1. **LinkedIn has no lawful API for this** and scraping it is against their
   terms. Any product built that way is legally exposed and technically brittle.
2. **Departures are not public.** Most are never announced anywhere.
3. **We do not need to.** Formations announce themselves in public records.

So we detect the **formation**, then backfill the pedigree.

---

## The backbone: SEC Form D

Every US private raise over $5,000 triggers a Form D within 15 days of first
sale — filed **weeks or months before any press release**. It is an official
US government record, free, unauthenticated, and structured.

The XML gives us:

| Field | Why it matters |
|---|---|
| `entityName` | The new company |
| `industryGroupType` | Drops pooled funds and real estate — two thirds of all volume |
| `yearOfInc` | A 2026 incorporation filing its first Form D is precisely the signal |
| `totalAmountSold` | Capital actually raised, not announced |
| `dateOfFirstSale` | When the money moved |
| `relatedPersonInfo` | **The officers, by name** |

Roughly 120–170 Form Ds are filed every business day. About two thirds are
funds and real-estate vehicles, which the industry filter removes.

---

## The three matches

Every row is a claim about a **named private individual**, so each carries its
evidence and its confidence, and nothing is asserted that the record does not
support.

**Strong lead** — an officer's name matches a founder recorded in `COMPANIES`,
*and* the new entity's industry is adjacent to that founder's known sector.

**Lead** — a name match without sector corroboration, or a match on a name that
is common or ambiguous in our data. Shown with an explicit warning on the row.

**New formation** — no pedigree match. A newly incorporated frontier-adjacent
entity raising real money, surfaced with no claim about the people at all.

### These tiers describe lead strength, not truth

A name in a Form D matching a name in our database is a **hypothesis**. Names
collide. The page never says a person did anything — it says what the filing
says, what our database says, and how well they corroborate. Every row links
to the filing so it can be checked in one click.

---

## Accuracy guards

Two failure modes would embarrass us. Both are handled explicitly.

**1. Surfacing a tracked company's funding round as a "new formation."**
Form D issuers use full legal names — *Pixxel Space Technologies, Inc.* — while
our database holds trading names — *Pixxel*. Stem equality misses that. We test
distinctive-token containment in **both directions** and suppress the filing
entirely. Caught in testing: Pixxel and Antares Nuclear both leaked through the
naive matcher on the first run.

**2. False corroboration from vague industry codes.**
`Other Technology` covers everything from telehealth to rockets, so it cannot
corroborate anything. It is deliberately excluded from the sector-adjacency
map. Before that fix, a telehealth filing ranked as a robotics founder's next
company purely because both fall under "technology."

Also guarded: person keys resolving to more than one distinct individual are
demoted, and a hard-coded list of very common surnames cannot reach the top tier
on a name match alone.

---

## Known limits

- **US only.** A company incorporated in Delaware but operating abroad appears;
  one that never raises US capital does not.
- **Form D is filed after first sale.** Early relative to press coverage, not
  relative to the round itself.
- **The roster is the bottleneck.** Pedigree matching is only as good as the
  founders documented in `COMPANIES` — currently ~2,450 founder names, of which
  ~100 carry an explicit prior-employer mention. Growing that roster is the
  single highest-leverage improvement available.
- **Bootstrapped companies are invisible.** No raise, no Form D.

### The obvious next upgrade

Add `PATENTSVIEW_API_KEY` to repo secrets and mine **patent inventor history**
for pedigree. USPTO records show *"Inventor X, Assignee SpaceX"* — a public,
citable employment record. That would take the roster from hundreds to tens of
thousands of documented alumni, and every match would carry a patent number as
evidence rather than a text mention. See `scripts/API_STATUS.md`.

---

## Running it

```bash
python scripts/fetch_exit_watch.py --days 30     # sweep EDGAR
python scripts/build_exit_watch.py               # match and score
python scripts/build_exit_watch.py --min-score 40  # tighter queue
```

The fetcher caches every parsed accession in `data/.exit_watch_cache.json`, so
re-running overlapping windows is nearly free. A 30-day cold sweep takes roughly
25 minutes at the SEC's rate limit; the daily 10-day incremental takes a couple
of minutes.
