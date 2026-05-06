import pytest

from pytrovich.detector import PetrovichGenderDetector
from pytrovich.enums import Gender


@pytest.fixture(scope="session")
def gender_detector():
    return PetrovichGenderDetector()


class TestPetrovichGenderDetector:
    @pytest.mark.parametrize(
        "middlename,expected_gender",
        (
            ("Иванович", Gender.MALE),
            ("Ильинична", Gender.FEMALE),
            ("Блаблабла", Gender.ANDROGYNOUS),
        ),
    )
    def test_detect_by_middlename(self, gender_detector, middlename, expected_gender):
        assert gender_detector.detect(middlename=middlename) == expected_gender


class TestPetrovichGenderDetectorCoverage:
    """
    Adds coverage for code paths in PetrovichGenderDetector.detect not
    exercised by the original middlename-only test: detection by firstname
    only, by lastname only, by combinations, and the foreign-patronymic
    exception path.
    """

    @pytest.mark.parametrize(
        "firstname,expected",
        (
            ("Иван", Gender.MALE),
            ("Алексей", Gender.MALE),
            ("Мария", Gender.FEMALE),
            ("Елена", Gender.FEMALE),
        ),
    )
    def test_detect_by_firstname(self, gender_detector, firstname, expected):
        assert gender_detector.detect(firstname=firstname) == expected

    @pytest.mark.parametrize(
        "lastname,expected",
        (
            ("Голубцов", Gender.MALE),
            ("Лермонтов", Gender.MALE),
            ("Цветаева", Gender.FEMALE),
            ("Ахматова", Gender.FEMALE),
        ),
    )
    def test_detect_by_lastname(self, gender_detector, lastname, expected):
        assert gender_detector.detect(lastname=lastname) == expected

    @pytest.mark.parametrize(
        "firstname,middlename,expected",
        (
            ("Иван", "Семёнович", Gender.MALE),
            ("Анна", "Петровна", Gender.FEMALE),
            # Azerbaijani patronymics: 'кызы' = daughter (female),
            # 'оглы' = son (male). These exercise the suffix-detection path on
            # middlenames where the firstname alone is foreign/androgynous.
            ("Арзу", "Лутфияр кызы", Gender.FEMALE),
            ("Рамиз", "Рустам оглы", Gender.MALE),
        ),
    )
    def test_detect_by_firstname_and_middlename(
        self,
        gender_detector,
        firstname,
        middlename,
        expected,
    ):
        assert (
            gender_detector.detect(
                firstname=firstname,
                middlename=middlename,
            )
            == expected
        )

    def test_detect_combined_firstname_and_lastname(self, gender_detector):
        # Both parts agree on MALE.
        assert (
            gender_detector.detect(
                firstname="Иван",
                lastname="Голубцов",
            )
            == Gender.MALE
        )


class TestPetrovichGenderDetectorKnownIssues:
    """
    Each test here pins down a defect identified during code review.
    Marked xfail(strict=True): a fix will turn them XPASS and the
    suite red. Do NOT delete these tests on fix — convert them to
    plain assertions.
    """

    @pytest.mark.parametrize(
        "firstname",
        [
            "Саша",  # legitimate Russian androgynous diminutive
            "Блаблабла",  # nonsense input
            "",  # empty string — bypasses the None-only assert
        ],
    )
    def test_unknown_firstname_returns_androgynous(self, gender_detector, firstname):
        # Regression test for Issue #6. detect() used to call
        # next(iter(joined_set)) on a possibly-empty set, raising
        # StopIteration when no rule matched. The fix returns
        # Gender.ANDROGYNOUS in that case, matching the canonical Ruby
        # contract (Petrovich.detect_gender('блаблабла') => :androgynous).
        assert gender_detector.detect(firstname=firstname) == Gender.ANDROGYNOUS

    def test_no_arguments_raises_value_error(self, gender_detector):
        # Pre-fix this used `assert` for validation, which `python -O`
        # would strip and let downstream AttributeError on a None Name
        # surface to callers. Now raises ValueError unconditionally.
        with pytest.raises(ValueError, match="at least one of"):
            gender_detector.detect()


class TestPetrovichGenderDetectorCaseNormalization:
    """
    The rules data uses lowercase Cyrillic throughout (exception lists
    and suffix tests). Without case normalization, inputs with capital
    letters miss exception entries (`'Савва' in {'савва'}` is False)
    and uppercase suffix endings fail str.endswith('ов') against 'ОВ'.
    The Ruby reference rolls a custom Cyrillic downcase
    (lib/petrovich/unicode.rb) for this same reason.
    """

    @pytest.mark.parametrize(
        "firstname,expected",
        [
            # 'савва' is in firstname.exceptions.male; without
            # case-normalization this StopIteration'd before Issue #6
            # was fixed, and after Issue #6 was fixed it would have
            # silently returned ANDROGYNOUS via the no-match path.
            ("Савва", Gender.MALE),
            ("САВВА", Gender.MALE),
            ("сАвВа", Gender.MALE),
            # 'любава' is in firstname.exceptions.female.
            ("Любава", Gender.FEMALE),
            ("ЛЮБАВА", Gender.FEMALE),
        ],
    )
    def test_capitalized_firstname_exception_matches(self, gender_detector, firstname, expected):
        assert gender_detector.detect(firstname=firstname) == expected

    @pytest.mark.parametrize(
        "lastname,expected",
        [
            # 'ИВАНОВ'.endswith('ов') is False; with normalization
            # 'иванов'.endswith('ов') matches the male suffix rule.
            ("ИВАНОВ", Gender.MALE),
            ("Иванов", Gender.MALE),
            # Female surname suffix rule.
            ("ИВАНОВА", Gender.FEMALE),
            ("Иванова", Gender.FEMALE),
        ],
    )
    def test_capitalized_lastname_suffix_matches(self, gender_detector, lastname, expected):
        assert gender_detector.detect(lastname=lastname) == expected

    def test_yo_letter_normalizes(self, gender_detector):
        # Ё/ё is a separate Unicode codepoint from Е/е but Python's
        # str.lower() handles it. 'лёва' is in firstname.exceptions.male,
        # so capitalized 'Лёва' should match after normalization.
        assert gender_detector.detect(firstname="Лёва") == Gender.MALE
        assert gender_detector.detect(firstname="ЛЁВА") == Gender.MALE


class TestPetrovichGenderDetectorConflictResolution:
    """
    Pin the firstname-and-lastname conflict-resolution path in
    detect(): when one part has a definite gender and the other is
    ANDROGYNOUS-only, the definite one wins.

    The two andro-only firstname exceptions in the rules data are
    'саша' and 'женя' — every other entry in firstname.exceptions.andro
    also matches one of the suffix rules and so resolves to a
    multi-element set rather than pure {ANDROGYNOUS}. The
    lastname.exceptions.andro list happens not to contain any
    pure-andro names at all (every entry overlaps a suffix rule), so
    only the lastname-decides-firstname direction is tested below.
    """

    def test_androgynous_firstname_with_definite_lastname_returns_lastname_gender(self, gender_detector):
        # 'Саша' resolves to ANDROGYNOUS only (firstname.exceptions);
        # 'Иванова' resolves to FEMALE (suffix rule). The conflict
        # resolver should return FEMALE rather than fall through.
        # Hits the `return ln` branch.
        assert gender_detector.detect(firstname="Саша", lastname="Иванова") == Gender.FEMALE
        # Same shape with the other direction of definite gender.
        assert gender_detector.detect(firstname="Женя", lastname="Иванов") == Gender.MALE


class TestPetrovichGenderDetectorErrorPaths:
    """
    Mirror of the maker's missing/malformed-rules-file tests for the
    detector. The contract is: a missing or unparseable gender.json
    raises RuntimeError with a hint telling the user how to fix it.
    """

    def test_missing_rules_file_raises_runtime_error(self, tmp_path):
        with pytest.raises(RuntimeError, match="rules file not found"):
            PetrovichGenderDetector(str(tmp_path / "does-not-exist.json"))

    def test_malformed_rules_file_raises_runtime_error(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("not valid json {{{")
        with pytest.raises(RuntimeError, match="malformed"):
            PetrovichGenderDetector(str(bad))
