#!/bin/bash
# Hourly FunPay job: snapshot (retry once) -> rebuild site -> publish if changed. Exits non-zero on failure.
set -o pipefail
cd /workspace/plati_monitor/funpay || exit 1
exec 7>/tmp/funpay_hourly.lock; flock -n 7 || { echo "another funpay run in progress" >&2; exit 3; }
python3 funpay_snapshot.py || { echo "funpay fetch failed, retrying in 20s" >&2; sleep 20; python3 funpay_snapshot.py; } || { echo "FUNPAY SNAPSHOT FAILED" >&2; exit 2; }
cd /workspace/plati_monitor && ./publish.sh "funpay update $(TZ=Asia/Shanghai date '+%Y-%m-%d %H:%M')" || { echo "PUBLISH FAILED" >&2; exit 4; }
echo "funpay run OK"
