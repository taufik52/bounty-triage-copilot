#!/bin/bash
# End-to-end smoke test for Bounty Triage Copilot.
# Starts the app on port 18080, exercises every endpoint, then stops it.
# Usage: bash test_e2e.sh
set -u
cd "$(dirname "$0")"
PORT=18080
BASE="http://127.0.0.1:$PORT"
PASS=0; FAIL=0

ok()   { echo "PASS: $1"; PASS=$((PASS+1)); }
bad()  { echo "FAIL: $1"; FAIL=$((FAIL+1)); }

python3 app.py --port $PORT > /tmp/arbiter-e2e.log 2>&1 &
PID=$!
trap 'kill $PID 2>/dev/null' EXIT
sleep 2

# 1. Home page
if curl -s -m 10 "$BASE/" | grep -q "Bounty Triage Copilot"; then ok "GET / serves UI"; else bad "GET / serves UI"; fi

# 2. Static assets
if curl -s -o /dev/null -w "%{http_code}" -m 10 "$BASE/static/app.js" | grep -q 200; then ok "GET /static/app.js 200"; else bad "GET /static/app.js 200"; fi
if curl -s -o /dev/null -w "%{http_code}" -m 10 "$BASE/static/style.css" | grep -q 200; then ok "GET /static/style.css 200"; else bad "GET /static/style.css 200"; fi

# 3. Health
HEALTH=$(curl -s -m 10 "$BASE/api/health")
echo "$HEALTH" | grep -q '"status": "ok"' && ok "GET /api/health ok" || bad "GET /api/health ok"

# 4. Samples
if curl -s -m 10 "$BASE/api/samples" | grep -q '"id": "strong"'; then ok "GET /api/samples has strong+weak"; else bad "GET /api/samples"; fi

# 5. Triage — strong draft (from samples.py via python to avoid shell quoting)
python3 - "$BASE" <<'EOF'
import json, sys, urllib.request
from samples import SAMPLES
base = sys.argv[1]
for sample in SAMPLES:
    req = urllib.request.Request(
        f"{base}/api/triage",
        data=json.dumps({"title": sample["title"], "program": sample["program"], "draft": sample["draft"]}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        res = json.load(r)
    print(f"{sample['id']}: total={res['total']} grade={res['grade']} verdict={res['verdict']} "
          f"suggestions={len(res['suggestions'])} dup_hits={len(res['duplicate_screen'])}")
    assert 0 <= res["total"] <= 100, "total out of range"
    assert res["total"] == sum(d["score"] for d in res["dimensions"].values()), "total != sum"
print("TRIAGE_ASSERTS_OK")
EOF
[ $? -eq 0 ] && ok "POST /api/triage strong+weak (asserts pass)" || bad "POST /api/triage strong+weak"

# 6. Triage — empty draft rejected
CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 10 -X POST "$BASE/api/triage" -H "Content-Type: application/json" -d '{"title":"x","draft":""}')
[ "$CODE" = "400" ] && ok "POST /api/triage empty draft -> 400" || bad "POST /api/triage empty draft -> 400 (got $CODE)"

# 7. Unknown route
CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 10 "$BASE/nope")
[ "$CODE" = "404" ] && ok "GET /nope -> 404" || bad "GET /nope -> 404 (got $CODE)"

# 8. Response time of rules scoring (must be fast — LLM is never on this path)
T=$(curl -s -o /dev/null -w "%{time_total}" -m 10 -X POST "$BASE/api/triage" -H "Content-Type: application/json" -d '{"title":"t","program":"p","draft":"Severity: High. Funds can be drained. Steps: 1. Do x. 2. Do y."}')
echo "rules scoring latency: ${T}s"
python3 -c "exit(0 if float('$T') < 2 else 1)" && ok "rules scoring < 2s (${T}s)" || bad "rules scoring < 2s (${T}s)"

echo "----------------------------------------"
echo "E2E: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
