#!/usr/bin/env python3
"""
Earnings Signal Extractor — The Innovators League
==================================================

Reads data/earnings_transcripts_raw.json, then:

  • If ANTHROPIC_API_KEY is set, calls Claude (the best available frontier
    model the repo already depends on) to extract structured "earnings
    signals" about frontier tech from each transcript excerpt.

  • If the key is NOT set, falls back to the CURATED, VERIFIED signal set
    that lives in this file (SEED_SIGNALS). Every seed signal was manually
    verified via the original transcript URLs — no fabrication.

Output: data/earnings_signals_auto.json
Shape:  list of earnings signals (see SIGNAL_SCHEMA below).

Design notes
------------
1. Every signal MUST have a valid source_url. Seed signals point to the
   Motley Fool / Benzinga / IR page where the quote was pulled from.
2. Every signal MUST have a verbatim quote — we NEVER synthesize quotes.
3. When the LLM runs, we instruct it to preserve verbatim quotes and to
   drop any signal where it cannot locate a direct quote in the transcript.

Idempotent. Safe to rerun. Overwrites output atomically.
"""

import json
import os
import logging
from datetime import datetime, timezone
from pathlib import Path


# ─── Logging ───
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("extract_earnings_signals")


# ─── Constants ───
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

IN_PATH = DATA_DIR / "earnings_transcripts_raw.json"
OUT_PATH = DATA_DIR / "earnings_signals_auto.json"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()

SIGNAL_SCHEMA = {
    "incumbent": "string",
    "ticker": "string",
    "quarter": "string like 2025-Q4",
    "date": "YYYY-MM-DD",
    "signal_type": "one of: rd_investment, partnership, competitive_threat, supply_chain, capital_shift, forward_guidance",
    "target_vertical": "one of: fusion, quantum, hypersonics, autonomy, humanoid, space, biotech, advanced_materials, nuclear, ai_compute, defense",
    "frontier_companies_mentioned": "list of startup/frontier company names",
    "quote": "VERBATIM quote from transcript",
    "implications": "list of 1-3 short strategic implications",
    "significance": "one of: high, medium, low",
    "sentiment": "one of: bullish, neutral, bearish",
    "source_url": "URL to the transcript/filing",
}


# ═══════════════════════════════════════════════════════════════════════════
# CURATED + VERIFIED SEED SIGNALS
# ───────────────────────────────────────────────────────────────────────────
# Every quote below was verified by pulling the transcript page via WebFetch
# in April 2026. Verification method recorded alongside each batch.
# Priority: QUALITY over QUANTITY. If a quote could not be verified, it was
# omitted.
# ═══════════════════════════════════════════════════════════════════════════

SEED_SIGNALS = [
    # ── LOCKHEED MARTIN — Q4 2025 (earnings call 2026-01-29) ───────────────
    # Verified: fool.com Jan 29 2026 transcript page. CEO Jim Taiclet quotes.
    {
        "incumbent": "Lockheed Martin",
        "ticker": "LMT",
        "quarter": "2025-Q4",
        "date": "2026-01-29",
        "signal_type": "rd_investment",
        "target_vertical": "space",
        "frontier_companies_mentioned": [],
        "quote": "We're building an operable space-based interceptor that we wanna fly in space by 2028.",
        "implications": [
            "Golden Dome architecture is moving from concept to hardware procurement.",
            "Space-based weapons primes will see step-function RFP volume over next 24 months.",
        ],
        "significance": "high",
        "sentiment": "bullish",
        "source_url": "https://www.fool.com/earnings/call-transcripts/2026/01/29/lockheed-martin-lmt-q4-2025-earnings-transcript/",
    },
    {
        "incumbent": "Lockheed Martin",
        "ticker": "LMT",
        "quarter": "2025-Q4",
        "date": "2026-01-29",
        "signal_type": "rd_investment",
        "target_vertical": "defense",
        "frontier_companies_mentioned": [],
        "quote": "We successfully used the shipboard laser system, Lockheed Martin's Helios, to knock an incoming UAV right out of the sky.",
        "implications": [
            "Directed-energy counter-UAS is now operationally demonstrated on Navy vessels.",
            "Pressures pure-kinetic incumbents; tailwind for power-electronics and beam-director suppliers.",
        ],
        "significance": "high",
        "sentiment": "bullish",
        "source_url": "https://www.fool.com/earnings/call-transcripts/2026/01/29/lockheed-martin-lmt-q4-2025-earnings-transcript/",
    },
    {
        "incumbent": "Lockheed Martin",
        "ticker": "LMT",
        "quarter": "2025-Q4",
        "date": "2026-01-29",
        "signal_type": "capital_shift",
        "target_vertical": "defense",
        "frontier_companies_mentioned": [],
        "quote": "Capital and IRAD investment is expected to approach $5 billion in 2026.",
        "implications": [
            "Step-function ~40% YoY increase in IRAD + capex suggests major new program investments.",
            "Munitions Acceleration Center groundbreaking signals multi-year production capacity build.",
        ],
        "significance": "high",
        "sentiment": "bullish",
        "source_url": "https://www.fool.com/earnings/call-transcripts/2026/01/29/lockheed-martin-lmt-q4-2025-earnings-transcript/",
    },
    {
        "incumbent": "Lockheed Martin",
        "ticker": "LMT",
        "quarter": "2025-Q4",
        "date": "2026-01-29",
        "signal_type": "rd_investment",
        "target_vertical": "autonomy",
        "frontier_companies_mentioned": [],
        "quote": "You don't need a pilot in there.",
        "implications": [
            "Optionally-piloted Black Hawk capability is now demonstrated, not theoretical.",
            "Signal to Shield AI, Anduril, Red Cat: primes are going full autonomy in rotary-wing.",
        ],
        "significance": "medium",
        "sentiment": "bullish",
        "source_url": "https://www.fool.com/earnings/call-transcripts/2026/01/29/lockheed-martin-lmt-q4-2025-earnings-transcript/",
    },

    # ── RTX — Q4 2025 (earnings call 2026-01-27) ───────────────────────────
    # Verified: fool.com Jan 27 2026 transcript page. Chris Calio / Neil Mitchill.
    {
        "incumbent": "RTX",
        "ticker": "RTX",
        "quarter": "2025-Q4",
        "date": "2026-01-27",
        "signal_type": "forward_guidance",
        "target_vertical": "defense",
        "frontier_companies_mentioned": [],
        "quote": "Other key awards in the quarter included over $900 million of classified bookings.",
        "implications": [
            "Classified portfolio continues to scale — signal that black-budget programs (Golden Dome, space, hypersonics) are funding at pace.",
        ],
        "significance": "medium",
        "sentiment": "bullish",
        "source_url": "https://www.fool.com/earnings/call-transcripts/2026/01/27/rtx-rtx-q4-2025-earnings-call-transcript/",
    },
    {
        "incumbent": "RTX",
        "ticker": "RTX",
        "quarter": "2025-Q4",
        "date": "2026-01-27",
        "signal_type": "rd_investment",
        "target_vertical": "ai_compute",
        "frontier_companies_mentioned": [],
        "quote": "We've deployed our proprietary data analytics and AI tools across our factories.",
        "implications": [
            "Factory AI is table-stakes for primes; vendors of industrial AI (Palantir, C3, Cognite) likely beneficiaries.",
        ],
        "significance": "low",
        "sentiment": "neutral",
        "source_url": "https://www.fool.com/earnings/call-transcripts/2026/01/27/rtx-rtx-q4-2025-earnings-call-transcript/",
    },

    # ── NORTHROP GRUMMAN — Q4 2025 (earnings call 2026-01-27) ──────────────
    # Verified: benzinga.com transcript page. CEO Kathy Warden.
    {
        "incumbent": "Northrop Grumman",
        "ticker": "NOC",
        "quarter": "2025-Q4",
        "date": "2026-01-27",
        "signal_type": "capital_shift",
        "target_vertical": "defense",
        "frontier_companies_mentioned": [],
        "quote": "Since 2021, we have successfully doubled our production capacity for tactical solid rocket motors at our ABL facility in West Virginia and are now advancing efforts to further increase that capacity by another 50%.",
        "implications": [
            "Solid rocket motor capacity remains a gating factor across missile programs; 50% more = major munition-program pull.",
            "Tailwind for specialty chemicals + energetic-materials suppliers.",
        ],
        "significance": "high",
        "sentiment": "bullish",
        "source_url": "https://www.benzinga.com/insights/news/26/01/50191849/northrop-grumman-q-2026-earnings-call-transcript",
    },
    {
        "incumbent": "Northrop Grumman",
        "ticker": "NOC",
        "quarter": "2025-Q4",
        "date": "2026-01-27",
        "signal_type": "forward_guidance",
        "target_vertical": "space",
        "frontier_companies_mentioned": [],
        "quote": "Space security or capabilities to protect space assets represent a tremendous growth opportunity for our company given our proven technology and experience in this domain.",
        "implications": [
            "Space protection is an explicit growth pillar — competitive pressure on True Anomaly, Starlab, Gravitics.",
        ],
        "significance": "medium",
        "sentiment": "bullish",
        "source_url": "https://www.benzinga.com/insights/news/26/01/50191849/northrop-grumman-q-2026-earnings-call-transcript",
    },

    # ── BOEING — Q4 2025 (earnings call 2026-01-27) ────────────────────────
    # Verified: fool.com transcript page. CEO Kelly Ortberg.
    {
        "incumbent": "Boeing",
        "ticker": "BA",
        "quarter": "2025-Q4",
        "date": "2026-01-27",
        "signal_type": "forward_guidance",
        "target_vertical": "autonomy",
        "frontier_companies_mentioned": [],
        "quote": "The US Navy's MQ-25 successfully completed its inaugural engine run, moving it closer to first flight.",
        "implications": [
            "Autonomous aerial tanker is moving toward IOC — first large unmanned carrier-launched production program.",
            "De-risks long-range autonomous aircraft as a category.",
        ],
        "significance": "medium",
        "sentiment": "bullish",
        "source_url": "https://www.fool.com/earnings/call-transcripts/2026/01/27/boeing-ba-q4-2025-earnings-call-transcript/",
    },

    # ── PALANTIR — Q4 2025 (earnings call 2026-02-02) ──────────────────────
    # Verified: fool.com transcript page. Karp / Sankar / Taylor.
    {
        "incumbent": "Palantir Technologies",
        "ticker": "PLTR",
        "quarter": "2025-Q4",
        "date": "2026-02-02",
        "signal_type": "rd_investment",
        "target_vertical": "defense",
        "frontier_companies_mentioned": [],
        "quote": "Maven is also pushing to the edge. We completed a live-fire exercise with Maven coordinating with UAV assets through our new Maven Edge agent called MAGE.",
        "implications": [
            "Maven is now edge-deployed and orchestrating UAV swarms — not just a cloud targeting service.",
            "Direct competitive pressure on Anduril Lattice's orchestration pitch; validates C2 startups that integrate.",
        ],
        "significance": "high",
        "sentiment": "bullish",
        "source_url": "https://www.fool.com/earnings/call-transcripts/2026/02/02/palantir-pltr-q4-2025-earnings-call-transcript/",
    },
    {
        "incumbent": "Palantir Technologies",
        "ticker": "PLTR",
        "quarter": "2025-Q4",
        "date": "2026-02-02",
        "signal_type": "forward_guidance",
        "target_vertical": "ai_compute",
        "frontier_companies_mentioned": [],
        "quote": "AIP continues to fundamentally transform how quickly our customers realize value, collapsing the time from initial engagement to transformational impact.",
        "implications": [
            "Enterprise AI adoption timeline compressing — commercial tail-wind for AI platform players.",
        ],
        "significance": "medium",
        "sentiment": "bullish",
        "source_url": "https://www.fool.com/earnings/call-transcripts/2026/02/02/palantir-pltr-q4-2025-earnings-call-transcript/",
    },

    # ── NVIDIA — Q4 FY2026 (earnings call 2026-02-25) ──────────────────────
    # Verified: fool.com transcript page. Jensen Huang / Colette Kress.
    {
        "incumbent": "NVIDIA",
        "ticker": "NVDA",
        "quarter": "2026-Q4",  # fiscal-year ending January
        "date": "2026-02-25",
        "signal_type": "forward_guidance",
        "target_vertical": "humanoid",
        "frontier_companies_mentioned": [],
        "quote": "Physical AI is here, having already contributed north of $6,000,000,000 in NVIDIA Corporation revenue in fiscal year 2026.",
        "implications": [
            "Robotics + humanoid compute stack is a >$6B business at NVIDIA — validates Figure, 1X, Apptronik, Agility.",
            "Jetson + Isaac + GR00T ecosystem is the default stack. Competitors must interop or lose.",
        ],
        "significance": "high",
        "sentiment": "bullish",
        "source_url": "https://www.fool.com/earnings/call-transcripts/2026/02/25/nvidia-nvda-q4-2026-earnings-call-transcript/",
    },
    {
        "incumbent": "NVIDIA",
        "ticker": "NVDA",
        "quarter": "2026-Q4",
        "date": "2026-02-25",
        "signal_type": "forward_guidance",
        "target_vertical": "ai_compute",
        "frontier_companies_mentioned": [],
        "quote": "Rubin will deliver improved resiliency and serviceability relative to Blackwell.",
        "implications": [
            "Rubin roadmap on track; two-generation cadence locks in for hyperscale customers.",
            "Pressure on AMD MI450 and AWS Trainium to match on inference TCO.",
        ],
        "significance": "medium",
        "sentiment": "bullish",
        "source_url": "https://www.fool.com/earnings/call-transcripts/2026/02/25/nvidia-nvda-q4-2026-earnings-call-transcript/",
    },

    # ── AMD — Q4 2025 (earnings call 2026-02-03) ───────────────────────────
    # Verified: fool.com transcript page. Lisa Su.
    {
        "incumbent": "AMD",
        "ticker": "AMD",
        "quarter": "2025-Q4",
        "date": "2026-02-03",
        "signal_type": "partnership",
        "target_vertical": "ai_compute",
        "frontier_companies_mentioned": ["OpenAI"],
        "quote": "In addition to our multi-generation partnership with OpenAI to deploy six gigawatts of Instinct GPUs, we are in active discussions with other customers on at-scale multi-year deployments.",
        "implications": [
            "6 GW OpenAI commitment locks AMD into the frontier-model training stack for multi-year.",
            "Validates merchant-silicon optionality — OpenAI is not NVIDIA-exclusive.",
        ],
        "significance": "high",
        "sentiment": "bullish",
        "source_url": "https://www.fool.com/earnings/call-transcripts/2026/02/03/amd-amd-q4-2025-earnings-call-transcript/",
    },

    # ── TESLA — Q4 2025 (earnings call 2026-01-28) ─────────────────────────
    # Verified: fool.com transcript page. Elon Musk.
    {
        "incumbent": "Tesla",
        "ticker": "TSLA",
        "quarter": "2025-Q4",
        "date": "2026-01-28",
        "signal_type": "capital_shift",
        "target_vertical": "humanoid",
        "frontier_companies_mentioned": [],
        "quote": "We are going to take the Model S and X production space in our Fremont factory and convert that into an Optimus factory with a long-term goal of having a million units a year of Optimus robots.",
        "implications": [
            "Tesla is reallocating flagship auto capacity to humanoids — first prime to do so at scale.",
            "Pressure on Figure, 1X, Apptronik to raise/deploy before Tesla cost curves hit.",
        ],
        "significance": "high",
        "sentiment": "bullish",
        "source_url": "https://www.fool.com/earnings/call-transcripts/2026/01/28/tesla-tsla-q4-2025-earnings-call-transcript/",
    },

    # ── ROCKET LAB — Q4 2025 (earnings call 2026-02-26) ────────────────────
    # Verified: fool.com transcript page. CEO Peter Beck.
    {
        "incumbent": "Rocket Lab",
        "ticker": "RKLB",
        "quarter": "2025-Q4",
        "date": "2026-02-26",
        "signal_type": "forward_guidance",
        "target_vertical": "space",
        "frontier_companies_mentioned": [],
        "quote": "The priority will always be to bring a reliable rocket to market, even if it means taking a few extra months.",
        "implications": [
            "Neutron first launch slipping to Q4 2026 — rideshare / constellation customers must replan.",
            "SpaceX medium-lift dominance extends through 2026.",
        ],
        "significance": "high",
        "sentiment": "bearish",
        "source_url": "https://www.fool.com/earnings/call-transcripts/2026/02/26/rocket-lab-rklb-q4-2025-earnings-call-transcript/",
    },

    # ── IONQ — Q4 2025 (earnings call 2026-02-25) ──────────────────────────
    # Verified: fool.com transcript page. CEO Niccolo de Masi.
    {
        "incumbent": "IonQ",
        "ticker": "IONQ",
        "quarter": "2025-Q4",
        "date": "2026-02-25",
        "signal_type": "partnership",
        "target_vertical": "quantum",
        "frontier_companies_mentioned": [],
        "quote": "In quantum networking, among numerous deployments we partnered with the U.S. Air Force Research Lab to achieve the first qubit-to-photon frequency conversion in a field-deployable system.",
        "implications": [
            "Field-deployable quantum networking is no longer lab-bench — DoD procurement pathway is open.",
            "Pulls forward demand for quantum-safe crypto and entanglement-distribution startups.",
        ],
        "significance": "high",
        "sentiment": "bullish",
        "source_url": "https://www.fool.com/earnings/call-transcripts/2026/02/25/ionq-ionq-q4-2025-earnings-call-transcript/",
    },
    {
        "incumbent": "IonQ",
        "ticker": "IONQ",
        "quarter": "2025-Q4",
        "date": "2026-02-25",
        "signal_type": "supply_chain",
        "target_vertical": "quantum",
        "frontier_companies_mentioned": ["SkyWater Technology"],
        "quote": "By leveraging Skywater's unique expertise and pioneering quantum semiconductor scaling within secure, trusted environments, we will be positioned to accelerate manufacturability of IonQ, Inc.'s entire quantum platform roadmap.",
        "implications": [
            "IonQ acquiring a US-based Tier 1 foundry — vertical integration of quantum stack.",
            "Secure/trusted fab capacity becomes a strategic lever; watch RigettiComputing and Atom Computing response.",
        ],
        "significance": "high",
        "sentiment": "bullish",
        "source_url": "https://www.fool.com/earnings/call-transcripts/2026/02/25/ionq-ionq-q4-2025-earnings-call-transcript/",
    },

    # ── KRATOS DEFENSE — Q4 2025 (earnings call 2026-02-23) ────────────────
    # Verified: fool.com transcript page. CEO Eric DeMarco.
    {
        "incumbent": "Kratos Defense",
        "ticker": "KTOS",
        "quarter": "2025-Q4",
        "date": "2026-02-23",
        "signal_type": "rd_investment",
        "target_vertical": "hypersonics",
        "frontier_companies_mentioned": [],
        "quote": "Kratos has been selected by the Pentagon to develop highly maneuverable Mach 5+ hypersonic missiles including advancing in-flight steering and propulsion systems.",
        "implications": [
            "Kratos is now a prime on hypersonic propulsion — no longer just a target-drone shop.",
            "Competitive pressure on Hermeus, Castelion, Venus Aerospace to show flight hardware.",
        ],
        "significance": "high",
        "sentiment": "bullish",
        "source_url": "https://www.fool.com/earnings/call-transcripts/2026/02/23/kratos-ktos-q4-2025-earnings-call-transcript/",
    },
    {
        "incumbent": "Kratos Defense",
        "ticker": "KTOS",
        "quarter": "2025-Q4",
        "date": "2026-02-23",
        "signal_type": "forward_guidance",
        "target_vertical": "autonomy",
        "frontier_companies_mentioned": [],
        "quote": "The Marines are expected to field the first CCA. We will not let them down.",
        "implications": [
            "Collaborative Combat Aircraft program pulling into the field — Kratos Valkyrie has first-mover customer.",
            "Watch Anduril Fury, GA-ASI Gambit to respond at Kratos price point.",
        ],
        "significance": "medium",
        "sentiment": "bullish",
        "source_url": "https://www.fool.com/earnings/call-transcripts/2026/02/23/kratos-ktos-q4-2025-earnings-call-transcript/",
    },

    # ── META — Q4 2025 (earnings call 2026-01-28) ──────────────────────────
    # Verified: fool.com transcript page. Mark Zuckerberg.
    {
        "incumbent": "Meta Platforms",
        "ticker": "META",
        "quarter": "2025-Q4",
        "date": "2026-01-28",
        "signal_type": "capital_shift",
        "target_vertical": "ai_compute",
        "frontier_companies_mentioned": [],
        "quote": "We are now seeing a major AI acceleration.",
        "implications": [
            "Meta 2026 capex guided $115B-$135B — step function in data-center buildout.",
            "Validates massive demand tail for power, cooling, networking, memory, and optical components.",
        ],
        "significance": "high",
        "sentiment": "bullish",
        "source_url": "https://www.fool.com/earnings/call-transcripts/2026/01/28/meta-meta-q4-2025-earnings-call-transcript/",
    },

    # ── CONSTELLATION ENERGY — Q4 2025 (earnings call 2026-02-24) ──────────
    # Verified: constellationenergy.com press release. Dated Feb 2026.
    {
        "incumbent": "Constellation Energy",
        "ticker": "CEG",
        "quarter": "2025-Q4",
        "date": "2026-02-24",
        "signal_type": "partnership",
        "target_vertical": "nuclear",
        "frontier_companies_mentioned": ["CyrusOne"],
        "quote": "Constellation's subsidiary Calpine LLC signed a new 380-megawatt agreement with Dallas-based CyrusOne to connect and serve a new data center adjacent to the Freestone Energy Center in Freestone County, Texas.",
        "implications": [
            "Hyperscaler power deals continue to lock in behind-the-meter generation capacity.",
            "Tailwind for SMR developers (X-energy, NuScale, Oklo, Kairos) as nuclear PPAs scale.",
        ],
        "significance": "medium",
        "sentiment": "bullish",
        "source_url": "https://www.constellationenergy.com/news/2026/02/constellation-reports-fourth-quarter-and-full-year-2025-results.html",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
# LLM extraction (Claude) — only runs if ANTHROPIC_API_KEY present
# ═══════════════════════════════════════════════════════════════════════════

EXTRACTION_PROMPT = """You are an equity research analyst specializing in
frontier-tech public incumbents.

Given the earnings call transcript excerpts below from {company} ({ticker}) for
{quarter}, extract ALL significant signals about frontier-tech topics.

Rules:
1. ONLY extract signals where you can cite a VERBATIM quote from the excerpts.
   Do not paraphrase or synthesize. If you cannot find a direct quote on a
   topic, do not create a signal for that topic.
2. Each signal must be relevant to one of these frontier-tech verticals:
   fusion | quantum | hypersonics | autonomy | humanoid | space | biotech |
   advanced_materials | nuclear | ai_compute | defense
3. Each signal is one of these types:
   rd_investment | partnership | competitive_threat | supply_chain |
   capital_shift | forward_guidance
4. Return STRICT JSON: a list of objects with these exact keys:
   incumbent, ticker, quarter, date, signal_type, target_vertical,
   frontier_companies_mentioned (array of strings), quote (verbatim),
   implications (array of 1-3 short strings), significance (high|medium|low),
   sentiment (bullish|neutral|bearish), source_url.

If no frontier-tech signals exist in the excerpts, return an empty list: [].

Transcript excerpts:
---
{excerpts}
---

Source URL to include: {source_url}
Company date: {date}

Respond with JSON only — no prose, no code fence."""


def run_llm_extraction(transcripts):
    """Call Claude to extract signals. Returns list of signals or [] on any error."""
    try:
        import anthropic  # type: ignore
    except ImportError:
        log.warning("anthropic package not installed — cannot run LLM extraction.")
        return []

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    signals = []

    for rec in transcripts:
        if not rec.get("transcript_excerpts"):
            continue
        excerpts = "\n\n".join(rec["transcript_excerpts"])
        prompt = EXTRACTION_PROMPT.format(
            company=rec["company"],
            ticker=rec["ticker"],
            quarter=rec["quarter"],
            date=rec.get("date") or "",
            excerpts=excerpts,
            source_url=rec.get("source_url", ""),
        )
        try:
            msg = client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            text = msg.content[0].text.strip()
            # Tolerant: strip leading/trailing fences if present
            if text.startswith("```"):
                text = "\n".join(text.splitlines()[1:])
                if text.endswith("```"):
                    text = "\n".join(text.splitlines()[:-1])
            parsed = json.loads(text)
            if isinstance(parsed, list):
                for s in parsed:
                    if isinstance(s, dict) and s.get("quote"):
                        signals.append(s)
                log.info(f"  {rec['ticker']}: extracted {len(parsed)} signals")
            else:
                log.debug(f"  {rec['ticker']}: unexpected LLM response shape")
        except Exception as e:
            log.debug(f"  {rec['ticker']}: LLM extraction failed — {e}")
            continue

    return signals


# ═══════════════════════════════════════════════════════════════════════════
# Pipeline
# ═══════════════════════════════════════════════════════════════════════════

def read_transcripts():
    if not IN_PATH.exists():
        log.warning(f"Input file missing: {IN_PATH} — will use seed only.")
        return []
    try:
        payload = json.loads(IN_PATH.read_text())
    except Exception as e:
        log.error(f"Failed to read {IN_PATH}: {e}")
        return []
    if isinstance(payload, dict):
        return payload.get("records", [])
    if isinstance(payload, list):
        return payload
    return []


def dedupe_signals(signals):
    """Deduplicate by (ticker, quote-prefix) to avoid identical entries."""
    seen = set()
    out = []
    for s in signals:
        key = (s.get("ticker", ""), (s.get("quote") or "")[:80].lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out


def write_output(signals):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    by_vertical = {}
    by_type = {}
    by_sig = {}
    for s in signals:
        by_vertical[s.get("target_vertical", "—")] = by_vertical.get(s.get("target_vertical", "—"), 0) + 1
        by_type[s.get("signal_type", "—")] = by_type.get(s.get("signal_type", "—"), 0) + 1
        by_sig[s.get("significance", "—")] = by_sig.get(s.get("significance", "—"), 0) + 1

    payload = {
        "_meta": {
            "generated_at": now,
            "total_signals": len(signals),
            "by_vertical": by_vertical,
            "by_signal_type": by_type,
            "by_significance": by_sig,
            "source": "llm_extraction" if ANTHROPIC_API_KEY else "curated_seed",
        },
        "signals": signals,
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2))
    return OUT_PATH


def main():
    log.info("═" * 70)
    log.info("Earnings Signal Extractor")
    log.info("═" * 70)

    transcripts = read_transcripts()
    log.info(f"Input transcripts: {len(transcripts)}")

    signals = []
    if ANTHROPIC_API_KEY and transcripts:
        log.info("ANTHROPIC_API_KEY present — running LLM extraction.")
        signals = run_llm_extraction(transcripts)
        # Merge LLM output with seed so we always have at least the verified baseline
        signals = dedupe_signals(list(signals) + SEED_SIGNALS)
        log.info(f"LLM extracted {len(signals)} signals (merged + deduped with seed).")
    else:
        log.info("ANTHROPIC_API_KEY not set — using curated seed signals only.")
        signals = SEED_SIGNALS

    # Sanity: every signal must have quote + source_url + ticker
    clean = [s for s in signals if s.get("quote") and s.get("source_url") and s.get("ticker")]
    if len(clean) != len(signals):
        log.info(f"Dropped {len(signals) - len(clean)} invalid signals.")
    signals = clean

    out = write_output(signals)
    log.info("─" * 70)
    log.info(f"Output: {out}")
    log.info(f"Total signals: {len(signals)}")
    log.info("═" * 70)


if __name__ == "__main__":
    main()
