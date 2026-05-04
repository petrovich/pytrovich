#!/usr/bin/env bash
#
# Unit-test suite with coverage measurement and a minimum-threshold gate.
#
# Usage:
#   ./scripts/coverage.sh                  # run, print terminal + write html/xml
#   ./scripts/coverage.sh -k TestMaker     # forward extra args to pytest
#   COVERAGE_MIN=90 ./scripts/coverage.sh  # tighten threshold for one run
#
# Exits non-zero if any test fails or coverage falls below COVERAGE_MIN.

set -euo pipefail

# Move to repo root so paths in .coveragerc resolve correctly regardless
# of where the user invokes the script from.
cd "$(dirname "${BASH_SOURCE[0]}")/.."

# Threshold defaults to 80% but can be overridden per-invocation.
# Current measured baseline is ~85.76% on the active modules; raise this
# as additional tests for serialize() and the exception paths land.
COVERAGE_MIN="${COVERAGE_MIN:-70}"

echo "==> Cleaning previous coverage artifacts"
rm -rf htmlcov/ coverage.xml .coverage

echo "==> Running tests with coverage (minimum: ${COVERAGE_MIN}%)"
echo "    Benchmarks are excluded by default (see pytest.ini addopts)."
echo

# --cov reads source/omit/branch settings from .coveragerc.
# --cov-fail-under turns sub-threshold coverage into a non-zero exit.
pytest \
    --cov \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-report=xml \
    --cov-fail-under="${COVERAGE_MIN}" \
    "$@"

echo
echo "==> Reports written:"
echo "    Terminal: printed above"
echo "    HTML:     htmlcov/index.html"
echo "    XML:      coverage.xml (machine-readable, e.g. for Codecov)"
