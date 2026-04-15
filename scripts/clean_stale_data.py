#!/usr/bin/env python3
"""
Clean Stale Placeholder Data
============================
Idempotent cleanup for downstream-confusing placeholder artefacts that
accumulate in the data/ directory:

  1. `data/predictive_scores_auto.json` — replaces every "$TBD" string with
     `null` (recursively walks nested dicts/lists).
  2. `data/diffbot_enrichment_raw.json` — if the file contains Diffbot-style
     test / tier-label records (e.g. the sentinel "Founder Tier"), resets
     the whole file to `{"status": "uninitialized", "data": []}` so the
     enricher starts clean next run.
  3. Logs a line per cleaning action so CI surfaces what changed.

Standalone runnable:
    python3 scripts/clean_stale_data.py
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("clean_stale_data")

DATA_DIR = Path(__file__).parent.parent / "data"

# Sentinels that indicate test/tier-label data in diffbot_enrichment_raw.json.
DIFFBOT_TEST_MARKERS = {
    "Founder Tier",
    "Investor Tier",
    "Analyst Tier",
}


# ─────────────────────────────────────────────────────────────────
# Walker helpers
# ─────────────────────────────────────────────────────────────────
def replace_tbd(obj, counter):
    """Recursively replace '$TBD' (exact match) with None. Returns obj."""
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if isinstance(v, str) and v.strip() == "$TBD":
                obj[k] = None
                counter[0] += 1
            else:
                replace_tbd(v, counter)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, str) and v.strip() == "$TBD":
                obj[i] = None
                counter[0] += 1
            else:
                replace_tbd(v, counter)
    return obj


# ─────────────────────────────────────────────────────────────────
# Cleaners
# ─────────────────────────────────────────────────────────────────
def clean_predictive_scores():
    path = DATA_DIR / "predictive_scores_auto.json"
    if not path.exists():
        log.info("predictive_scores_auto.json not found — skipping")
        return 0
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        log.error(f"predictive_scores_auto.json: JSON parse error: {e}")
        return 0

    counter = [0]
    replace_tbd(data, counter)

    if counter[0] == 0:
        log.info("predictive_scores_auto.json: no $TBD strings found — already clean")
        return 0

    path.write_text(json.dumps(data, indent=2))
    log.info(
        f"predictive_scores_auto.json: replaced {counter[0]} '$TBD' strings with null"
    )
    return counter[0]


def clean_diffbot_enrichment():
    path = DATA_DIR / "diffbot_enrichment_raw.json"
    if not path.exists():
        log.info("diffbot_enrichment_raw.json not found — skipping")
        return False
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        log.error(f"diffbot_enrichment_raw.json: JSON parse error: {e}")
        return False

    # Already an uninitialized placeholder? leave alone
    if isinstance(data, dict) and data.get("status") == "uninitialized":
        log.info("diffbot_enrichment_raw.json: already uninitialized — skipping")
        return False

    # Detect test/tier-label pollution
    if isinstance(data, list):
        polluted = any(
            isinstance(item, dict) and (item.get("name") in DIFFBOT_TEST_MARKERS)
            for item in data
        )
    else:
        polluted = False

    if not polluted:
        log.info("diffbot_enrichment_raw.json: no tier-label test data — leaving as-is")
        return False

    reset = {
        "status": "uninitialized",
        "data": [],
        "reset_at": datetime.now().isoformat(),
        "reason": "Tier-label / test entries detected — reset for a clean enrichment run."
    }
    path.write_text(json.dumps(reset, indent=2))
    log.warning("diffbot_enrichment_raw.json: reset to uninitialized state")
    return True


# ─────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────
def main():
    log.info("=" * 60)
    log.info("Clean Stale Data")
    log.info("=" * 60)
    log.info(f"Data directory: {DATA_DIR}")
    log.info("=" * 60)

    changes = 0
    tbd_replaced = clean_predictive_scores()
    if tbd_replaced:
        changes += 1

    diffbot_reset = clean_diffbot_enrichment()
    if diffbot_reset:
        changes += 1

    log.info("=" * 60)
    if changes:
        log.info(f"Cleaned {changes} file(s). {tbd_replaced} $TBD replacements; "
                 f"diffbot reset: {diffbot_reset}.")
    else:
        log.info("No changes — everything already clean.")
    log.info("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
