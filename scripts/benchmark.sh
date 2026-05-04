#!/usr/bin/env bash
#
# Performance benchmarks
#
# Usage:
#   ./scripts/benchmark.sh
#   ./scripts/benchmark.sh --benchmark-save=baseline
#   ./scripts/benchmark.sh --benchmark-compare=0001
#
# The default invocation prints min/mean/median/max/stddev/ops sorted by
# mean. To compare two runs:
#
#   ./scripts/benchmark.sh --benchmark-save=before
#   # ...make changes...
#   ./scripts/benchmark.sh --benchmark-compare=before

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

# -m benchmark selects only the performance tests (other tests register
# with -m "not benchmark" via pytest.ini addopts; the explicit -m here
# overrides). --override-ini lets us bypass the addopts default cleanly.
pytest \
    --override-ini="addopts=" \
    -m benchmark \
    --benchmark-columns=min,mean,median,max,stddev,ops \
    --benchmark-sort=mean \
    --benchmark-warmup=on \
    "$@"
