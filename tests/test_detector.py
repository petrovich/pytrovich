import pytest

from pytrovich.detector import PetrovichGenderDetector
from pytrovich.enums import Gender


@pytest.fixture(scope='session')
def gender_detector():
    return PetrovichGenderDetector()


class TestPetrovichGenderDetector:
    @pytest.mark.parametrize('middlename,expected_gender', (
            ('Иванович', Gender.MALE),
            ('Ильинична', Gender.FEMALE),
            pytest.param(
                'Блаблабла', Gender.ANDROGYNOUS,
                marks=pytest.mark.xfail(reason='Issue #6'),
            ),
    ))
    def test_detect_by_middlename(self, gender_detector, middlename, expected_gender):
        assert gender_detector.detect(middlename=middlename) == expected_gender


class TestPetrovichGenderDetectorCoverage:
    """
    Adds coverage for code paths in PetrovichGenderDetector.detect not
    exercised by the original middlename-only test: detection by firstname
    only, by lastname only, by combinations, and the foreign-patronymic
    exception path.
    """

    @pytest.mark.parametrize('firstname,expected', (
            ('Иван', Gender.MALE),
            ('Алексей', Gender.MALE),
            ('Мария', Gender.FEMALE),
            ('Елена', Gender.FEMALE),
    ))
    def test_detect_by_firstname(self, gender_detector, firstname, expected):
        assert gender_detector.detect(firstname=firstname) == expected

    @pytest.mark.parametrize('lastname,expected', (
            ('Голубцов', Gender.MALE),
            ('Лермонтов', Gender.MALE),
            ('Цветаева', Gender.FEMALE),
            ('Ахматова', Gender.FEMALE),
    ))
    def test_detect_by_lastname(self, gender_detector, lastname, expected):
        assert gender_detector.detect(lastname=lastname) == expected

    @pytest.mark.parametrize('firstname,middlename,expected', (
            ('Иван', 'Семёнович', Gender.MALE),
            ('Анна', 'Петровна', Gender.FEMALE),
            # Azerbaijani patronymics: 'кызы' = daughter (female),
            # 'оглы' = son (male). These exercise the suffix-detection path on
            # middlenames where the firstname alone is foreign/androgynous.
            ('Арзу', 'Лутфияр кызы', Gender.FEMALE),
            ('Рамиз', 'Рустам оглы', Gender.MALE),
    ))
    def test_detect_by_firstname_and_middlename(
            self, gender_detector, firstname, middlename, expected,
    ):
        assert gender_detector.detect(
            firstname=firstname, middlename=middlename,
        ) == expected

    def test_detect_combined_firstname_and_lastname(self, gender_detector):
        # Both parts agree on MALE.
        assert gender_detector.detect(
            firstname='Иван', lastname='Голубцов',
        ) == Gender.MALE


class TestPetrovichGenderDetectorKnownIssues:
    """
    Each test here pins down a defect identified during code review.
    Marked xfail(strict=True): a fix will turn them XPASS and the
    suite red. Do NOT delete these tests on fix — convert them to
    plain assertions.
    """

    @pytest.mark.parametrize('firstname', [
        'Саша',  # legitimate Russian androgynous diminutive
        'Блаблабла',  # nonsense input
        '',  # empty string bypasses the None-only assert
    ])
    @pytest.mark.xfail(
        reason=(
                "detector.py:97 calls next(iter(joined_set)) on a possibly-empty "
                "set when no rule matches and there are no exceptions, raising "
                "StopIteration instead of returning Gender.ANDROGYNOUS or a "
                "typed exception. The existing 'Блаблабла' middlename xfail "
                "(Issue #6) is the same bug surfaced through firstname."
        ),
        strict=True,
        raises=StopIteration,
    )
    def test_unknown_firstname_does_not_crash(self, gender_detector, firstname):
        result = gender_detector.detect(firstname=firstname)
        # Acceptable post-fix behaviors: ANDROGYNOUS or None.
        assert result is None or isinstance(result, Gender)

    @pytest.mark.xfail(
        reason=(
                "detector.py:63 uses 'assert' for argument validation. Under "
                "`python -O` the assertion is stripped and downstream code "
                "crashes with AttributeError on a None Name. Validation should "
                "raise ValueError unconditionally."
        ),
        strict=True,
    )
    def test_no_arguments_raises_value_error(self, gender_detector):
        with pytest.raises(ValueError):
            gender_detector.detect()
