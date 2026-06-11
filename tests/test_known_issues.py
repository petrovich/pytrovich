"""
Tests pinned to specific GitHub issues on petrovich/pytrovich.

Each class below corresponds to one open issue in the tracker. All tests
are marked ``xfail(strict=True)`` because the underlying issues are still
open: when an issue is fixed, its tests will XPASS, the suite will turn
red, and the maintainer must remove the marker (and ideally close the
issue) in the same change. Do NOT delete these tests when an issue is
fixed — convert ``xfail`` to plain assertions so we keep regression
coverage.

Issues covered (as of last update):

  * Issue #2 — Hyphenated lastname support. Resolved: make() splits on
    hyphens and inflects each component, like petrovich-ruby; tests
    below pin the contract against regression.
    https://github.com/petrovich/pytrovich/issues/2

  * Issue #6 — PetrovichGenderDetector.detect should return
    Gender.ANDROGYNOUS for unrecognized names instead of crashing with
    StopIteration. Resolved; tests below pin the canonical contract
    against regression.
    https://github.com/petrovich/pytrovich/issues/6

  * Issue #8 — Three reported genitive-case inflection bugs (Асадчий,
    Гремитских, Ольга). Only the Асадчий case reproduces, and only
    against the bundled rules_data.py.
    https://github.com/petrovich/pytrovich/issues/8

If a third issue exists in the tracker, add a class for it here.
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


# ---------------------------------------------------------------------------
# Issue #2 — Hyphenated lastname support
# ---------------------------------------------------------------------------


class TestIssue2HyphenatedLastnames:
    """
    https://github.com/petrovich/pytrovich/issues/2

    Reporter (georgthegreat, 2022-01-15):

        In Cyrillic we have many double lastnames. This includes some
        simple cases such as: Петров-Водкин, Бестужев-Марлинский. [...]
        These can be handled by naive code: split the lexem by hyphen,
        translate each part, join back with hyphen. However, this becomes
        nasty with exceptions, including Бонч-Бруевич, Мамин-Сибиряк,
        Муравьёв-Апостол.

    RESOLVED: make() now splits on hyphens and inflects each component
    with its own rule, matching petrovich-ruby's Inflector#inflect.
    "Петров-Водкин" in the genitive correctly becomes
    "Петрова-Водкина".

    The "nasty" exception cases also come out right, for the right
    reason: "бонч" is an explicit indeclinable exception in
    petrovich-rules, and exceptions are matched per hyphen-component,
    so "Бонч-Бруевич" declines only on the second component.
    """

    SIMPLE_HYPHENATED_NAMES_FROM_ISSUE = [
        "Петров-Водкин",
        "Бестужев-Марлинский",
    ]

    NASTY_EXCEPTIONS_FROM_ISSUE = [
        # (lastname, gender, case, expected_correct_output)
        # Бонч is foreign-origin (German "Bontsch") and conventionally
        # indeclinable in Russian — only the second part inflects.
        ("Бонч-Бруевич", Gender.MALE, Case.GENITIVE, "Бонч-Бруевича"),
        ("Бонч-Бруевич", Gender.MALE, Case.INSTRUMENTAL, "Бонч-Бруевичем"),
    ]

    @pytest.mark.parametrize(
        "case_to_use",
        [
            Case.GENITIVE,
            Case.DATIVE,
            Case.ACCUSATIVE,
            Case.INSTRUMENTAL,
            Case.PREPOSITIONAL,
        ],
    )
    @pytest.mark.parametrize("lastname", SIMPLE_HYPHENATED_NAMES_FROM_ISSUE)
    def test_simple_hyphenated_inflects_each_part(
        self,
        maker,
        lastname,
        case_to_use,
    ):
        # Issue #2 is fixed: make() splits on hyphens and inflects each
        # component with its own rule, as petrovich-ruby's
        # Inflector#inflect does. (Formerly xfail(strict=True);
        # converted to a plain assertion per this module's policy.)
        # The expected output is computed by running each part through
        # the library separately and rejoining — the exact "naive code"
        # approach the issue describes.
        parts = lastname.split("-")
        expected = "-".join(maker.make(NamePart.LASTNAME, Gender.MALE, case_to_use, p) for p in parts)
        actual = maker.make(NamePart.LASTNAME, Gender.MALE, case_to_use, lastname)
        assert actual == expected

    @pytest.mark.parametrize(
        "lastname,gender,case_to_use,expected",
        NASTY_EXCEPTIONS_FROM_ISSUE,
    )
    def test_hyphenated_with_indeclinable_first_part(
        self,
        maker,
        lastname,
        gender,
        case_to_use,
        expected,
    ):
        # With hyphen splitting in place this output is now correct for
        # the right reason: "бонч" hits the indeclinable lastname
        # exception in petrovich-rules (matched per component), so only
        # "Бруевич" declines. Before the fix the same string came out
        # only because the whole-string suffix lookup happened to touch
        # just the trailing component.
        actual = maker.make(NamePart.LASTNAME, gender, case_to_use, lastname)
        assert actual == expected


# ---------------------------------------------------------------------------
# Issue #6 — Unknown name should return Gender.ANDROGYNOUS, not crash
# ---------------------------------------------------------------------------


class TestIssue6UnknownNameReturnsAndrogynous:
    """
    https://github.com/petrovich/pytrovich/issues/6

    The contract documented in the canonical Ruby reference (rubydoc.info
    for `Petrovich.detect_gender`, stable across versions 0.1.6 and
    0.2.1):

        Если пол не был определён, метод возвращает значение androgynous
        detect_gender('блаблабла')  # => androgynous

    pytrovich previously violated this: detect() called
    next(iter(joined_set)) on a possibly-empty set inside the else-branch,
    raising StopIteration on unrecognized inputs. The fix returns
    Gender.ANDROGYNOUS in the empty-set case.

    The cases tested below cover three failure modes that all funnelled
    into the same StopIteration:

      * 'Блаблабла' — the canonical nonsense name from the reference docs.
      * 'Саша' — a legitimate Russian androgynous diminutive (short for
        either Александр or Александра); after lowercasing nothing
        matches in firstname/lastname rules so the empty-set path runs.
      * '' — empty string. Bypasses the None-only assert at the top
        of detect() (a separate input-validation gap, not in scope here)
        and hits the same empty-set path.
    """

    UNRECOGNIZED_NAMES = [
        "Блаблабла",  # canonical nonsense from the reference docs
        "Саша",  # legitimate androgynous diminutive
        "",  # empty string — separate input-validation gap
    ]

    @pytest.mark.parametrize("name", UNRECOGNIZED_NAMES)
    @pytest.mark.parametrize("name_part_kwarg", ["firstname", "lastname", "middlename"])
    def test_unrecognized_name_returns_androgynous(
        self,
        detector,
        name_part_kwarg,
        name,
    ):
        result = detector.detect(**{name_part_kwarg: name})
        assert result == Gender.ANDROGYNOUS


# ---------------------------------------------------------------------------
# Issue #8 — Specific genitive-case inflection bugs (data-dependent)
# ---------------------------------------------------------------------------


class TestIssue8GenitiveInflectionBugs:
    """
    https://github.com/petrovich/pytrovich/issues/8

    Reporter (@Star23397, 2025-11-17) listed three specific incorrect
    inflections from nominative to genitive:

    1. Male lastname "Асадчий"  → got 'Асадчия',     expected 'Асадчего'
       (cf. Касперский → Касперского; same -ий ending)
    2. Male lastname "Гремитских" should be indeclinable, but reportedly
       inflects to 'Гремитскиха'.
    3. Female firstname "Ольга" → got 'Ольгы',       expected 'Ольги'.

    Maintainer (@alexeyev, 2025-11-27) commented that the "Ольга" case
    does not reproduce in their environment, and asked for a minimal
    repro plus the pytrovich version.

    Empirical findings:

      * "Асадчий" reproduced ONLY against the 2020-vintage embedded
        copy of the rules at pytrovich/rules_data.py, which silently
        replaced rules.json whenever the submodule was missing. That
        copy was removed in the same change as this comment; pytrovich
        now reads its rules exclusively from the petrovich-rules
        submodule's rules.json, which produces the correct 'Асадчего'.
        Locked in below.
      * "Гремитских" does NOT reproduce; the library correctly leaves
        it indeclinable. Locked in below.
      * "Ольга" does NOT reproduce (matches the maintainer's
        observation); the library correctly returns 'Ольги'. Locked in
        below.
    """

    def test_asadchiy_male_genitive(self, maker):
        # Russian morphology: lastnames ending -ий (after a soft
        # consonant) take the adjectival genitive ending -его, like
        # Касперский → Касперского. The companion reference test
        # below pins that the rule itself works.
        assert (
            maker.make(
                NamePart.LASTNAME,
                Gender.MALE,
                Case.GENITIVE,
                "Асадчий",
            )
            == "Асадчего"
        )

    def test_kasperskiy_male_genitive_reference(self, maker):
        # Reference / sanity check: same -ий pattern as Асадчий, works
        # correctly in both rules versions. If this ever regresses, the
        # Асадчий fix would also need re-checking.
        assert (
            maker.make(
                NamePart.LASTNAME,
                Gender.MALE,
                Case.GENITIVE,
                "Касперский",
            )
            == "Касперского"
        )

    @pytest.mark.parametrize(
        "case_to_use",
        [
            Case.GENITIVE,
            Case.DATIVE,
            Case.ACCUSATIVE,
            Case.INSTRUMENTAL,
            Case.PREPOSITIONAL,
        ],
    )
    def test_gremitskih_is_indeclinable_in_all_cases(self, maker, case_to_use):
        # Reported in #8 as inflecting to 'Гремитскиха' — could not be
        # reproduced. Russian -их surnames (archaic genitive plural form)
        # are conventionally indeclinable for both genders in all cases.
        # Locked in across every case so accidental regression is caught
        # immediately.
        assert (
            maker.make(
                NamePart.LASTNAME,
                Gender.MALE,
                case_to_use,
                "Гремитских",
            )
            == "Гремитских"
        )

    @pytest.mark.parametrize(
        "lastname",
        [
            "Чёрных",
            "Седых",
            "Коротких",
        ],
    )
    def test_other_indeclinable_ih_surnames(self, maker, lastname):
        # Sibling indeclinable -их surnames; if Гремитских ever regresses,
        # one of these probably will too. Locked in as a small regression
        # cohort.
        assert (
            maker.make(
                NamePart.LASTNAME,
                Gender.MALE,
                Case.GENITIVE,
                lastname,
            )
            == lastname
        )

    def test_olga_female_firstname_genitive(self, maker):
        # Reported in #8 as 'Ольгы' — could not be reproduced (maintainer
        # confirmed, and verified empirically here against both bundled
        # and upstream rules). The expected genitive is 'Ольги': after
        # the consonant 'г', Russian spelling rules require 'и' rather
        # than 'ы'. Locked in to catch any future rule-engine regression
        # that might break the consonant-ending rule.
        assert (
            maker.make(
                NamePart.FIRSTNAME,
                Gender.FEMALE,
                Case.GENITIVE,
                "Ольга",
            )
            == "Ольги"
        )
