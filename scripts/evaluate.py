"""
Evaluate pytrovich's accuracy against the petrovich-eval datasets.

This is a port of petrovich-ruby's lib/tasks/evaluate.rake — same data
files, same per-gender / per-case accuracy reporting, same error TSV
output. It is **not** a unit test: the eval datasets contain ~250k
gold-standard rows pulled from open dictionaries, and Petrovich is a
rule-based inflector that will never reach 100% on real-world data.
The script prints accuracy and (optionally) fails CI when accuracy
drops vs. a stored baseline — that's how regressions get caught
without flaking on the noisy long tail.

Usage:

    # Run everything (defaults to all parts, all subsets where present)
    python scripts/evaluate.py rules
    python scripts/evaluate.py gender

    # Just one name part
    python scripts/evaluate.py rules --namepart firstnames
    python scripts/evaluate.py gender --namepart surnames

    # Hand-curated misc subsets (small, high-signal smoke tests)
    python scripts/evaluate.py rules --namepart firstnames --subset misc

    # Custom errors-output path
    python scripts/evaluate.py rules --errors out.tsv

    # Regression mode (CI-friendly): fail if accuracy is more than the
    # specified percentage points worse than `baseline.json`.
    python scripts/evaluate.py rules --regression-against baseline.json --tolerance 0.5

The eval data lives in the petrovich-eval submodule at ./eval. If
the submodule isn't initialized, the script tells you how to fix it
and exits 0 (so it doesn't break CI on a fresh clone).
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

from pytrovich.detector import PetrovichGenderDetector
from pytrovich.enums import Case, Gender, NamePart
from pytrovich.maker import PetrovichDeclinationMaker

# Mapping from petrovich-eval grammeme tags to pytrovich enum values.
# Source: the OpenCorpora-derived TSVs use abbreviations from the
# Russian linguistic tradition: мр = мужской род (male), жр = женский
# род (female), им = именительный (nominative), рд = родительный
# (genitive), дт = дательный (dative), вн = винительный (accusative),
# тв = творительный (instrumental), пр = предложный (prepositional).
# The '0' marker means aptotic (indeclinable in all cases).
GRAMMEME_TO_CASE = {
    # NOMINATIVE is the identity transformation in pytrovich (added
    # to match petrovich-ruby's :nominative semantics). Including it
    # here picks up the ~30k 'им'-tagged eval rows that were
    # previously skipped — the checks are tautologically true for
    # any well-behaved inflector but keep the eval-suite output in
    # parity with the Ruby reference.
    "им": Case.NOMINATIVE,
    "рд": Case.GENITIVE,
    "дт": Case.DATIVE,
    "вн": Case.ACCUSATIVE,
    "тв": Case.INSTRUMENTAL,
    "пр": Case.PREPOSITIONAL,
}
GENDER_TAG_TO_GENDER = {
    "мр": Gender.MALE,
    "жр": Gender.FEMALE,
    "мр-жр": Gender.ANDROGYNOUS,
}

# Map between eval-file basenames and the NamePart enum members.
# The Ruby helper `figure_namepart` does the same fixup.
NAMEPART_FILENAMES = {
    "firstnames": NamePart.FIRSTNAME,
    "surnames": NamePart.LASTNAME,
    "midnames": NamePart.MIDDLENAME,
}

# Repo root is two levels up from this script: scripts/evaluate.py -> ../../
REPO_ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = REPO_ROOT / "eval"


def _missing_eval_dir_message() -> str:
    return (
        f"petrovich-eval submodule not found at {EVAL_DIR}. "
        f"Run `git submodule update --init --recursive` from the repo "
        f"root to fetch the evaluation datasets."
    )


def _read_tsv(path: Path):
    """Stream rows from a TSV file as dicts. petrovich-eval files
    occasionally start with a UTF-8 BOM, hence ``utf-8-sig``."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        yield from reader


def evaluate_rules(namepart_filename: str, subset: str | None, errors_path: Path):
    """
    Inflection accuracy against eval/<namepart>[.<subset>].tsv.

    Returns (correct: dict, total: dict) keyed by (gender_label,
    case_label) tuples for use by regression mode.
    """
    if namepart_filename not in NAMEPART_FILENAMES:
        raise SystemExit(
            f"Unknown namepart {namepart_filename!r}. Expected one of {sorted(NAMEPART_FILENAMES)}."
        )
    name_part = NAMEPART_FILENAMES[namepart_filename]

    # Same path-construction shape as the Ruby task:
    # eval/firstnames.tsv  or  eval/firstnames.misc.tsv
    suffix = f".{subset}" if subset else ""
    tsv_path = EVAL_DIR / f"{namepart_filename}{suffix}.tsv"
    if not tsv_path.is_file():
        print(f"File {tsv_path} not found, skipping.", file=sys.stderr)
        return {}, {}

    print(f'Evaluating inflector on "{tsv_path}", errors → "{errors_path}".')

    maker = PetrovichDeclinationMaker()
    correct = defaultdict(int)
    total = defaultdict(int)
    errors = []

    def check(lemma: str, gender: Gender, gcase: Case, expected: str):
        actual = maker.make(name_part, gender, gcase, lemma)
        # Eval data is heterogeneous: surnames.tsv etc. are ALL CAPS,
        # while firstnames.misc.tsv is Title Case. pytrovich preserves
        # input case in the output. Upcase both sides for comparison
        # so that the test compares phonemes, not stylization. The
        # Ruby task does the same with Petrovich::Unicode.upcase.
        actual_normalized = actual.upper()
        expected_normalized = expected.upper()
        key = (gender.name.lower(), gcase.name.lower())
        total[key] += 1
        if actual_normalized == expected_normalized:
            correct[key] += 1
        else:
            errors.append((lemma, expected_normalized, actual_normalized, key))

    for row in _read_tsv(tsv_path):
        lemma = row["lemma"]
        word = row["word"]
        grammemes = (row.get("grammemes") or "").split(",")

        # Gender for the inflector call, mapped exactly as petrovich-
        # ruby's evaluate.rake does: a row is inflected as MALE iff its
        # grammemes contain 'мр'; everything else — including the
        # androgynous 'мр-жр' rows this script previously skipped — is
        # inflected as FEMALE. Forcing androgynous rows through the
        # female rules is the stricter convention the Ruby reference
        # reports its accuracy under, and adopting it makes the totals
        # directly comparable (the skip silently dropped ~5k surname
        # checks).
        gender = Gender.MALE if "мр" in grammemes else Gender.FEMALE

        if "0" in grammemes:
            # Aptotic: every case must equal the lemma. The Ruby task
            # iterates Petrovich::CASES; we iterate the enum.
            for gcase in Case:
                check(lemma, gender, gcase, word)
        else:
            for tag, gcase in GRAMMEME_TO_CASE.items():
                if tag in grammemes:
                    check(lemma, gender, gcase, word)
                    break

    # Sort errors deterministically: by reversed lemma (groups
    # similar suffixes together) then by (gender, case). The Ruby
    # task does the same sort, for the same reason — when scanning
    # the errors file by hand, similar failure modes cluster.
    errors.sort(key=lambda row: (row[0][::-1], row[3]))

    with open(errors_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["lemma", "expected", "actual", "params"])
        for lemma, expected, actual, params in errors:
            w.writerow([lemma, expected, actual, ",".join(params)])

    _print_breakdown(correct, total)
    return correct, total


def evaluate_gender(namepart_filename: str, subset: str | None, errors_path: Path):
    """
    Gender-detection accuracy against eval/<namepart>[.<subset>].gender.tsv.

    Returns (correct: dict, total: dict) keyed by gender label.
    """
    if namepart_filename not in NAMEPART_FILENAMES:
        raise SystemExit(
            f"Unknown namepart {namepart_filename!r}. Expected one of {sorted(NAMEPART_FILENAMES)}."
        )
    namepart_kwarg = {
        "firstnames": "firstname",
        "surnames": "lastname",
        "midnames": "middlename",
    }[namepart_filename]

    suffix = f".{subset}" if subset else ""
    tsv_path = EVAL_DIR / f"{namepart_filename}{suffix}.gender.tsv"
    if not tsv_path.is_file():
        print(f"File {tsv_path} not found, skipping.", file=sys.stderr)
        return {}, {}

    print(f'Evaluating gender detector on "{tsv_path}", errors → "{errors_path}".')

    detector = PetrovichGenderDetector()
    correct = defaultdict(int)
    total = defaultdict(int)
    errors = []
    hard_error_count = 0

    for row in _read_tsv(tsv_path):
        lemma = row["lemma"]
        expected = GENDER_TAG_TO_GENDER.get(row["gender"])
        if expected is None:
            continue

        detected = detector.detect(**{namepart_kwarg: lemma})

        key = expected.name.lower()
        total[key] += 1
        if detected == expected:
            correct[key] += 1
        else:
            errors.append((lemma, expected.name.lower(), detected.name.lower()))
            # The Ruby task counts a "hard error" as a misdetection
            # that *isn't* simply falling back to androgynous — i.e.
            # the library confidently picked the wrong gender. Useful
            # signal: androgynous fallback is graceful; calling a
            # man's name female is not.
            if detected != Gender.ANDROGYNOUS:
                hard_error_count += 1

    print(f"Hard error count: {hard_error_count}.")

    part_index = {"female": 0, "male": 1, "androgynous": 3}
    errors.sort(key=lambda row: (row[0][::-1], part_index.get(row[1], 9)))

    with open(errors_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["lemma", "expected", "actual"])
        w.writerows(errors)

    for label in sorted(total):
        accuracy = correct[label] / total[label] * 100
        print(f"\tAc({label}) = {accuracy:.4f}%")

    correct_size = sum(correct.values())
    total_size = sum(total.values())
    if total_size:
        overall = correct_size / total_size * 100
        print(f"Well, the accuracy on {total_size} examples is about {overall:.4f}%.")
        print(
            f"Sum of the {correct_size} correct examples and "
            f"{total_size - correct_size} mistakes is {total_size}."
        )
    return correct, total


def _print_breakdown(correct: dict, total: dict) -> None:
    for key in sorted(total):
        accuracy = correct[key] / total[key] * 100
        # `key` is a tuple for rules, a string for gender. The rules
        # caller is the only one that goes through this helper.
        gender, gcase = key
        print(f"\tAc({gcase}|{gender}) = {accuracy:.4f}%")
    correct_size = sum(correct.values())
    total_size = sum(total.values())
    if total_size:
        overall = correct_size / total_size * 100
        print(f"Well, the accuracy on {total_size} examples is about {overall:.4f}%.")
        print(
            f"Sum of the {correct_size} correct examples and "
            f"{total_size - correct_size} mistakes is {total_size}."
        )


def _check_against_baseline(correct: dict, total: dict, baseline_path: Path, tolerance: float) -> int:
    """
    Compare current accuracy to a stored baseline. Returns 0 on no
    regression, 1 if any (gender, case) bucket is more than
    *tolerance* percentage points worse than baseline. Buckets that
    are absent from the baseline are tolerated (tooling for evolving
    eval sets), as are buckets that improved.
    """
    if not baseline_path.is_file():
        print(f"Baseline {baseline_path} not found — writing current numbers there.")
        _write_baseline(correct, total, baseline_path)
        return 0

    with open(baseline_path, encoding="utf-8") as f:
        baseline = json.load(f)

    failed = []
    for key, total_n in total.items():
        if total_n == 0:
            continue
        ac_now = correct[key] / total_n * 100
        # JSON keys are strings, so re-encode the tuple/string key.
        baseline_key = ":".join(key) if isinstance(key, tuple) else key
        ac_was = baseline.get(baseline_key)
        if ac_was is None:
            continue
        if ac_now < ac_was - tolerance:
            failed.append((baseline_key, ac_was, ac_now))

    if failed:
        print(f"\nRegression: {len(failed)} bucket(s) dropped more than {tolerance} pp vs baseline:")
        for key, was, now in failed:
            print(f"  {key}: {was:.4f}% → {now:.4f}%  (Δ {now - was:+.4f})")
        return 1
    print(f"\nNo regression vs baseline at tolerance {tolerance} pp.")
    return 0


def _write_baseline(correct: dict, total: dict, baseline_path: Path) -> None:
    out = {}
    for key, total_n in total.items():
        if total_n == 0:
            continue
        encoded_key = ":".join(key) if isinstance(key, tuple) else key
        out[encoded_key] = correct[key] / total_n * 100
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    with open(baseline_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, sort_keys=True, ensure_ascii=False)


def main(argv: list[str] | None = None) -> int:
    if not EVAL_DIR.is_dir() or not any(EVAL_DIR.iterdir()):
        print(_missing_eval_dir_message(), file=sys.stderr)
        return 0

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    sub = parser.add_subparsers(dest="command", required=True)

    for cmd in ("rules", "gender"):
        sp = sub.add_parser(cmd)
        sp.add_argument(
            "--namepart",
            choices=sorted(NAMEPART_FILENAMES),
            default=None,
            help="Restrict to one name part. Default: run all three.",
        )
        sp.add_argument(
            "--subset",
            default=None,
            help="Subset of the eval set: 'misc' (small, hand-curated), "
            "'popular' (firstnames only). Default: full set.",
        )
        sp.add_argument(
            "--errors",
            type=Path,
            default=None,
            help="Where to write the per-row errors TSV. "
            "Default: errors.tsv (rules) / errors.gender.tsv (gender).",
        )
        sp.add_argument(
            "--regression-against",
            type=Path,
            default=None,
            help="Compare results to a baseline JSON file; exit 1 if any "
            "bucket regresses by more than --tolerance percentage points. "
            "Bootstraps from current run if the file does not exist.",
        )
        sp.add_argument(
            "--tolerance",
            type=float,
            default=0.5,
            help="Allowed drop in any single bucket vs baseline, in percentage points. Default: 0.5.",
        )
    args = parser.parse_args(argv)

    nameparts = [args.namepart] if args.namepart else list(NAMEPART_FILENAMES)
    default_errors = Path("errors.tsv" if args.command == "rules" else "errors.gender.tsv")
    errors_path = args.errors or default_errors

    aggregate_correct: dict = defaultdict(int)
    aggregate_total: dict = defaultdict(int)
    runner = evaluate_rules if args.command == "rules" else evaluate_gender
    for namepart in nameparts:
        c, t = runner(namepart, args.subset, errors_path)
        for k, v in c.items():
            aggregate_correct[k] += v
        for k, v in t.items():
            aggregate_total[k] += v

    if args.regression_against is not None:
        return _check_against_baseline(
            aggregate_correct, aggregate_total, args.regression_against, args.tolerance
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
