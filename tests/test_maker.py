import os

import pytest

from pytrovich.enums import Case, NamePart, Gender
from pytrovich.maker import PetrovichDeclinationMaker


@pytest.fixture(scope='session')
def maker() -> PetrovichDeclinationMaker:
    return PetrovichDeclinationMaker()


class TestPetrovichDeclinationMaker:
    @pytest.mark.parametrize('name_part,gender,case_to_use,original_name,expected_result', (
        # firstnames
        (NamePart.FIRSTNAME, Gender.FEMALE, Case.GENITIVE, 'Мария', 'Марии'),
        (NamePart.FIRSTNAME, Gender.MALE, Case.DATIVE, 'Василий', 'Василию'),
        (NamePart.FIRSTNAME, Gender.FEMALE, Case.ACCUSATIVE, 'Ксюша', 'Ксюшу'),
        (NamePart.FIRSTNAME, Gender.MALE, Case.INSTRUMENTAL, 'Паша', 'Пашой'),
        (NamePart.FIRSTNAME, Gender.FEMALE, Case.PREPOSITIONAL, 'Елена', 'Елене'),
        # middlenames
        (NamePart.MIDDLENAME, Gender.FEMALE, Case.GENITIVE, 'Геннадиевна', 'Геннадиевны'),
        (NamePart.MIDDLENAME, Gender.MALE, Case.DATIVE, 'Васильевич', 'Васильевичу'),
        (NamePart.MIDDLENAME, Gender.FEMALE, Case.ACCUSATIVE, 'Васильевна', 'Васильевну'),
        (NamePart.MIDDLENAME, Gender.MALE, Case.INSTRUMENTAL, 'Павлович', 'Павловичем'),
        (NamePart.MIDDLENAME, Gender.FEMALE, Case.PREPOSITIONAL, 'Павловна', 'Павловне'),
        # lastnames
        (NamePart.LASTNAME, Gender.FEMALE, Case.GENITIVE, 'Цветаева', 'Цветаевой'),
        (NamePart.LASTNAME, Gender.MALE, Case.DATIVE, 'Толстой', 'Толстому'),
        (NamePart.LASTNAME, Gender.FEMALE, Case.ACCUSATIVE, 'Ахматова', 'Ахматову'),
        (NamePart.LASTNAME, Gender.MALE, Case.INSTRUMENTAL, 'Лермонтов', 'Лермонтовым'),
        (NamePart.LASTNAME, Gender.FEMALE, Case.PREPOSITIONAL, 'Баркова', 'Барковой'),
    ))
    def test_common_names(
        self,
        maker: PetrovichDeclinationMaker,
        name_part: NamePart,
        gender: Gender,
        case_to_use: Case,
        original_name: str,
        expected_result: str
    ) -> None:

        assert maker.make(name_part, gender, case_to_use, original_name) == expected_result


class TestPetrovichDeclinationMakerCoverage:
    """
    Additional coverage for code paths and edge cases not exercised by
    test_common_names. These tests lock in *current* behavior. Where current
    behavior is morphologically incorrect (e.g. 'Лев' -> 'Лева' instead of
    'Льва'), the comment notes the discrepancy so a future fix becomes a
    visible test failure rather than a silent change.
    """

    @pytest.mark.parametrize('case,expected', (
        (Case.GENITIVE, 'Ивана'),
        (Case.DATIVE, 'Ивану'),
        (Case.ACCUSATIVE, 'Ивана'),
        (Case.INSTRUMENTAL, 'Иваном'),
        (Case.PREPOSITIONAL, 'Иване'),
    ))
    def test_all_cases_for_one_name(self, maker, case, expected):
        # Exercises every Case enum value for a single male firstname.
        assert maker.make(NamePart.FIRSTNAME, Gender.MALE, case, 'Иван') == expected

    def test_lowercase_input_is_processed_via_suffix_match(self, maker):
        # Suffix matching is case-sensitive on the input; lowercase 'иван'
        # still ends in 'н' so the rule applies, yielding lowercase output.
        assert maker.make(NamePart.FIRSTNAME, Gender.MALE, Case.GENITIVE, 'иван') == 'ивана'

    def test_hyphenated_lastname_inflects_only_trailing_component(self, maker):
        # The library does not split hyphenated surnames; it applies the
        # suffix rule once to the whole string, which means only the
        # trailing component looks inflected.
        assert maker.make(
            NamePart.LASTNAME, Gender.MALE, Case.GENITIVE, 'Иванов-Петров'
        ) == 'Иванов-Петрова'

    def test_name_with_yo_letter(self, maker):
        # Russian morphology shifts 'ё' to 'е' in oblique cases of 'Пётр'
        # (correct genitive: 'Петра'). The library does not perform this
        # alternation, so the current output is 'Пётра'. Locking it in.
        assert maker.make(NamePart.FIRSTNAME, Gender.MALE, Case.GENITIVE, 'Пётр') == 'Пётра'

    def test_indeclinable_foreign_lastname_is_currently_inflected(self, maker):
        # 'Дюма' is conventionally indeclinable in Russian for both genders.
        # The library inflects it via the 'а'-suffix rule, producing 'Дюмы'.
        # This is a rules-data limitation; locking in current behavior.
        assert maker.make(
            NamePart.LASTNAME, Gender.MALE, Case.GENITIVE, 'Дюма'
        ) == 'Дюмы'
        assert maker.make(
            NamePart.LASTNAME, Gender.FEMALE, Case.GENITIVE, 'Дюма'
        ) == 'Дюмы'

    def test_empty_string_returns_empty_string(self, maker):
        # No input validation: empty name returns empty string silently.
        assert maker.make(NamePart.LASTNAME, Gender.MALE, Case.GENITIVE, '') == ''

    def test_missing_rules_file_falls_back_to_bundled_data(self, tmp_path, capsys):
        # An invalid rules path should not raise; it logs to stderr and
        # falls back to the embedded rules_data module.
        instance = PetrovichDeclinationMaker(str(tmp_path / 'does-not-exist.json'))
        captured = capsys.readouterr()
        assert 'Error occurred' in captured.err
        assert 'outdated rules' in captured.err
        # And it still works.
        assert instance.make(
            NamePart.FIRSTNAME, Gender.MALE, Case.GENITIVE, 'Иван'
        ) == 'Ивана'

    def test_custom_rules_file_is_loaded(self):
        # If a user passes a valid path, it is used in preference to the
        # bundled rules.
        bundled = os.path.join(
            os.path.dirname(__import__('pytrovich').__file__),
            'petrovich-rules', 'rules.json',
        )
        if not os.path.exists(bundled):
            pytest.skip("bundled rules.json not present in this checkout")
        instance = PetrovichDeclinationMaker(bundled)
        assert instance.make(
            NamePart.FIRSTNAME, Gender.MALE, Case.GENITIVE, 'Иван'
        ) == 'Ивана'


class TestPetrovichDeclinationMakerKnownIssues:
    """
    Each test here pins down a defect identified during code review.
    All are marked xfail(strict=True); when a fix lands, the test will
    XPASS and the suite will turn red, prompting removal of the marker.
    Do NOT delete these tests on fix — convert them to plain assertions.
    """

    @pytest.mark.xfail(
        reason=(
            "maker.py:36-37: an unrecognized NamePart (e.g. a string) is "
            "silently treated as MIDDLENAME, so make('FIRSTNAME', ...) "
            "returns the input unchanged with no error. Should raise "
            "TypeError or ValueError."
        ),
        strict=True,
    )
    def test_string_name_part_should_raise(self, maker):
        with pytest.raises((TypeError, ValueError)):
            # Note: passing a *string* literal instead of NamePart.FIRSTNAME.
            maker.make('FIRSTNAME', Gender.MALE, Case.GENITIVE, 'Иван')

    @pytest.mark.xfail(
        reason=(
            "Same fall-through as above: None NamePart is treated as "
            "MIDDLENAME and the input is returned unchanged."
        ),
        strict=True,
    )
    def test_none_name_part_should_raise(self, maker):
        with pytest.raises((TypeError, ValueError)):
            maker.make(None, Gender.MALE, Case.GENITIVE, 'Иван')
