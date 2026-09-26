# The Build-Out Pulse — data access (v1)

Static, versioned files. Stable paths; fields are added, never renamed within a major version. Free to cite with attribution ("The Build-Out Pulse, The Innovators League / RiskHedge"). Commercial reuse, redistribution or inclusion in a product needs a licence: contact@rationaloptimistsociety.com.

| File | What | Cadence |
|---|---|---|
| `data/pulse/pulse_latest.json` | The current print: `latest` (this month's row), `latest_buckets`, `history`, `buckets`, `movers`, `scores` (top 25), `states`, `board_checks`, `composition`, `revisions`, `mortality`, `intel` (paid layer), `method_version`, `taxonomy_version`, `thresholds`, `weights` | Monthly, 1st, 12:00 UTC; nowcast refreshed with each recompute |
| `data/pulse/pulse_history.csv` | One row per month. Columns: month, is_nowcast, asof, method, hiring_panel, hiring_up, hiring_flat, hiring_down, share_up_pct, share_down_pct, hiring_diffusion, hiring_ci_lo, hiring_ci_hi, hiring_diffusion_first_print, board_checks, open_roles, open_roles_prev, roles_mom_pct, manufacturing_roles, hardware_roles, software_roles, commercial_roles, mfg_roles (= atoms), sw_roles, atoms_bits_ratio, factory_flags, capital_diffusion_covered, capital_panel, capital_events_3m, capital_rate_per100_3m, contracts_diffusion_covered, contracts_panel, contracts_events_3m, contracts_rate_per100_3m, milestones_diffusion, milestone_events, footprint_diffusion, footprint_events, pulse_hiring, pulse_v0_composite, components_live | Monthly |
| `data/pulse/pulse_buckets.csv` | One row per bucket per month: panel, up, down, hiring_diffusion, open_roles, atoms (mfg_roles), sw_roles, manufacturing_roles, hardware_roles, commercial_roles, senior_roles, atoms_bits, sufficient | Monthly |
| `data/pulse/movers_<YYYY-MM>.json` | Top-10 up, top-5 down, factory-coming flags | Monthly |
| `data/pulse/company_scores_<YYYY-MM>.json` | Top-50 company Pulse scores | Monthly |
| `data/pulse/states_<YYYY-MM>.json` | Roles by state with atoms/software split | Monthly |
| `data/pulse/composition_<YYYY-MM>.json` | Panel composition by bucket, stage, founding year, state | Monthly |
| `data/pulse/board_checks_<YYYY-MM>.json` | Companies excluded from the panel pending confirmation of a board change | Monthly |
| `data/pulse/intel_<YYYY-MM>.json` | About-to-build, about-to-raise, Portfolio Pulse, the studies, Pulse-to-ticker (paying tiers; runway-stress names excluded from the public file) | Monthly |
| `data/pulse_companies_auto.js` | Per-company benchmark data for benchmark.html (free) | Monthly |
| `data/pulse/README-METHOD.md`, `CHANGELOG.md`, `PREREGISTRATION.md`, `revisions.json`, `first_prints.json` | Method, versions, pre-registered studies, revisions | As changed |

Definitions: `README-METHOD.md`. Method version is printed in every file. Questions about a number: contact@rationaloptimistsociety.com, two-hour reply during US hours for licence holders.
