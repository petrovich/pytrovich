import os

import pytest

from pytrovich.enums import Case, Gender, NamePart
from pytrovich.maker import PetrovichDeclinationMaker


@pytest.fixture(scope="session")
def maker() -> PetrovichDeclinationMaker:
    return PetrovichDeclinationMaker()


class TestPetrovichDeclinationMaker:
    @pytest.mark.parametrize(
        "name_part,gender,case_to_use,original_name,expected_result",
        (
            # firstnames
            (NamePart.FIRSTNAME, Gender.FEMALE, Case.GENITIVE, "Мария", "Марии"),
            (NamePart.FIRSTNAME, Gender.MALE, Case.DATIVE, "Василий", "Василию"),
            (NamePart.FIRSTNAME, Gender.FEMALE, Case.ACCUSATIVE, "Ксюша", "Ксюшу"),
            (NamePart.FIRSTNAME, Gender.MALE, Case.INSTRUMENTAL, "Паша", "Пашей"),
            (NamePart.FIRSTNAME, Gender.FEMALE, Case.PREPOSITIONAL, "Елена", "Елене"),
            # middlenames
            (NamePart.MIDDLENAME, Gender.FEMALE, Case.GENITIVE, "Геннадиевна", "Геннадиевны"),
            (NamePart.MIDDLENAME, Gender.MALE, Case.DATIVE, "Васильевич", "Васильевичу"),
            (NamePart.MIDDLENAME, Gender.FEMALE, Case.ACCUSATIVE, "Васильевна", "Васильевну"),
            (NamePart.MIDDLENAME, Gender.MALE, Case.INSTRUMENTAL, "Павлович", "Павловичем"),
            (NamePart.MIDDLENAME, Gender.FEMALE, Case.PREPOSITIONAL, "Павловна", "Павловне"),
            # lastnames
            (NamePart.LASTNAME, Gender.FEMALE, Case.GENITIVE, "Цветаева", "Цветаевой"),
            (NamePart.LASTNAME, Gender.MALE, Case.DATIVE, "Толстой", "Толстому"),
            (NamePart.LASTNAME, Gender.FEMALE, Case.ACCUSATIVE, "Ахматова", "Ахматову"),
            (NamePart.LASTNAME, Gender.MALE, Case.INSTRUMENTAL, "Лермонтов", "Лермонтовым"),
            (NamePart.LASTNAME, Gender.FEMALE, Case.PREPOSITIONAL, "Баркова", "Барковой"),
        ),
    )
    def test_common_names(
        self,
        maker: PetrovichDeclinationMaker,
        name_part: NamePart,
        gender: Gender,
        case_to_use: Case,
        original_name: str,
        expected_result: str,
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

    @pytest.mark.parametrize(
        "case,expected",
        (
            (Case.NOMINATIVE, "Иван"),
            (Case.GENITIVE, "Ивана"),
            (Case.DATIVE, "Ивану"),
            (Case.ACCUSATIVE, "Ивана"),
            (Case.INSTRUMENTAL, "Иваном"),
            (Case.PREPOSITIONAL, "Иване"),
        ),
    )
    def test_all_cases_for_one_name(self, maker, case, expected):
        # Exercises every Case enum value for a single male firstname.
        # Nominative is the identity (input unchanged); the five
        # oblique cases each have a distinct form.
        assert maker.make(NamePart.FIRSTNAME, Gender.MALE, case, "Иван") == expected

    def test_lowercase_input_is_processed_via_suffix_match(self, maker):
        # Suffix matching is case-sensitive on the input; lowercase 'иван'
        # still ends in 'н' so the rule applies, yielding lowercase output.
        assert maker.make(NamePart.FIRSTNAME, Gender.MALE, Case.GENITIVE, "иван") == "ивана"

    def test_hyphenated_lastname_inflects_only_trailing_component(self, maker):
        # The library does not split hyphenated surnames; it applies the
        # suffix rule once to the whole string, which means only the
        # trailing component looks inflected.
        assert maker.make(NamePart.LASTNAME, Gender.MALE, Case.GENITIVE, "Иванов-Петров") == "Иванов-Петрова"

    def test_name_with_yo_letter(self, maker):
        # Russian morphology shifts 'ё' to 'е' in oblique cases of 'Пётр'
        # (correct genitive: 'Петра'). The rules data ships an explicit
        # exception encoding this alternation. Before case-normalization,
        # the library couldn't find it (case-sensitive lookup against
        # the lowercase exception list), fell through to the generic
        # '-р' suffix rule, and produced the incorrect 'Пётра'.
        assert maker.make(NamePart.FIRSTNAME, Gender.MALE, Case.GENITIVE, "Пётр") == "Петра"

    def test_indeclinable_foreign_lastname(self, maker):
        # 'Дюма' is conventionally indeclinable in Russian for both
        # genders, and the rules data encodes that with an exception
        # whose mods are all '.' (keep-as-is). Before case-normalization
        # the library missed that exception and fell through to the
        # 'а'-suffix rule, incorrectly producing 'Дюмы'.
        assert maker.make(NamePart.LASTNAME, Gender.MALE, Case.GENITIVE, "Дюма") == "Дюма"
        assert maker.make(NamePart.LASTNAME, Gender.FEMALE, Case.GENITIVE, "Дюма") == "Дюма"

    def test_empty_string_returns_empty_string(self, maker):
        # No input validation: empty name returns empty string silently.
        assert maker.make(NamePart.LASTNAME, Gender.MALE, Case.GENITIVE, "") == ""

    def test_missing_rules_file_raises_runtime_error(self, tmp_path):
        # The constructor used to silently fall back to a frozen 2020 copy
        # of the rules embedded as pytrovich/rules_data.py. That fallback
        # was removed because it diverged from the upstream rules and
        # masked real bugs. A missing rules file now raises RuntimeError
        # with a hint telling the user how to fix it.
        with pytest.raises(RuntimeError, match="rules file not found"):
            PetrovichDeclinationMaker(str(tmp_path / "does-not-exist.json"))

    def test_malformed_rules_file_raises_runtime_error(self, tmp_path):
        # Same defensive contract for unparseable JSON.
        bad = tmp_path / "bad.json"
        bad.write_text("not valid json {{{")
        with pytest.raises(RuntimeError, match="malformed"):
            PetrovichDeclinationMaker(str(bad))

    def test_custom_rules_file_is_loaded(self):
        # Explicit-path constructor is part of the public API. The skip
        # branch that used to be here for missing rules.json is now
        # unreachable: if rules.json weren't present, the `maker` session
        # fixture would have raised RuntimeError before this test ran.
        bundled = os.path.join(
            os.path.dirname(__import__("pytrovich").__file__),
            "petrovich-rules",
            "rules.json",
        )
        instance = PetrovichDeclinationMaker(bundled)
        assert instance.make(NamePart.FIRSTNAME, Gender.MALE, Case.GENITIVE, "Иван") == "Ивана"


class TestPetrovichDeclinationMakerKnownIssues:
    """
    Each test here pins down a defect identified during code review.
    All are marked xfail(strict=True); when a fix lands, the test will
    XPASS and the suite will turn red, prompting removal of the marker.
    Do NOT delete these tests on fix — convert them to plain assertions.
    """

    @pytest.mark.parametrize("case", list(Case))
    def test_string_name_part_raises_type_error(self, maker, case):
        # Pre-fix, passing a string literal instead of the NamePart
        # enum silently fell through the dispatch and returned the
        # input unchanged. Now raises TypeError with a hint.
        # Parametrized over every Case to catch the asymmetric-validation
        # bug where NOMINATIVE's early-return short-circuited above the
        # name_part check.
        with pytest.raises(TypeError, match="name_part must be a NamePart"):
            maker.make("FIRSTNAME", Gender.MALE, case, "Иван")

    @pytest.mark.parametrize("case", list(Case))
    def test_none_name_part_raises_type_error(self, maker, case):
        with pytest.raises(TypeError, match="name_part must be a NamePart"):
            maker.make(None, Gender.MALE, case, "Иван")


class TestPetrovichDeclinationMakerCaseNormalization:
    """
    The rules data uses lowercase Cyrillic throughout (suffix tests
    'ов', 'ская', exception names 'пётр', 'дюма'). The maker now
    lowercases input for rule lookup so all-caps and mixed-case inputs
    inflect correctly, while keeping the original casing in the output
    via apply_mod2name. Mirrors the same fix in
    PetrovichGenderDetector.detect.
    """

    @pytest.mark.parametrize(
        "input_name,expected",
        [
            # Title Case: regression watch — must keep producing the
            # same output as before the fix.
            ("Иван", "Ивана"),
            ("Иванов", "Иванова"),
            ("Касперский", "Касперского"),
            # All-caps: previously fell through unchanged because
            # 'ИВАНОВ'.endswith('ов') is False. Now the suffix rule
            # fires and the appended modifier is preserved.
            ("ИВАН", "ИВАНа"),
            ("ИВАНОВ", "ИВАНОВа"),
            # Mixed case is unusual but defensible.
            ("иВаН", "иВаНа"),
        ],
    )
    def test_case_variation_inflects(self, maker, input_name, expected):
        np = NamePart.FIRSTNAME if input_name.lower() == "иван" else NamePart.LASTNAME
        assert maker.make(np, Gender.MALE, Case.GENITIVE, input_name) == expected

    def test_uppercase_yo_finds_lowercase_exception(self):
        # 'ПЁТР'.lower() == 'пётр', which is in the rules-data
        # exception list. The mods for that exception are character
        # replacements ('---етра'), so the output is the literal
        # lowercase from the rule — the trailing case-preservation
        # only applies to *append* mods, not to character-replacement.
        # That's a quirk of how the rules data encodes exceptions,
        # not the case-normalization fix.
        from pytrovich.maker import PetrovichDeclinationMaker

        m = PetrovichDeclinationMaker()
        assert m.make(NamePart.FIRSTNAME, Gender.MALE, Case.GENITIVE, "ПЁТР") == "Петра"
        assert m.make(NamePart.FIRSTNAME, Gender.MALE, Case.GENITIVE, "Пётр") == "Петра"

    def test_hyphenated_uppercase_inflects(self, maker):
        # Pre-fix, the all-caps form fell through unchanged because
        # the suffix rule was case-sensitive. Now it inflects, with
        # the original case preserved on the unmodified portion.
        assert maker.make(NamePart.LASTNAME, Gender.MALE, Case.GENITIVE, "ИВАНОВ-ПЕТРОВ") == "ИВАНОВ-ПЕТРОВа"


class TestPetrovichDeclinationMakerNominative:
    """
    Pin the contract for Case.NOMINATIVE: the identity transformation.
    Exists so callers can iterate over all six members of `Case`
    uniformly when generating a full declension table — same idiom as
    petrovich-ruby's `Petrovich::CASES.each`.
    """

    def test_nominative_returns_input_unchanged(self, maker):
        # No rule lookup, no inflection — input flows straight through.
        assert maker.make(NamePart.FIRSTNAME, Gender.MALE, Case.NOMINATIVE, "Иван") == "Иван"
        assert maker.make(NamePart.LASTNAME, Gender.FEMALE, Case.NOMINATIVE, "Иванова") == "Иванова"
        assert maker.make(NamePart.MIDDLENAME, Gender.MALE, Case.NOMINATIVE, "Иванович") == "Иванович"

    def test_nominative_handles_empty_string(self, maker):
        # The early-return precedes apply_mod2name's slicing logic
        # (`name[:-n]`), which on an empty string would still be safe
        # but worth pinning: NOMINATIVE on '' returns '' rather than
        # accidentally indexing or raising.
        assert maker.make(NamePart.FIRSTNAME, Gender.MALE, Case.NOMINATIVE, "") == ""

    def test_nominative_works_alongside_all_other_cases(self, maker):
        # Concretely exercise the petrovich-ruby idiom:
        #   forms = [maker.make(part, gender, c, name) for c in Case]
        forms = [maker.make(NamePart.LASTNAME, Gender.MALE, c, "Иванов") for c in Case]
        assert forms == [
            "Иванова",  # GENITIVE
            "Иванову",  # DATIVE
            "Иванова",  # ACCUSATIVE
            "Ивановым",  # INSTRUMENTAL
            "Иванове",  # PREPOSITIONAL
            "Иванов",  # NOMINATIVE
        ]
