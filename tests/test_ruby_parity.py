"""
Parity tests against the petrovich-ruby reference semantics.

pytrovich historically diverged from the canonical Ruby implementation
in four ways, all fixed together with the petrovich-rules bump to the
2024 data (df207fb):

1. Hyphenated names were not split (Issue #2) — Салтыков-Щедрин only
   declined on the trailing component.
2. Exception rules were matched as *suffixes* instead of whole words —
   Ельцин hit the lastname exception "цин" (Ельцином instead of
   Ельциным), and with the 2024 rules Наталия would have hit the new
   firstname exception "алия" (Наталие instead of Наталии).
3. Rule selection let androgynous rules compete on the first pass and
   used a cross-cutting exception/suffix priority. Ruby resolves the
   first match over one ordered list (exceptions, then suffixes) with
   an exact-gender filter, then falls back to an androgynous pass.
4. Gender detection unioned all matching suffixes across genders and
   picked by enum value. Ruby consults the exact-match exception first
   and otherwise takes the LONGEST matching suffix; hyphenated parts
   resolve per component with the last one deciding, and a genuine
   male-vs-female conflict yields no answer (nil in Ruby, ANDROGYNOUS
   here).

Every expected value below was cross-checked against the petrovich-eval
corpus and/or a petrovich-ruby-faithful reference implementation.
"""

import pytest

from pytrovich.detector import PetrovichGenderDetector
from pytrovich.enums import Case, Gender, NamePart
from pytrovich.maker import PetrovichDeclinationMaker


@pytest.fixture(scope="module")
def maker() -> PetrovichDeclinationMaker:
    return PetrovichDeclinationMaker()


@pytest.fixture(scope="module")
def detector() -> PetrovichGenderDetector:
    return PetrovichGenderDetector()


class TestHyphenatedNamesSplitLikeRuby:
    @pytest.mark.parametrize(
        "name_part,name,gender,case_to_use,expected",
        [
            # Both components decline (eval/surnames.misc.tsv).
            (NamePart.LASTNAME, "Салтыков-Щедрин", Gender.MALE, Case.DATIVE, "Салтыкову-Щедрину"),
            (NamePart.LASTNAME, "Петров-Водкин", Gender.MALE, Case.GENITIVE, "Петрова-Водкина"),
            # Indeclinable exception holds on the first component.
            (NamePart.LASTNAME, "Тер-Петрова", Gender.FEMALE, Case.DATIVE, "Тер-Петровой"),
            # Hyphenated first names and patronymics split too.
            (NamePart.FIRSTNAME, "Анна-Мария", Gender.FEMALE, Case.DATIVE, "Анне-Марии"),
            (NamePart.MIDDLENAME, "Борух-Бендитовна", Gender.FEMALE, Case.DATIVE, "Борух-Бендитовне"),
        ],
    )
    def test_each_component_declines(self, maker, name_part, name, gender, case_to_use, expected):
        assert maker.make(name_part, gender, case_to_use, name) == expected


class TestExceptionsMatchWholeWordsOnly:
    @pytest.mark.parametrize(
        "name,expected",
        [
            # End with the exception string "цин" but are NOT the
            # exception word; must take the regular -ин declension
            # (instrumental -ым), not the exception's -ом.
            ("Ельцин", "Ельциным"),
            ("Спицин", "Спициным"),
        ],
    )
    def test_lastnames_ending_in_an_exception_string(self, maker, name, expected):
        assert maker.make(NamePart.LASTNAME, Gender.MALE, Case.INSTRUMENTAL, name) == expected

    def test_exact_exception_word_still_uses_the_exception(self, maker):
        # The whole-word match must not break the exception itself.
        assert maker.make(NamePart.LASTNAME, Gender.MALE, Case.INSTRUMENTAL, "Цин") == "Цином"

    @pytest.mark.parametrize(
        "name,expected",
        [
            # The 2024 rules add whole-word exceptions алия/асия/… for
            # Tatar names (dative in -е). Common Russian names that
            # merely END in those strings must keep the regular -ия
            # declension (dative -и).
            ("Наталия", "Наталии"),
            ("Анастасия", "Анастасии"),
        ],
    )
    def test_common_names_ending_in_new_exception_strings(self, maker, name, expected):
        assert maker.make(NamePart.FIRSTNAME, Gender.FEMALE, Case.DATIVE, name) == expected

    def test_tatar_exception_names_themselves(self, maker):
        assert maker.make(NamePart.FIRSTNAME, Gender.FEMALE, Case.DATIVE, "Алия") == "Алие"

    def test_firstname_exception_lev(self, maker):
        # Regression guard: the canonical exception still applies.
        assert maker.make(NamePart.FIRSTNAME, Gender.MALE, Case.GENITIVE, "Лев") == "Льва"
        # …and a word merely ending in "лев" must not.
        assert maker.make(NamePart.LASTNAME, Gender.MALE, Case.GENITIVE, "Королев") == "Королева"


class TestRubyGenderFilter:
    def test_known_female_keeps_androgynous_indeclinable_via_fallback(self, maker):
        # Дюма is an androgynous indeclinable exception. With a KNOWN
        # female gender the first pass admits only female rules (none
        # match), and the androgynous fallback pass then finds the
        # exception — so the name stays indeclinable.
        assert maker.make(NamePart.LASTNAME, Gender.FEMALE, Case.DATIVE, "Дюма") == "Дюма"

    def test_known_gender_changes_ambiguous_surname(self, maker):
        assert maker.make(NamePart.LASTNAME, Gender.MALE, Case.DATIVE, "Воробей") == "Воробью"
        assert maker.make(NamePart.LASTNAME, Gender.FEMALE, Case.DATIVE, "Воробей") == "Воробей"


class TestGenderDetectionRubySemantics:
    def test_exception_beats_suffix(self, detector):
        # 'Иона' is an explicit androgynous exception; the female -а
        # suffix must not override it.
        assert detector.detect(firstname="Иона") == Gender.ANDROGYNOUS

    def test_longest_suffix_wins(self, detector):
        # 'Склифасовская' matches both short and long suffixes; the
        # longest (female) one decides.
        assert detector.detect(lastname="Склифасовская") == Gender.FEMALE
        assert detector.detect(lastname="Склифасовский") == Gender.MALE

    def test_definite_part_beats_androgynous_part(self, detector):
        assert detector.detect(firstname="Саша", lastname="Иванов") == Gender.MALE

    def test_confident_patronymic_wins(self, detector):
        assert (
            detector.detect(firstname="Саша", lastname="Андрейчук", middlename="Олегович")
            == Gender.MALE
        )

    def test_hyphenated_part_resolves_on_last_component(self, detector):
        assert detector.detect(middlename="Мухаммад-кызы") == Gender.FEMALE

    def test_space_separated_turkic_patronymics(self, detector):
        assert detector.detect(middlename="Мухаммад оглы") == Gender.MALE
        assert detector.detect(middlename="Мухаммад кызы") == Gender.FEMALE

    def test_true_conflict_returns_androgynous(self, detector):
        # Male first name vs female surname: petrovich-ruby returns
        # nil; the total-function contract here maps that to
        # ANDROGYNOUS.
        assert detector.detect(firstname="Иван", lastname="Иванова") == Gender.ANDROGYNOUS
