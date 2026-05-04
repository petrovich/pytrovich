#!/usr/bin/env python3
"""
scripts/trim_benchmark_json.py — shrink a pytest-benchmark JSON file for
artifact storage by dropping per-sample timing data.

pytest-benchmark records every individual iteration's wall-clock time in
the `stats.data` field. For benchmarks that run hundreds of thousands of
iterations this balloons the JSON to many megabytes, while every value
that's useful for comparison (min, mean, median, max, stddev, the
quartiles, and the iqr-outlier counts) is already pre-aggregated and
stays after the strip.

Usage:
    python scripts/trim_benchmark_json.py benchmark.json
"""
import json
import os
import sys


def trim(path: str) -> None:
    with open(path) as f:
        data = json.load(f)

    before = os.path.getsize(path)
    for bench in data.get('benchmarks', []):
        bench.get('stats', {}).pop('data', None)

    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

    after = os.path.getsize(path)
    print(
        f"Trimmed {path}: {before:,} -> {after:,} bytes "
        f"({(1 - after / before) * 100:.2f}% smaller)"
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: trim_benchmark_json.py <path-to-benchmark.json>")
    trim(sys.argv[1])
