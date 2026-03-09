#!/usr/bin/env python3
"""
Generate Weekly Intelligence Brief
Reads all data/*.json files, filters to last 7 days, builds structured brief JSON,
then POSTs to the Supabase Edge Function webhook to trigger email sends.

Usage:
  python scripts/generate_weekly_brief.py

Environment Variables:
  SUPABASE_URL          - Supabase project URL (required for webhook)
  BRIEF_WEBHOOK_SECRET  - Shared secret for authenticating the webhook POST
"""

import json
import os
import sys
import hashlib
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

# ── Paths ──────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
BRIEF_OUTPUT = os.path.join(DATA_DIR, 'weekly_brief.json')
PREV_SCORES_PATH = os.path.join(DATA_DIR, 'prev_week_scores.json')

# ── Cutoff: 7 days ago ────────────────────────────────────────────────
NOW = datetime.now(timezone.utc)
CUTOFF = NOW - timedelta(days=7)


def load_json(filename):
    """Load a JSON file from the data directory. Returns [] if missing or invalid."""
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def parse_date(date_str):
    """Parse various date formats into a timezone-aware datetime."""
    if not date_str:
        return None
    # Handle Unix timestamps (integers or strings)
    if isinstance(date_str, (int, float)):
        try:
            return datetime.fromtimestamp(date_str, tz=timezone.utc)
        except (ValueError, OSError):
            return None
    date_str = str(date_str).strip()
    # Try RFC 2822 format (e.g. "Mon, 09 Mar 2026 05:01:43 +0000")
    try:
        dt = parsedate_to_datetime(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        pass
    # Try ISO formats
    for fmt in ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%dT%H:%M:%S%z', '%Y-%m'):
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def is_recent(date_str, cutoff=CUTOFF):
    """Check if a date string is within the cutoff window."""
    dt = parse_date(date_str)
    if dt is None:
        return False
    return dt >= cutoff


def filter_recent(items, date_field):
    """Filter list of dicts to only those with a recent date."""
    return [item for item in items if is_recent(item.get(date_field))]


def summarize_deals():
    """New funding rounds from the last 7 days."""
    deals = load_json('deals_auto.json')
    recent = filter_recent(deals, 'date')
    if not recent:
        return None
    # Sort by amount descending (best deals first)
    def sort_key(d):
        amt = d.get('amount', '')
        if isinstance(amt, str):
            amt = amt.replace('$', '').replace('M', '').replace('B', '').strip()
            try:
                return float(amt)
            except ValueError:
                return 0
        return float(amt) if amt else 0
    recent.sort(key=sort_key, reverse=True)
    return {
        'title': 'New Funding Rounds',
        'icon': '\U0001f4b0',
        'count': len(recent),
        'items': [{
            'company': d.get('company', 'Unknown'),
            'amount': d.get('amount', 'Undisclosed'),
            'round': d.get('round', ''),
            'investor': d.get('investor', ''),
            'date': d.get('date', '')
        } for d in recent[:10]]  # Top 10
    }


def summarize_sec_filings():
    """SEC filings from the last 7 days."""
    filings = load_json('sec_filings_raw.json')
    recent = filter_recent(filings, 'date')
    if not recent:
        return None
    # Prioritize S-1 (IPOs) and 8-K (material events)
    priority = {'S-1': 0, 'S-1/A': 1, '8-K': 2, '10-K': 3, '10-Q': 4}
    recent.sort(key=lambda f: priority.get(f.get('form', ''), 99))
    return {
        'title': 'SEC Activity',
        'icon': '\U0001f4dc',
        'count': len(recent),
        'items': [{
            'company': f.get('company', 'Unknown'),
            'form': f.get('form', ''),
            'description': f.get('description', '')[:120],
            'date': f.get('date', ''),
            'isIPO': f.get('isIPO', False)
        } for f in recent[:8]]
    }


def summarize_news():
    """News signals from the last 7 days."""
    news = load_json('news_raw.json')
    recent = filter_recent(news, 'pubDate')
    if not recent:
        return None
    # Sort by impact if available
    recent.sort(key=lambda n: n.get('impact', 'medium') == 'high', reverse=True)
    return {
        'title': 'Market Signals',
        'icon': '\U0001f4f0',
        'count': len(recent),
        'items': [{
            'title': n.get('title', '')[:100],
            'source': n.get('source', ''),
            'company': n.get('matchedCompany', ''),
            'impact': n.get('impact', 'medium'),
            'type': n.get('type', '')
        } for n in recent[:8]]
    }


def summarize_hackernews():
    """Hacker News buzz from the last 7 days."""
    hn = load_json('hackernews_buzz_raw.json')
    recent = filter_recent(hn, 'date')
    if not recent:
        return None
    recent.sort(key=lambda h: h.get('score', 0), reverse=True)
    return {
        'title': 'Hacker News Buzz',
        'icon': '\U0001f525',
        'count': len(recent),
        'items': [{
            'title': h.get('title', '')[:100],
            'score': h.get('score', 0),
            'comments': h.get('comments', 0),
            'companies': h.get('companies', []),
            'url': h.get('hn_url', '')
        } for h in recent[:6]]
    }


def summarize_press_releases():
    """Press releases from the last 7 days."""
    pr = load_json('press_releases_raw.json')
    recent = filter_recent(pr, 'pubDate')
    if not recent:
        return None
    return {
        'title': 'Press Releases',
        'icon': '\U0001f4e2',
        'count': len(recent),
        'items': [{
            'title': p.get('title', '')[:120],
            'source': p.get('source', ''),
            'companies': p.get('companies', [])
        } for p in recent[:6]]
    }


def summarize_federal_register():
    """Federal Register notices from the last 7 days."""
    fr = load_json('federal_register_raw.json')
    recent = filter_recent(fr, 'publication_date')
    if not recent:
        return None
    # Prioritize significant rules
    recent.sort(key=lambda r: r.get('significant', False), reverse=True)
    return {
        'title': 'Federal Register',
        'icon': '\U0001f3db\ufe0f',
        'count': len(recent),
        'items': [{
            'title': r.get('title', '')[:120],
            'type': r.get('type', ''),
            'agencies': r.get('agencies', [])[:3],
            'significant': r.get('significant', False),
            'date': r.get('publication_date', '')
        } for r in recent[:6]]
    }


def summarize_contracts():
    """SAM.gov contract opportunities from the last 7 days."""
    contracts = load_json('sam_contracts_raw.json')
    recent = filter_recent(contracts, 'postedDate')
    if not recent:
        return None
    return {
        'title': 'Contract Opportunities',
        'icon': '\U0001f3e2',
        'count': len(recent),
        'items': [{
            'title': c.get('title', '')[:120],
            'agency': c.get('agency', ''),
            'value': c.get('value', ''),
            'date': c.get('postedDate', '')
        } for c in recent[:6]]
    }


def summarize_fda():
    """FDA actions from the last 7 days."""
    fda = load_json('fda_actions_raw.json')
    recent = filter_recent(fda, 'date')
    if not recent:
        return None
    return {
        'title': 'FDA Activity',
        'icon': '\U0001f48a',
        'count': len(recent),
        'items': [{
            'company': f.get('company', 'Unknown'),
            'product': f.get('product', ''),
            'type': f.get('type', ''),
            'status': f.get('status', ''),
            'date': f.get('date', '')
        } for f in recent[:6]]
    }


def summarize_insider_trading():
    """Insider transactions from the last 7 days."""
    insider = load_json('insider_transactions_raw.json')
    recent = filter_recent(insider, 'date')
    if not recent:
        return None
    # Sort by value descending
    def val_key(t):
        v = t.get('value', 0)
        return float(v) if v else 0
    recent.sort(key=val_key, reverse=True)
    return {
        'title': 'Insider Trading',
        'icon': '\U0001f50d',
        'count': len(recent),
        'items': [{
            'company': t.get('company', 'Unknown'),
            'insider': t.get('insider', ''),
            'transaction_type': t.get('transaction_type', ''),
            'shares': t.get('shares', ''),
            'value': t.get('value', ''),
            'date': t.get('date', '')
        } for t in recent[:8]]
    }


def summarize_score_changes():
    """Compare current innovator scores against previous week snapshot."""
    current_scores = load_json('innovator_scores_auto.json')
    if not current_scores:
        return None

    # Load previous week's scores
    prev_scores = []
    if os.path.exists(PREV_SCORES_PATH):
        try:
            with open(PREV_SCORES_PATH, 'r') as f:
                prev_scores = json.load(f)
        except (json.JSONDecodeError, IOError):
            prev_scores = []

    if not prev_scores:
        # First run — no comparison possible, just save snapshot
        return None

    # Build lookup by company name
    prev_lookup = {s.get('company', ''): s.get('composite', 0) for s in prev_scores}

    movers = []
    for score in current_scores:
        company = score.get('company', '')
        current_composite = score.get('composite', 0)
        prev_composite = prev_lookup.get(company)
        if prev_composite is not None and current_composite and prev_composite:
            try:
                change = float(current_composite) - float(prev_composite)
                if abs(change) >= 2:  # Only significant moves (2+ points)
                    movers.append({
                        'company': company,
                        'current': current_composite,
                        'previous': prev_composite,
                        'change': round(change, 1),
                        'tier': score.get('tier', '')
                    })
            except (ValueError, TypeError):
                continue

    if not movers:
        return None

    # Sort by absolute change
    movers.sort(key=lambda m: abs(m['change']), reverse=True)

    return {
        'title': 'Top Score Movers',
        'icon': '\U0001f4c8',
        'count': len(movers),
        'items': movers[:10]
    }


def save_score_snapshot():
    """Save current scores as the baseline for next week's comparison."""
    current_scores = load_json('innovator_scores_auto.json')
    if current_scores:
        with open(PREV_SCORES_PATH, 'w') as f:
            json.dump(current_scores, f, indent=2)
        print(f"  Saved score snapshot: {len(current_scores)} companies")


def build_brief():
    """Build the complete weekly brief."""
    brief_date = NOW.strftime('%Y-%m-%d')
    brief_display_date = NOW.strftime('%b %d, %Y')

    print(f"Generating Weekly Intelligence Brief for {brief_display_date}")
    print(f"  Cutoff: {CUTOFF.strftime('%Y-%m-%d %H:%M UTC')}")
    print()

    sections = []
    generators = [
        ('Score Changes', summarize_score_changes),
        ('Funding', summarize_deals),
        ('SEC', summarize_sec_filings),
        ('Contracts', summarize_contracts),
        ('FDA', summarize_fda),
        ('Federal Register', summarize_federal_register),
        ('Insider Trading', summarize_insider_trading),
        ('News', summarize_news),
        ('HN Buzz', summarize_hackernews),
        ('Press Releases', summarize_press_releases),
    ]

    for label, gen_fn in generators:
        try:
            section = gen_fn()
            if section:
                sections.append(section)
                print(f"  {section['icon']} {section['title']}: {section['count']} items")
            else:
                print(f"  \u2013 {label}: no recent data")
        except Exception as e:
            print(f"  \u26a0\ufe0f {label}: error - {e}")

    brief = {
        'date': brief_date,
        'display_date': brief_display_date,
        'generated_at': NOW.isoformat(),
        'cutoff': CUTOFF.isoformat(),
        'section_count': len(sections),
        'total_items': sum(s.get('count', 0) for s in sections),
        'sections': sections
    }

    # Generate a unique brief ID for dedup
    brief_hash = hashlib.md5(json.dumps(brief, sort_keys=True).encode()).hexdigest()[:12]
    brief['brief_id'] = f"brief-{brief_date}-{brief_hash}"

    return brief


def send_to_webhook(brief):
    """POST the brief JSON to the Supabase Edge Function webhook."""
    supabase_url = os.environ.get('SUPABASE_URL', '')
    webhook_secret = os.environ.get('BRIEF_WEBHOOK_SECRET', '')

    if not supabase_url or not webhook_secret:
        print("\n  Skipping webhook (SUPABASE_URL or BRIEF_WEBHOOK_SECRET not set)")
        print("  Brief saved locally only.")
        return False

    import requests

    webhook_url = f"{supabase_url}/functions/v1/weekly-brief"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {webhook_secret}'
    }

    try:
        resp = requests.post(webhook_url, json=brief, headers=headers, timeout=30)
        if resp.status_code == 200:
            result = resp.json()
            print(f"\n  Webhook success: {result.get('emails_sent', 0)} emails sent")
            return True
        else:
            print(f"\n  Webhook error: {resp.status_code} - {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"\n  Webhook failed: {e}")
        return False


def main():
    # Build the brief
    brief = build_brief()

    # Save to file
    with open(BRIEF_OUTPUT, 'w') as f:
        json.dump(brief, f, indent=2)
    print(f"\n  Saved brief to {BRIEF_OUTPUT}")
    print(f"  Sections: {brief['section_count']}, Total items: {brief['total_items']}")

    # Save score snapshot for next week's comparison
    save_score_snapshot()

    # Send to webhook
    if brief['section_count'] > 0:
        send_to_webhook(brief)
    else:
        print("\n  No sections with data — skipping email send.")

    print("\nDone!")


if __name__ == '__main__':
    main()
