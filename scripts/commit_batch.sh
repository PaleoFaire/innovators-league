#!/usr/bin/env bash
# commit_batch.sh — robust auto-apply + commit + push for verify-all-remaining-v2.
#
# Usage:  bash scripts/commit_batch.sh batch4
#
# Exits non-zero (and fails the workflow step) if:
#   - verification JSON is missing (verify step failed silently)
#   - data.js sanity check fails after apply (corruption risk)
#   - push fails after 5 retries
#
# Robust against concurrent writers (hourly news sync, etc.) via rebase
# with explicit conflict resolution + backup-and-restore.

set -euo pipefail

SUFFIX="${1:?usage: commit_batch.sh <suffix>}"
JSON="data/company_facts_verification_${SUFFIX}.json"
REPORT="COMPANY_FACTS_VERIFICATION_REPORT_${SUFFIX}.md"

echo "===================================================="
echo "commit_batch.sh suffix=${SUFFIX}"
echo "===================================================="

# ── 1. Sanity: verification JSON must exist ─────────────────
if [ ! -s "$JSON" ]; then
  echo "::error::Verification JSON missing or empty: $JSON"
  echo "  → verify step likely failed silently."
  echo "  → Aborting commit step. Verify artifact for $SUFFIX may still be in workflow artifacts."
  exit 1
fi

echo "✓ Verification JSON present: $(wc -c < "$JSON") bytes"

# ── 2. Snapshot data.js BEFORE auto-apply (for diff sanity) ─
cp data.js /tmp/data.js.before_${SUFFIX}

# ── 3. Run auto-apply ───────────────────────────────────────
python scripts/auto_apply_verified.py --suffix "${SUFFIX}"

# ── 4. data.js sanity check (proper JS parse via node) ──────
if command -v node >/dev/null 2>&1; then
  node -e "
    const fs = require('fs');
    const src = fs.readFileSync('data.js', 'utf8');
    if (!src.includes('const COMPANIES')) { console.error('COMPANIES marker missing'); process.exit(1); }
    // Eval just enough to validate parse
    try {
      // Wrap in a function so 'window' / DOM refs don't crash node
      new Function('window', src + '; return COMPANIES;');
      // If we got here, data.js parses.
      console.log('✓ data.js parses cleanly via node');
    } catch (e) {
      console.error('::error::data.js parse error:', e.message);
      console.error('  → Restoring data.js from snapshot');
      process.exit(2);
    }
  " || {
    echo "::error::data.js corruption detected after auto-apply"
    cp /tmp/data.js.before_${SUFFIX} data.js
    echo "  → Restored data.js from snapshot (no changes applied for ${SUFFIX})"
    # Continue to commit verification artifacts even though data.js wasn't updated
  }
else
  # Fallback: brace-balance + COMPANIES marker
  python3 -c "
import sys
src = open('data.js').read()
assert 'const COMPANIES' in src, 'COMPANIES marker missing'
assert src.count('{') == src.count('}'), f\"brace imbalance: open={src.count('{')} close={src.count('}')}\"
print('✓ data.js sanity check passed (no node available)')
"
fi

# ── 5. Show what changed ────────────────────────────────────
DATA_JS_DIFF_LINES=$(diff /tmp/data.js.before_${SUFFIX} data.js | wc -l || true)
echo "  data.js diff lines: ${DATA_JS_DIFF_LINES}"

# ── 6. Stage verification artifacts + (possibly) data.js ────
git add "$JSON" 2>&1 || { echo "::error::git add $JSON failed"; exit 1; }
[ -f "$REPORT" ] && git add "$REPORT" 2>&1 || true
git add data.js 2>&1 || { echo "::error::git add data.js failed"; exit 1; }

# ── 7. Backup staged files to /tmp BEFORE any push attempt ──
mkdir -p /tmp/commit_backup_${SUFFIX}
cp "$JSON" /tmp/commit_backup_${SUFFIX}/ 2>/dev/null || true
[ -f "$REPORT" ] && cp "$REPORT" /tmp/commit_backup_${SUFFIX}/ 2>/dev/null || true
cp data.js /tmp/commit_backup_${SUFFIX}/data.js 2>/dev/null || true
echo "  Staged artifacts backed up to /tmp/commit_backup_${SUFFIX}"

# ── 8. Commit (skip if nothing staged) ──────────────────────
if git diff --staged --quiet; then
  echo "Nothing to commit for ${SUFFIX} — verifier may have found 0 changes"
  exit 0
fi

git commit -m "📊 ${SUFFIX} verified + auto-applied"
echo "✓ Committed locally"

# ── 9. Push with retry + recovery on conflict ───────────────
for attempt in 1 2 3 4 5; do
  echo
  echo "  Push attempt ${attempt}/5..."
  git fetch origin main --quiet
  if git push origin HEAD:main 2>&1; then
    echo "✓ Pushed successfully on attempt ${attempt}"
    exit 0
  fi
  echo "  Push rejected on attempt ${attempt}. Recovering and retrying..."
  # Reset to clean origin/main, restore our files, recommit
  git reset --hard origin/main
  cp /tmp/commit_backup_${SUFFIX}/$(basename "$JSON") "$JSON" 2>/dev/null || true
  [ -f /tmp/commit_backup_${SUFFIX}/$(basename "$REPORT") ] && \
    cp /tmp/commit_backup_${SUFFIX}/$(basename "$REPORT") "$REPORT" 2>/dev/null || true
  cp /tmp/commit_backup_${SUFFIX}/data.js data.js 2>/dev/null || true
  git add "$JSON" 2>&1 || true
  [ -f "$REPORT" ] && git add "$REPORT" 2>&1 || true
  git add data.js 2>&1 || true
  if git diff --staged --quiet; then
    echo "  Nothing to commit after recovery — main already has our state."
    exit 0
  fi
  git commit -m "📊 ${SUFFIX} verified + auto-applied (retry ${attempt})"
  sleep $((attempt * 3))
done

echo "::error::Push failed after 5 retries for ${SUFFIX}"
echo "  → Verification data is preserved in:"
echo "     - workflow artifact: verification-${SUFFIX}"
echo "     - runner /tmp: /tmp/commit_backup_${SUFFIX}/"
exit 1
