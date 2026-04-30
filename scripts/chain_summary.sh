#!/usr/bin/env bash
# chain_summary.sh — print verification-chain summary
# Usage: bash scripts/chain_summary.sh 4 5 6 7 8 9

set +e

echo "==============================================="
echo "VERIFICATION CHAIN COMPLETE"
echo "==============================================="

for b in "$@"; do
  f="data/company_facts_verification_batch${b}.json"
  if [ -f "$f" ]; then
    echo
    echo "Batch $b:"
    python3 - <<PY
import json
try:
    d = json.load(open('$f'))
    s = d.get('summary',{})
    print(f"  cohort: {d.get('cohortSize',0)}")
    print(f"  cleared: {s.get('cleared',0)}")
    print(f"  changes: {s.get('changesProposed',0)}")
    print(f"  unverifiable: {s.get('unverifiable',0)}")
    print(f"  cost: ~\${d.get('newExtractionsThisRun',0)*0.05:.2f}")
except Exception as e:
    print(f"  ERROR reading $f: {e}")
PY
  else
    echo "Batch $b: did not complete — check workflow artifacts"
  fi
done

echo
echo "==============================================="
echo "Latest commits on origin/main:"
git fetch origin main --quiet 2>/dev/null || true
git log origin/main --oneline -10
