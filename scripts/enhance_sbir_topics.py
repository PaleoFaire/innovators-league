#!/usr/bin/env python3
"""
SBIR Topics Enhancement — full-COMPANIES matching + bid-fit scoring
─────────────────────────────────────────────────────────────────────────
The existing fetch_sbir_topics.py pulls SBIR/STTR solicitation topics
but its `relevantCompanies` list is driven by a tiny hand-curated map
(~10 companies per sector). There are **868 companies** in our
database; many more could bid on any given topic.

This script reads `sbir_topics_auto.js` and RE-COMPUTES the
`relevantCompanies` field using the full COMPANIES array. For each
topic we:

  1. Tokenize the topic title + description + sector tags
  2. Tokenize every tracked company's description/insight/thesisCluster
  3. Compute a TF-IDF-flavored relevance score
  4. Surface the top N companies as "bid-fit" matches

We also add a `bid_fit_score` (0-100) and a short `reason` string
explaining WHY each company matched — so the UI can show
"Anduril — 94% fit · matched on 'counter-UAS', 'electronic warfare',
'tactical autonomy'."

Inputs:
  data/sbir_topics_auto.js         — produced by fetch_sbir_topics.py
  data.js                          — COMPANIES array

Output:
  data/sbir_topics_enhanced.json   — full enriched list
  data/sbir_topics_auto.js         — rewritten in-place with new
                                     `bidFit` array per topic

Cadence: whenever fetch_sbir_topics.py runs (comprehensive-data-sync).
Runs AFTER fetch_sbir_topics.py in the workflow.
"""

import json
import math
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_JS = ROOT / "data.js"

TOPICS_JS = DATA_DIR / "sbir_topics_auto.js"
ENHANCED_JSON = DATA_DIR / "sbir_topics_enhanced.json"

STOPWORDS = {
    "the", "of", "and", "or", "a", "an", "for", "to", "by", "with", "in",
    "on", "at", "as", "is", "are", "be", "will", "this", "that", "these",
    "those", "its", "from", "into", "such", "other", "than", "via",
    "new", "advanced", "next", "generation", "novel", "innovative",
    "develop", "development", "research", "enable", "enabling",
    "solution", "solutions", "system", "systems", "technology",
    "technologies", "provide", "provides", "provided", "capability",
    "capabilities",
}


def tokenize(text):
    if not text:
        return []
    s = re.sub(r"[^a-z0-9 ]", " ", text.lower())
    s = re.sub(r"\s+", " ", s)
    return [t for t in s.split() if t not in STOPWORDS and len(t) >= 3]


def parse_companies():
    text = DATA_JS.read_text()
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
    block = text[i + 1:end] if end else ""

    companies = []
    # Split into per-company brace blocks
    idx = 0; n = len(block); d = 0; in_str = False; sc = None; esc = False
    while idx < n:
        while idx < n and block[idx] in " \t\n,": idx += 1
        if idx >= n: break
        if block[idx] != "{": idx += 1; continue
        s = idx
        while idx < n:
            c = block[idx]
            if esc: esc = False; idx += 1; continue
            if c == "\\" and in_str: esc = True; idx += 1; continue
            if in_str:
                if c == sc: in_str = False
                idx += 1; continue
            if c in "\"'": in_str = True; sc = c; idx += 1; continue
            if c == "{": d += 1
            elif c == "}":
                d -= 1
                if d == 0:
                    idx += 1
                    entry = block[s:idx]
                    def gs(f):
                        m = re.search(rf'\b{f}:\s*"((?:[^"\\]|\\.)*)"', entry)
                        return m.group(1) if m else ""
                    companies.append({
                        "name": gs("name"),
                        "sector": gs("sector"),
                        "description": gs("description"),
                        "insight": gs("insight"),
                        "thesisCluster": gs("thesisCluster"),
                        "founder": gs("founder"),
                    })
                    break
            idx += 1
    return [c for c in companies if c["name"]]


def parse_sbir_topics():
    """Extract the SBIR_TOPICS_AUTO array from the JS file."""
    text = TOPICS_JS.read_text()
    # Strip the "const SBIR_TOPICS_AUTO = " prefix and trailing semicolon
    m = re.search(r"=\s*(\[[\s\S]*?\])\s*;?\s*$", text)
    if not m:
        return []
    try:
        return json.loads(m.group(1))
    except Exception as e:
        print(f"  JSON parse error: {e}")
        return []


def company_vector(c):
    """Build a weighted token multiset for a company.
    Insight is highest-signal (curator-written thesis), then description,
    then thesisCluster, then founder text."""
    tokens = Counter()
    for weight, field in [(4, "insight"), (2, "description"), (3, "thesisCluster"), (1, "founder")]:
        for tok in tokenize(c.get(field, "")):
            tokens[tok] += weight
    # Sector gets its own heavy weight
    for tok in tokenize(c.get("sector", "")):
        tokens[tok] += 5
    return tokens


def score_match(topic_tokens, company_tokens, common_idf):
    """Return (score, matched_terms) where score is 0–100 and matched_terms
    is the top 3 overlapping tokens weighted by IDF (rare words count more)."""
    shared = set(topic_tokens) & set(company_tokens)
    if not shared:
        return 0.0, []
    # Weighted overlap — TF from company vector × IDF
    weighted = []
    for tok in shared:
        idf = common_idf.get(tok, 1.0)
        w = company_tokens[tok] * idf
        weighted.append((tok, w))
    weighted.sort(key=lambda x: -x[1])
    total_w = sum(w for _, w in weighted)
    # Normalize: divide by topic-token count to prevent topic-length bias
    normalized = total_w / max(4, len(topic_tokens))
    # Scale to 0–100 with a soft ceiling (20 = strong match in practice)
    score = min(100, normalized * 4)
    return score, [t for t, _ in weighted[:3]]


def main():
    print("=" * 68)
    print("SBIR Topics Enhancement — full-COMPANIES bid-fit scoring")
    print("=" * 68)

    companies = parse_companies()
    topics = parse_sbir_topics()
    if not topics:
        print("No SBIR topics file or empty — nothing to enhance.")
        return
    print(f"Topics: {len(topics)}  |  Companies: {len(companies)}")

    # IDF computed across all company vectors
    doc_freq = Counter()
    company_vectors = []
    for c in companies:
        v = company_vector(c)
        company_vectors.append(v)
        for tok in v:
            doc_freq[tok] += 1
    N = max(1, len(companies))
    idf = {t: math.log(1 + N / (1 + df)) for t, df in doc_freq.items()}

    # Score each topic against every company
    enhanced_topics = []
    for topic in topics:
        title = topic.get("title", "")
        desc  = topic.get("description", "")
        sectors = " ".join(topic.get("sectors", []) if isinstance(topic.get("sectors"), list) else [topic.get("sectors", "")])
        topic_tokens = tokenize(f"{title} {desc} {sectors}")

        # Score every company; keep top 8 above threshold
        ranked = []
        for c, cv in zip(companies, company_vectors):
            score, terms = score_match(topic_tokens, cv, idf)
            if score >= 8:
                ranked.append((c["name"], c["sector"], score, terms))
        ranked.sort(key=lambda x: -x[2])
        ranked = ranked[:8]

        bid_fit = [{
            "company":       name,
            "sector":        sector,
            "bid_fit_score": round(score, 1),
            "matched_terms": terms,
        } for name, sector, score, terms in ranked]

        # Preserve existing relevantCompanies (hand-curated) but also
        # surface our auto-scored bid-fit list.
        topic["bidFit"] = bid_fit
        topic["bidFitSource"] = "TF-IDF across insight/description/thesisCluster"
        enhanced_topics.append(topic)

    # Write back an enhanced JS file (same const name, richer content)
    header = (
        f"// Auto-generated SBIR topics + full-company bid-fit scoring\n"
        f"// Topics: {len(enhanced_topics)}  |  Matching: TF-IDF weighted\n"
        f"// Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
    )
    body = f"const SBIR_TOPICS_AUTO = {json.dumps(enhanced_topics, indent=2, ensure_ascii=False)};\n"
    TOPICS_JS.write_text(header + body)

    # Also write a pure-JSON companion for downstream tooling
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_topics": len(enhanced_topics),
        "topics": enhanced_topics,
    }
    ENHANCED_JSON.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {TOPICS_JS.name} + {ENHANCED_JSON.name}")

    if enhanced_topics[:3]:
        print("\nSample top bid-fits:")
        for t in enhanced_topics[:3]:
            print(f"\n  {t.get('title','')[:60]}")
            for bf in t.get("bidFit", [])[:3]:
                print(f"    {bf['company']:28s}  fit={bf['bid_fit_score']:5.1f}  terms={bf['matched_terms']}")


if __name__ == "__main__":
    main()
