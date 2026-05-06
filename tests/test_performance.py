"""
Performance benchmarks for pytrovich.

These tests use pytest-benchmark and were originally targeted at the
inefficiencies flagged in code review. Most have since been resolved
in master:

  * Linear suffix scan in the maker / detector — replaced by the
    SuffixTrie introduced on the faster-lookup branch (3-5x speedup;
    see pytrovich/suffix_trie.py).
  * Character-by-character loop in apply_mod2name — simplified to
    `name[:-n] + suffix` form.
  * JSON parsing on every constructor invocation — now cached at
    module level by rules-file path, so repeated construction is
    effectively free.

Benchmarks are tagged with `@pytest.mark.benchmark` so they can be
selected/deselected at the command line:

    pytest -m benchmark              # run only benchmarks
    pytest -m "not benchmark"        # run everything except benchmarks
    pytest                           # runs everything (default)

The scripts in `scripts/` use the explicit selectors so coverage runs
exclude benchmarks and benchmark runs exclude unit tests.
"""

import pytest

from pytrovich.detector import PetrovichGenderDetector
from pytrovich.enums import Case, Gender, NamePart
from pytrovich.maker import PetrovichDeclinationMaker

# Skip the entire module if the pytest-benchmark plugin is not installed.
pytest.importorskip("pytest_benchmark")

pytestmark = pytest.mark.benchmark

# A representative workload: a mix of name parts, genders, cases, and
# endings that exercise different rule branches (suffix-matched, exception
# list, indeclinable). Designed to be more realistic than benchmarking a
# single name in a hot loop.
SAMPLE_WORKLOAD = [
    (NamePart.FIRSTNAME, Gender.MALE, Case.GENITIVE, "Иван"),
    (NamePart.FIRSTNAME, Gender.MALE, Case.DATIVE, "Василий"),
    (NamePart.FIRSTNAME, Gender.FEMALE, Case.ACCUSATIVE, "Ксюша"),
    (NamePart.FIRSTNAME, Gender.FEMALE, Case.PREPOSITIONAL, "Елена"),
    (NamePart.FIRSTNAME, Gender.MALE, Case.INSTRUMENTAL, "Александр"),
    (NamePart.MIDDLENAME, Gender.FEMALE, Case.GENITIVE, "Геннадиевна"),
    (NamePart.MIDDLENAME, Gender.MALE, Case.DATIVE, "Васильевич"),
    (NamePart.MIDDLENAME, Gender.MALE, Case.INSTRUMENTAL, "Павлович"),
    (NamePart.LASTNAME, Gender.FEMALE, Case.GENITIVE, "Цветаева"),
    (NamePart.LASTNAME, Gender.MALE, Case.DATIVE, "Толстой"),
    (NamePart.LASTNAME, Gender.MALE, Case.INSTRUMENTAL, "Лермонтов"),
    (NamePart.LASTNAME, Gender.FEMALE, Case.PREPOSITIONAL, "Баркова"),
]


@pytest.fixture(scope="module")
def maker() -> PetrovichDeclinationMaker:
    return PetrovichDeclinationMaker()


@pytest.fixture(scope="module")
def detector() -> PetrovichGenderDetector:
    return PetrovichGenderDetector()


class TestMakerPerformance:
    """Per-call latency and throughput for PetrovichDeclinationMaker."""

    def test_make_single_call(self, benchmark, maker):
        # Measures the per-call cost for one common short name.
        result = benchmark(
            maker.make,
            NamePart.FIRSTNAME,
            Gender.MALE,
            Case.GENITIVE,
            "Иван",
        )
        assert result == "Ивана"

    def test_make_long_lastname(self, benchmark, maker):
        # Longer string + likely deeper rule traversal.
        result = benchmark(
            maker.make,
            NamePart.LASTNAME,
            Gender.FEMALE,
            Case.INSTRUMENTAL,
            "Тургенева-Достоевская",
        )
        assert isinstance(result, str)

    def test_make_mixed_workload(self, benchmark, maker):
        # Realistic mix; this is the headline number for "how fast can we
        # inflect names in production?"
        def workload():
            for name_part, gender, case_to_use, name in SAMPLE_WORKLOAD:
                maker.make(name_part, gender, case_to_use, name)

        benchmark(workload)


class TestDetectorPerformance:
    """Per-call latency and throughput for PetrovichGenderDetector."""

    def test_detect_by_firstname(self, benchmark, detector):
        result = benchmark(detector.detect, "Иван")
        # detector.detect's first positional is firstname; lock it.
        assert result == Gender.MALE

    def test_detect_by_full_triplet(self, benchmark, detector):
        # Exercises all three name parts — the detector iterates over
        # exception sets and suffix lists for each part, so this is the
        # worst case in detector.detect's call graph.
        result = benchmark(
            detector.detect,
            "Иван",
            "Иванов",
            "Семёнович",
        )
        assert result == Gender.MALE

    def test_detect_mixed_workload(self, benchmark, detector):
        names = [
            ("Иван", None, "Семёнович"),
            ("Мария", "Цветаева", "Ивановна"),
            ("Василий", "Лермонтов", None),
            ("Анна", "Ахматова", "Андреевна"),
            ("Алексей", "Толстой", "Николаевич"),
            ("Арзу", None, "Лутфияр кызы"),
        ]

        def workload():
            for fn, ln, mn in names:
                detector.detect(firstname=fn, lastname=ln, middlename=mn)

        benchmark(workload)


class TestConstructorPerformance:
    """
    Constructor cost — directly measures the JSON parse-on-every-init
    behavior flagged in review. A meaningful improvement here (caching at
    module level) should shrink this benchmark by an order of magnitude.
    """

    def test_maker_constructor(self, benchmark):
        # Each call re-reads and re-parses pytrovich/petrovich-rules/rules.json.
        benchmark(PetrovichDeclinationMaker)

    def test_detector_constructor(self, benchmark):
        # Each call re-reads and re-parses pytrovich/petrovich-rules/gender.json.
        benchmark(PetrovichGenderDetector)
