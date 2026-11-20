# The Build-Out, Live: method v1.0

This file is written by `scripts/build_lagebild.py` from the constants in that script. Edit the script, not this file.

One page that turns each public sign that a tracked US company is building into one line with its source. Version 1 uses only data this repo already collects. Nothing is written by a language model and nothing is fetched at build time.

## The seven steps

1. **Collect from primary sources only.** SEC filings, federal award records, company newsrooms and public job boards. Feeds built from trade press are read so their rows can be counted and rejected. They are never published.
2. **Drop what is not an event.** A forecast, a likelihood, an estimate, a schedule or a data check is not an event. A summary row per company is not read as an event; the single rows behind it are.
3. **Fixed fields.** Company, event type, amount in US dollars (or empty), place, date, agency or programme where relevant, source. What the source data does not hold stays empty. Nothing is guessed. An amount in another currency is left empty, not converted.
4. **Place.** Town level only. Coordinates are rounded to 1 decimal place (about 11 km), so a point marks a town, never a building. When the source names no place, the event sits at the company's headquarters town and is labelled "HQ town". A place the repo cannot locate is listed but not mapped.
5. **One line per event.** A fixed template per event type fills in the fields. The finished line is then parsed back and every part is compared with the fields. Any mismatch rejects the event.
6. **Score.** Built only from the fields. See below.
7. **Publish with the source linked.** An event with no link to a primary source in repo data is rejected and counted in `rejected.json` with the reason. A follow-up (same company, same event type, within 30 days of the first event) is threaded onto the first event.

## Who is in scope

A company must match a record in `data.js` by its exact name, its name ignoring case, or a recorded former name. There is no fuzzy matching. The company must be headquartered in the United States.

## Event types

| Type | Key | Type points | Can earn first-of-kind points |
|---|---|---|---|
| Funding round | `round` | 20 | no |
| Debt financing | `debt` | 20 | no |
| SEC Form D | `form_d` | 10 | no |
| IPO filing | `ipo_filing` | 35 | yes |
| Federal contract | `contract` | 20 | yes |
| Federal grant | `grant` | 15 | yes |
| New location | `new_location` | 45 | yes |
| First manufacturing role | `first_mfg_role` | 45 | yes |
| Senior manufacturing role | `senior_mfg_role` | 35 | yes |
| Shift to production roles | `production_turn` | 35 | yes |
| Rise in open roles | `hiring_surge` | 25 | yes |

What each type means:

- **Funding round, debt financing.** A dated post on the company's own newsroom, or its own release on a press wire, whose headline states a completed raise by the company. The amount, round and valuation are taken from the headline, and the amount must agree with the newsroom collector's figure. A headline about a plan, an acquisition, a grant or a contract is not read as a round.
- **SEC Form D.** A filing matched to the company by its SEC number. The amount is the amount sold.
- **IPO filing.** A Form S-1 or F-1 registration statement. A pipeline estimate is not an event.
- **Federal contract.** One award from USAspending. The date is the award's start date as USAspending reports it.
- **Federal grant.** One National Science Foundation award to a tracked company.
- **Job-board signals.** Computed each week from public job boards (the weekly files in `data/pulse/signals/`): a new location (at least two postings in a state where the company listed none in the prior twelve weeks), a first manufacturing role (after at least four weeks without one), a senior manufacturing, plant or facilities role, a shift to production roles (the share of manufacturing and hardware titles up at least 15 points in twelve weeks), and a rise in open roles (up at least 30% in four weeks). The date is the day the signal was recorded. Two guards: a rise of more than 200% in four weeks, or a shift that starts from a share of zero, is treated as a change in the feed and rejected. These signals are held out of the public files until the build is run with `--include-job-signals`.

Never published: hiring pullbacks or any other negative or distress signal about a named company; investor names; anything from fund, brief or private files (the script refuses to open them).

## How this is ranked

`score = type points + dollar points + first-of-kind points`

- **Type points.** The table above. Types that carry a dollar figure start lower and earn most of their score from the dollars. Types that never carry a dollar figure start higher, in order of how directly they show building.
- **Dollar points.** `10 x log10(amount / $100K)`, never below 0 and never above 50, rounded to one decimal place. So $100K = 0.0, $1M = 10.0, $10M = 20.0, $100M = 30.0, $1B = 40.0, $10B = 50.0. An event with no dollar figure gets 0.
- **First-of-kind points.** 10 points when the event is the earliest of its type for that company in this site's record, and only where the record of that type starts at least 365 days before the event. The record includes rows that cannot be published only because they lack a link. These points are not given to funding rounds, debt financings or Form D filings, because this site's history of rounds is incomplete and a "first" claim could be wrong.
- **Order.** Higher score first. Ties: the newer event first, then the company name.

The formula is the same for every event. It is never tuned for one event.

## The counters on the page

All four cover the last 7 days up to the build date.

- **Funding rounds.** The number of funding-round threads.
- **Raised.** For each of those threads, the largest amount stated in the thread, added up. Debt financings and Form D filings are listed in the feed but not added, because a filing or a second post can repeat an announced round.
- **Federal contracts.** The number of contract events.
- **New locations and first manufacturing roles.** The number of those two job-board events.

## Why an event is rejected

Every rejected row is counted under one primary reason (the first that applies, in this order) and under every reason that applies.

| Reason | Meaning |
|---|---|
| `negative_signal` | Negative or distress signal about a named company. Never published. |
| `not_an_event` | A forecast, estimate, schedule or data check, not something that happened. |
| `company_not_in_database` | The company name does not match a record in data.js. |
| `outside_us` | The company is not headquartered in the United States. |
| `no_source_url` | The repo data holds no link to a primary source for the event. |
| `source_not_primary` | The link is not a secure link to a primary source: the company's own site, a filing or an award record. |
| `date_missing` | No date in the source data. |
| `date_not_a_day` | The date has no day (a month or a year only). |
| `date_future` | The date is after the build date. |
| `date_implausible` | The date is not a real date, is before 1990, or is before the company was founded. |
| `date_unreliable` | Several different announcements carry one identical timestamp. |
| `fields_not_confirmed` | The source does not state a completed event with these fields. |
| `fields_implausible` | The numbers look like a change in the data feed, not a real change. |
| `line_mismatch` | The written line did not match the fields when checked. |

## Known gaps in the source data

- `data/deals_auto.json` has no link field and its dates have no day. Every row is rejected. To publish them, the collector needs to store the address of the company's own announcement (or the SEC filing) and the full date.
- `data/gov_contracts_raw.json` has no link field. USAspending returns a `generated_internal_id` for each award. Storing `https://www.usaspending.gov/award/<generated_internal_id>` as `url`, the way `scripts/fetch_sbir_awards.py` already does, would let these awards through.
- `data/sec_filings_raw.json` holds accession numbers but no filing address.
- `data/launch_manifest_auto.json` is a list of upcoming launches. A list of completed launches with the operator's own link would be needed.

## Files

- `events.json`: every published event, with the fields, the line, the score and its parts, the thread, and where each field came from.
- `rejected.json`: counts by type, by source file and by reason. No company is named.
- `../lagebild_auto.js`: the last 90 days for the page.

## Run it

```
python3 scripts/build_lagebild.py --today 2026-11-20
python3 -m unittest scripts/tests/test_lagebild.py
```

The same `--today` and the same inputs give byte-identical files.
