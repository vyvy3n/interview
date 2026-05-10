#!/usr/bin/env bash
# ./test.sh N → run all TestStepN tests via pytest.
# ./test.sh    → run every step.
set -euo pipefail
cd "$(dirname "$0")"
if [[ $# -eq 0 ]]; then
    pytest tests/test_dns.py -v
else
    pytest tests/test_dns.py -v -k "TestStep$1"
fi
