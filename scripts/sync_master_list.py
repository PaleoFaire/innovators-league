#!/usr/bin/env python3
"""Keep scripts/company_master_list.js in step with COMPANIES in data.js.

    python3 scripts/sync_master_list.py            # add every missing company
    python3 scripts/sync_master_list.py --dry      # print the lines it would add
    python3 scripts/sync_master_list.py --check    # report only; exit 1 if any are missing
    python3 scripts/sync_master_list.py --stems    # also add the suffix-less names it suggests

The master list is what the news, jobs and deal matchers know about
(aggregate_news.js, fetch_jobs.py, fetch_deals.py, fetch_funding_rss.py and
the signal fetchers). Companies were added to data.js without it, so by
7 Oct 2026 it held 675 entries against 1,180 companies and 619 of them,
xLight, Arxlight and American Terawatt among them, could never be credited
with a deal.

New lines get only safe aliases:
  - the CamelCase join of a multi-word name ("AmericanTerawatt");
  - former names from data.js (formerNames, or "(formerly X)" in the name);
  - with --stems, the name without its corporate suffix ("Alsym Energy" ->
    "Alsym"). Without it these are only printed: a stem is a name other
    companies share more often than a full name is ("Oligo Space" ->
    "Oligo" would take Oligo Security's rounds), so read the list first.
Former names and stems must not be an ordinary word or a proper noun in the
system dictionary, a generic term, under five letters, or the name of
another company. Existing lines are never rewritten (their aliases are
hand-written), except that a line still carrying a company's former name is
renamed to the data.js name with the old name kept as an alias. Companies in
data/cut_companies_archive.json or in fetch_curated_lists.EXCLUDE are never
added.

A new one-word name that is also an ordinary word is printed for review: if
headlines use it as a word ("Union", "Span"), add it to common_word_names in
data/name_collisions.json, which makes the deal matcher accept it only where
a name stands. The dictionary is /usr/share/dict/words; without it every new
one-word name is printed and no one-word alias is made.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fetch_curated_lists import EXCLUDE  # noqa: E402
from fetch_deals import GENERIC_WORDS, _CORP_SUFFIX, _db_key, _squash  # noqa: E402
from validate_data_quality import company_objects, gv  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA_JS = ROOT / "data.js"
MASTER = ROOT / "scripts" / "company_master_list.js"
ARCHIVE = ROOT / "data" / "cut_companies_archive.json"
COLLISIONS = ROOT / "data" / "name_collisions.json"
DICT = Path("/usr/share/dict/words")

# data.js sector -> master-list sector, by what the existing lines use most.
SECTOR = {
    "Space & Aerospace": "space", "Supersonic & Hypersonic": "space",
    "Robotics & Manufacturing": "robotics", "Defense & Security": "defense",
    "Climate & Energy": "climate", "Nuclear Energy": "nuclear",
    "Biotech & Health": "biotech", "Chips & Semiconductors": "chips",
    "Quantum Computing": "quantum", "Drones & Autonomous": "autonomous",
    "Transportation": "transportation", "AI & Software": "ai",
    "Housing & Construction": "construction", "Ocean & Maritime": "ocean",
    "Infrastructure & Logistics": "infrastructure", "Consumer Tech": "consumer",
}
SUBSECTOR = {("Robotics & Manufacturing", "Advanced Manufacturing"): "manufacturing"}

LINE = re.compile(r'^(\s*\{\s*name:\s*)"([^"]+)"(,\s*aliases:\s*\[)([^\]]*)(\].*)$')


def load_words():
    """(common words, every entry) from the system dictionary, lower-cased; (None, None) without one.

    Its lower-case entries are ordinary words ("union", "span"); the rest are
    proper nouns ("Titan", "Corvus"), which are just as poor as aliases."""
    if not DICT.exists():
        return None, None
    raw = [w.strip() for w in DICT.read_text(errors="ignore").splitlines() if w.strip()]
    return {w for w in raw if w[:1].islower()}, {w.lower() for w in raw}


def in_dict(word, words):
    """True when `word`, or its singular, is in `words`; True for everything without a dictionary."""
    w = word.lower()
    if words is None:
        return True
    return w in words or (w.endswith("s") and w[:-1] in words) or (w.endswith("es") and w[:-2] in words)


def js(s):
    return json.dumps(s, ensure_ascii=False)


def plain(name):
    """The name a headline would use: 'T1 Energy (formerly FREYR Battery)' -> 'T1 Energy'."""
    return re.sub(r"\s*\([^)]*\)", "", name).strip()


def core(name):
    """'Divergent Technologies' -> 'Divergent'; 'The Nuclear Company' -> 'Nuclear'."""
    words = plain(name).split()
    if words and words[0].lower() == "the":
        words = words[1:]
    while len(words) > 1 and re.sub(r"[^a-z]", "", words[-1].lower()) in _CORP_SUFFIX:
        words.pop()
    return " ".join(words)


def ticker(raw):
    """'NASDAQ: LUNR' -> 'LUNR'; '9348.T' stays as written."""
    t = (raw or "").split(":")[-1].strip()
    return t or None


def load_companies():
    out = []
    for o in company_objects(DATA_JS.read_text(encoding="utf-8")):
        name = gv(o, "name")
        if not name:
            continue
        try:
            former = json.loads(gv(o, "formerNames") or "[]")
        except ValueError:
            former = []
        former += re.findall(r"\(formerly ([^)]+)\)", name)
        out.append({"name": name, "sector": gv(o, "sector") or "", "subsector": gv(o, "subsector") or "",
                    "ticker": gv(o, "ticker"),
                    "former": [f for f in former if isinstance(f, str) and _squash(f) != _squash(name)]})
    return out


def parse_master(text):
    """[(line index, name, [aliases])] for every entry line of MASTER_COMPANY_LIST."""
    lines = text.split("\n")
    out = []
    for i, line in enumerate(lines):
        m = LINE.match(line)
        if m:
            out.append((i, m.group(2), re.findall(r'"([^"]+)"', m.group(4))))
    return lines, out


def plan(companies, entries, common, every, stems):
    """(renames, new lines, suggested stems, names to review) for the companies the list lacks."""
    covered = {_db_key(n) for _, n, _ in entries}
    cut = set(EXCLUDE)
    if ARCHIVE.exists():
        cut |= {_squash(c["name"]) for c in json.loads(ARCHIVE.read_text(encoding="utf-8"))["companies"]}

    # Every spelling already spoken for, by company: a new alias must not be one of them.
    owner = {}
    for _, n, aliases in entries:
        for s in [n, core(n)] + aliases:
            owner.setdefault(_squash(s), set()).add(_db_key(n))
    for c in companies:
        for s in (c["name"], plain(c["name"]), core(c["name"])):
            owner.setdefault(_squash(s), set()).add(_db_key(c["name"]))

    renames, new, suggested, review = {}, [], [], []
    by_name = {_db_key(n): (i, n, aliases) for i, n, aliases in entries}
    for c in companies:
        key = _db_key(c["name"])
        if key in covered or key in cut or _squash(c["name"]) in cut:
            continue
        # A line still under the company's former name: rename it, keep the old name.
        old = next((by_name[_db_key(f)] for f in c["former"] if _db_key(f) in by_name), None)
        if old and old[0] not in renames:
            i, oldname, aliases = old
            renames[i] = (plain(c["name"]), [oldname] + [a for a in aliases if _squash(a) != _squash(oldname)])
            covered.add(key)
            continue

        name = plain(c["name"])

        def safe(alias):
            k = _squash(alias)
            if len(k) < 5 or alias.lower() in GENERIC_WORDS or k == _squash(name):
                return False
            if owner.get(k, set()) - {key}:
                return False                       # another company's name or alias
            words = re.sub(r"[^A-Za-z0-9 ]", " ", alias).split()
            if len(words) == 1:
                return alias[:1].isupper() and not in_dict(alias, every)
            return any(not in_dict(w, every) for w in words)      # "Noble Gas" is a phrase

        aliases = []
        parts = re.sub(r"[^A-Za-z0-9 ]", " ", name).split()
        if len(parts) > 1:
            aliases.append("".join(p[:1].upper() + p[1:] for p in parts))
        aliases += [f for f in c["former"] if safe(f)]
        stem = core(c["name"])
        if stem != name and safe(stem):
            if stems:
                aliases.append(stem)
            else:
                suggested.append(f"{stem}  (for {name})")
        aliases = [a for i2, a in enumerate(aliases) if a not in aliases[:i2]]
        sector = SUBSECTOR.get((c["sector"], c["subsector"])) or SECTOR.get(c["sector"], "other")
        t = ticker(c["ticker"])
        new.append((sector, name, f'  {{ name: {js(name)}, aliases: [{", ".join(js(a) for a in aliases)}], '
                                  f'sector: {js(sector)}, ticker: {js(t) if t else "null"} }},'))
        for a in aliases:
            owner.setdefault(_squash(a), set()).add(key)
        if " " not in name and in_dict(name, common):
            review.append(name)
    return renames, sorted(new), suggested, review


def write(text, lines, renames, new, total):
    for i, (name, aliases) in renames.items():
        m = LINE.match(lines[i])
        lines[i] = f'{m.group(1)}{js(name)}{m.group(3)}{", ".join(js(a) for a in aliases)}{m.group(5)}'
    text = "\n".join(lines)
    if new:
        close = text.index("\n];", text.index("const MASTER_COMPANY_LIST = ["))
        block = (f"\n  // ─── {date.today():%d %b %Y} sync: data.js companies the list lacked "
                 f"(scripts/sync_master_list.py) ───\n" + "\n".join(line for _, _, line in new))
        text = text[:close] + block + text[close:]
    text = re.sub(r"Total companies: \d+", f"Total companies: {total}", text, count=1)
    text = re.sub(r"Last updated: [\d-]+", f"Last updated: {date.today().isoformat()}", text, count=1)
    MASTER.write_text(text, encoding="utf-8")


def main():
    dry, check, stems = "--dry" in sys.argv, "--check" in sys.argv, "--stems" in sys.argv
    common, every = load_words()
    companies = load_companies()
    text = MASTER.read_text(encoding="utf-8")
    lines, entries = parse_master(text)
    renames, new, suggested, review = plan(companies, entries, common, every, stems)
    missing = len(new) + len(renames)
    print(f"data.js companies: {len(companies)}; master-list lines: {len(entries)}; "
          f"missing: {missing} ({len(new)} new lines, {len(renames)} renamed former names)")
    if check:
        for _, name, _ in new:
            print(f"  missing: {name}")
        return 1 if missing else 0
    for i, (name, aliases) in renames.items():
        print(f"  rename: {LINE.match(lines[i]).group(2)} -> {name} (old name kept as alias)")
    if dry:
        for _, _, line in new:
            print(line)
    else:
        write(text, lines, renames, new, len(entries) + len(new))
        print(f"Wrote {MASTER.relative_to(ROOT)}")
    if suggested:
        print(f"\nSuffix-less names not added ({len(suggested)}). Add by hand, or rerun with --stems, "
              f"only those no other company goes by:\n  " + "\n  ".join(suggested))
    if review:
        print(f"\nOne-word names that are also ordinary words ({len(review)}). Add any that headlines "
              f"use as words to common_word_names in data/name_collisions.json:\n  " + ", ".join(review))
    return 0


if __name__ == "__main__":
    sys.exit(main())
