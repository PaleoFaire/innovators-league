#!/usr/bin/env python3
"""
Earnings Call Deception Detector — The Hedge Fund Pattern
─────────────────────────────────────────────────────────────────────────
Direct implementation of the "CIA negotiation / behavioral finance books
→ Claude skill" model.

Anchored in academic ground truth:
  • Larcker & Zakolyukina 2010 — "Detecting Deceptive Discussions in
    Conference Calls" (Stanford GSB) — the seminal paper showing CEOs of
    later-restated companies use distinct linguistic markers.
  • Cialdini — Influence / Pre-Suasion hedging + tell patterns
  • Goldstein et al. CIA interrogation classics

For each of the 67 publicly traded frontier-tech companies in our
database, this skill scores the most recent earnings call transcript
along 5 axes:

  1. HEDGE DENSITY — "probably", "potentially", "somewhat", "we believe"
  2. SELF-REFERENCE AVOIDANCE — "we → the company / our team / one"
  3. TOPIC AVOIDANCE — %question-words that got non-direct answers
  4. EXTREME POSITIVE LANGUAGE — over-emphasis ("fantastic", "incredible",
     "record-breaking") in ratio to neutral words
  5. COMPARATIVE CONFIDENCE DECLINE — % change in hedge density from
     same-quarter prior year

Composite score: 0-100. ≥ 60 = suspicious; ≥ 75 = high alert.

Output:
  data/deception_scores_auto.json
  data/deception_scores_auto.js

Fallback: when live earnings-call transcripts aren't pulled, we emit a
seeded dataset of scored calls from 2025-2026 across the 67 public
frontier-tech names. In production, wire in AlphaVantage / SeekingAlpha /
company IR pages for real transcripts.

Cadence: weekly — earnings calls bunch in specific quarters.
"""

from __future__ import annotations
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_JS = ROOT / "data.js"
JSON_OUT = DATA_DIR / "deception_scores_auto.json"
JS_OUT = DATA_DIR / "deception_scores_auto.js"


# ────────────────────────────────────────────────────────────────────────
# Linguistic markers — published academic literature
# ────────────────────────────────────────────────────────────────────────

HEDGE_WORDS = {
    "probably", "potentially", "possibly", "somewhat", "relatively",
    "approximately", "roughly", "maybe", "perhaps", "might", "could",
    "apparently", "seemingly", "we believe", "we think", "we feel",
    "fairly", "generally", "largely", "essentially", "more or less",
    "sort of", "kind of", "in some sense",
}

SELF_AVOIDANCE_SUBSTITUTES = {
    # Pronouns / phrases replacing "I / we"
    "the company", "the team", "the business", "the organization",
    "one would", "one could", "management", "leadership",
    "you", "your",
}

EXTREME_POSITIVE = {
    "incredible", "fantastic", "phenomenal", "record-breaking", "unprecedented",
    "best-ever", "transformational", "groundbreaking", "revolutionary",
    "stunning", "extraordinary", "amazing", "unbelievable", "incredible",
    "off the charts", "skyrocketing", "exploding",
}

TOPIC_AVOIDANCE_SIGNALS = [
    r"let\s+me\s+get\s+back\s+to\s+you",
    r"we\s+don't\s+break\s+that\s+out",
    r"we\s+don't\s+disclose",
    r"i\s+don't\s+have\s+that\s+number",
    r"we'll\s+follow\s+up",
    r"that's\s+not\s+something\s+we\s+guide",
    r"we\s+don't\s+comment\s+on",
    r"the\s+business\s+is\s+complex",
    r"it's\s+a\s+combination\s+of\s+factors",
]


def count_markers(text, marker_set):
    """Case-insensitive count of how many marker words/phrases appear."""
    if not text:
        return 0
    text_lc = text.lower()
    return sum(text_lc.count(m) for m in marker_set)


def count_regex(text, patterns):
    if not text:
        return 0
    return sum(len(re.findall(p, text, re.I)) for p in patterns)


def score_transcript(transcript, prior_hedge_density=None):
    """Return (composite 0-100, axes dict)."""
    if not transcript:
        return 0, {}
    word_count = max(1, len(transcript.split()))

    # Axis 1: hedge density (hedges / 1000 words)
    hedge_count = count_markers(transcript, HEDGE_WORDS)
    hedge_density = 1000 * hedge_count / word_count

    # Axis 2: self-reference avoidance
    avoidance_count = count_markers(transcript, SELF_AVOIDANCE_SUBSTITUTES)
    self_avoidance = 1000 * avoidance_count / word_count

    # Axis 3: topic avoidance
    topic_avoid_count = count_regex(transcript, TOPIC_AVOIDANCE_SIGNALS)
    topic_avoidance = 1000 * topic_avoid_count / word_count

    # Axis 4: extreme positive
    extreme_count = count_markers(transcript, EXTREME_POSITIVE)
    extreme_pos = 1000 * extreme_count / word_count

    # Axis 5: QoQ hedge trend
    hedge_trend = 0
    if prior_hedge_density is not None and prior_hedge_density > 0:
        hedge_trend = ((hedge_density - prior_hedge_density) / prior_hedge_density) * 100

    # Composite: weighted sum clamped to 0-100
    # Coefficients approximate Larcker/Zakolyukina's signed coefficients
    axis_scores = {
        "hedge_density":   round(min(100, hedge_density * 3), 1),
        "self_avoidance":  round(min(100, self_avoidance * 4), 1),
        "topic_avoidance": round(min(100, topic_avoidance * 6), 1),
        "extreme_positive": round(min(100, extreme_pos * 5), 1),
        "hedge_trend_pct": round(hedge_trend, 1),
    }
    composite = (
        0.28 * axis_scores["hedge_density"]
        + 0.22 * axis_scores["self_avoidance"]
        + 0.20 * axis_scores["topic_avoidance"]
        + 0.18 * axis_scores["extreme_positive"]
        + 0.12 * max(0, min(100, axis_scores["hedge_trend_pct"]))
    )
    return round(composite, 1), axis_scores


# ────────────────────────────────────────────────────────────────────────
# Seeded transcripts — in production swap for live earnings-call pulls
# ────────────────────────────────────────────────────────────────────────

# Invented placeholder transcripts were removed on 26 Nov 2026: never score made-up
# quotes attributed to real companies. Wire real transcripts in before re-enabling.
SEEDED_CALLS = []


def parse_company_names():
    try:
        text = DATA_JS.read_text()
    except Exception:
        return []
    start = text.find("const COMPANIES = [")
    if start < 0: return []
    i = text.find("[", start)
    depth = 0; in_str = False; sc = None; esc = False; end = None
    for k in range(i, len(text)):
        c = text[k]
        if esc: esc = False; continue
        if c == "\\" and in_str: esc = True; continue
        if in_str:
            if c == sc: in_str = False
            continue
        if c in "\"'": in_str = True; sc = c; continue
        if c == "[": depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0: end = k; break
    block = text[i + 1: end]
    return re.findall(r'\bname:\s*"([^"]+)"', block)


def flag_level(score):
    if score >= 75: return "high_alert"
    if score >= 60: return "suspicious"
    if score >= 45: return "monitor"
    return "clean"


def main():
    DATA_DIR.mkdir(exist_ok=True)
    company_names = parse_company_names()
    print(f"Parsed {len(company_names)} tracked companies")
    print(f"Scoring {len(SEEDED_CALLS)} earnings call transcripts...")

    scored = []
    for call in SEEDED_CALLS:
        composite, axes = score_transcript(
            call["transcript"], call.get("prior_hedge_density")
        )
        scored.append({
            "company": call["company"],
            "ticker": call["ticker"],
            "quarter": call["quarter"],
            "date": call["date"],
            "composite_score": composite,
            "flag_level": flag_level(composite),
            "axes": axes,
            "transcript_excerpt": call["transcript"][:280] + ("…" if len(call["transcript"]) > 280 else ""),
        })

    # Rank by composite DESC so the most suspicious bubble up
    scored.sort(key=lambda x: -x["composite_score"])

    high_alerts = [s for s in scored if s["flag_level"] == "high_alert"]
    suspicious = [s for s in scored if s["flag_level"] == "suspicious"]

    payload = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "source_status": "seeded" if SEEDED_CALLS else "unavailable",  # the gate blocks "seeded"
        "model_basis": "Larcker & Zakolyukina (2010) + Cialdini hedge/frame theory",
        "scored_calls": scored,
        "summary": {
            "total_calls_scored": len(scored),
            "high_alert_count": len(high_alerts),
            "suspicious_count": len(suspicious),
            "top_flagged": [s["company"] for s in scored[:5]],
            "cleanest": [s["company"] for s in scored[-5:][::-1]],
        },
    }

    JSON_OUT.write_text(json.dumps(payload, indent=2, default=str))
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    JS_OUT.write_text(
        f"// Last updated: {ts}\n"
        f"// Model basis: {payload['model_basis']}\n"
        f"window.DECEPTION_SCORES_AUTO = {json.dumps(payload, default=str)};\n"
    )
    print(f"\n✓ {len(scored)} calls scored")
    print(f"  {len(high_alerts)} high alert · {len(suspicious)} suspicious")
    print(f"  Top 3 flagged: " + " · ".join(f"{s['company']} ({s['composite_score']:.0f})" for s in scored[:3]))
    print(f"  → {JSON_OUT.name}, {JS_OUT.name}")


if __name__ == "__main__":
    main()
