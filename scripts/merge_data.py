#!/usr/bin/env python3
"""
Data Merger for The Innovators League
Merges auto-generated data from various sources into data.js
"""

import json
import re
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_JS_PATH = Path(__file__).parent.parent / "data.js"

def load_json(filename):
    """Load JSON data from the data directory."""
    filepath = DATA_DIR / filename
    if filepath.exists():
        with open(filepath) as f:
            return json.load(f)
    return []

def format_js_array(name, data, indent=2):
    """Format Python data as a JavaScript array."""
    lines = [f"const {name} = ["]

    for item in data:
        item_lines = []
        item_lines.append("  {")

        for key, value in item.items():
            if isinstance(value, str):
                # Escape quotes and newlines
                escaped = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')
                item_lines.append(f'    {key}: "{escaped}",')
            elif isinstance(value, bool):
                item_lines.append(f'    {key}: {"true" if value else "false"},')
            elif isinstance(value, (int, float)):
                item_lines.append(f'    {key}: {value},')
            elif isinstance(value, list):
                item_lines.append(f'    {key}: {json.dumps(value)},')
            elif value is None:
                item_lines.append(f'    {key}: null,')

        item_lines.append("  },")
        lines.extend(item_lines)

    lines.append("];")
    return "\n".join(lines)

def update_sec_filings(data_js_content):
    """Update SEC_FILINGS_LIVE in data.js."""
    filings = load_json("sec_filings_recent.json")
    if not filings:
        print("No SEC filings data found, skipping...")
        return data_js_content

    print(f"Merging {len(filings)} SEC filings...")

    # Generate new SEC_FILINGS_LIVE block
    js_array = "// Auto-updated SEC filings from EDGAR\n"
    js_array += f"// Last updated: {datetime.now().strftime('%Y-%m-%d')}\n"
    js_array += "const SEC_FILINGS_LIVE = [\n"

    for f in filings[:40]:
        desc = f.get("description", f.get("form", "")).replace('"', "'")
        js_array += f'  {{ company: "{f["company"]}", form: "{f["form"]}", date: "{f["date"]}", '
        js_array += f'description: "{desc}", isIPO: {"true" if f.get("isIPO") else "false"}, '
        js_array += f'ticker: "{f.get("ticker", "")}" }},\n'

    js_array += "];"

    # Replace existing SEC_FILINGS_LIVE
    pattern = r'const SEC_FILINGS_LIVE = \[[\s\S]*?\];'
    if re.search(pattern, data_js_content):
        data_js_content = re.sub(pattern, js_array, data_js_content)
        print("  Updated SEC_FILINGS_LIVE")
    else:
        print("  SEC_FILINGS_LIVE not found in data.js")

    return data_js_content

def update_company_signals(data_js_content):
    """Update COMPANY_SIGNALS in data.js with fresh news."""
    signals = load_json("news_raw.json")
    if not signals:
        print("No news signals data found, skipping...")
        return data_js_content

    print(f"Merging {len(signals)} news signals...")

    # Convert to COMPANY_SIGNALS format
    formatted_signals = []
    for i, s in enumerate(signals[:15]):
        formatted_signals.append({
            "id": i + 1,
            "type": s.get("type", "news"),
            "company": s.get("matchedCompany", ""),
            "headline": s.get("title", "")[:120].replace('"', "'"),
            "source": s.get("source", ""),
            "time": s.get("time", ""),
            "impact": s.get("impact", "medium"),
            "unread": i < 5
        })

    # Generate JS block
    js_array = "// Auto-generated real-time signals\n"
    js_array += f"// Last updated: {datetime.now().strftime('%Y-%m-%d')}\n"
    js_array += "const COMPANY_SIGNALS = [\n"

    for s in formatted_signals:
        js_array += f'  {{ id: {s["id"]}, type: "{s["type"]}", company: "{s["company"]}", '
        js_array += f'headline: "{s["headline"]}", source: "{s["source"]}", '
        js_array += f'time: "{s["time"]}", impact: "{s["impact"]}", '
        js_array += f'unread: {"true" if s["unread"] else "false"} }},\n'

    js_array += "];"

    # Replace existing COMPANY_SIGNALS
    pattern = r'const COMPANY_SIGNALS = \[[\s\S]*?\];'
    if re.search(pattern, data_js_content):
        data_js_content = re.sub(pattern, js_array, data_js_content)
        print("  Updated COMPANY_SIGNALS")
    else:
        print("  COMPANY_SIGNALS not found in data.js")

    return data_js_content

def update_last_updated(data_js_content):
    """Update the LAST_UPDATED timestamp."""
    today = datetime.now().strftime("%Y-%m-%d")
    pattern = r'const LAST_UPDATED = "[^"]+";'
    replacement = f'const LAST_UPDATED = "{today}";'

    if re.search(pattern, data_js_content):
        data_js_content = re.sub(pattern, replacement, data_js_content)
        print(f"  Updated LAST_UPDATED to {today}")

    return data_js_content

def main():
    print("=" * 60)
    print("Data Merger for The Innovators League")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Read current data.js
    if not DATA_JS_PATH.exists():
        print("ERROR: data.js not found!")
        return

    with open(DATA_JS_PATH, 'r') as f:
        data_js_content = f.read()

    original_length = len(data_js_content)

    # Apply updates
    data_js_content = update_sec_filings(data_js_content)
    data_js_content = update_company_signals(data_js_content)
    data_js_content = update_last_updated(data_js_content)

    # Write updated data.js
    with open(DATA_JS_PATH, 'w') as f:
        f.write(data_js_content)

    print("\n" + "=" * 60)
    print(f"data.js updated ({original_length} -> {len(data_js_content)} bytes)")
    print("=" * 60)

if __name__ == "__main__":
    main()
