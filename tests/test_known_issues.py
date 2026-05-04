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

  * Issue #2 — Hyphenated lastname support
    https://github.com/petrovich/pytrovich/issues/2

  * Issue #6 — PetrovichGenderDetector.detect crashes with StopIteration
    on unknown names instead of returning Gender.ANDROGYNOUS
    (referenced as the existing xfail in test_detector.py:16)

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

    Current behavior (verified on master at the time of writing): the
    suffix rule is applied once to the whole hyphenated string, so only
    the trailing component looks inflected. For "Петров-Водкин" in the
    genitive case, the library returns "Петров-Водкина" instead of the
    expected "Петрова-Водкина".

    The tests below split into two parametrized groups:

      * "simple" hyphenated names from the issue body — naive
        split-and-inflect would yield correct output. The expected value
        is computed by inflecting each part through the maker
        individually, so the assertion does not require the test author
        to be a Russian-morphology expert.

      * "exception" cases the issue calls out as nasty. For example,
        "Бонч" is conventionally indeclinable, so the linguistically
        correct genitive of "Бонч-Бруевич" is "Бонч-Бруевича" — *not*
        the "Бонча-Бруевича" that naive split-and-inflect produces.
        These tests assert the linguistically-correct outcome and will
        require both a hyphen-splitting fix AND rules-data updates
        (additional indeclinable exceptions) to pass.
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
    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Issue #2: hyphenated lastnames are not split before the "
            "suffix rule is applied; only the trailing component looks "
            "inflected. The expected behavior is the 'naive' split-and-"
            "inflect-each from the issue body."
        ),
    )
    def test_simple_hyphenated_inflects_each_part(
        self,
        maker,
        lastname,
        case_to_use,
    ):
        # The library already knows how to inflect the individual parts
        # of these names. The bug is purely in not splitting on hyphens.
        # Compute the expected output by running each part through the
        # library separately and rejoining — this is the exact "naive
        # code" approach the issue describes.
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
        # Subtle case: this test is *not* marked xfail. The library
        # currently produces the linguistically correct output for these
        # names — but for the wrong reason. Because the bug only inflects
        # the trailing component, and "Бонч" is conventionally
        # indeclinable in Russian (so only the trailing component
        # *should* inflect), the buggy code coincidentally matches the
        # correct grammar.
        #
        # The value of this test is forward-looking: when a naive
        # hyphen-splitting fix for Issue #2 lands without an accompanying
        # "Бонч is indeclinable" rules-data exception, the output will
        # change to "Бонча-Бруевича" (wrong) and this assertion will
        # fail, alerting the maintainer that the rules-data side of the
        # issue is still pending.
        actual = maker.make(NamePart.LASTNAME, gender, case_to_use, lastname)
        assert actual == expected


# ---------------------------------------------------------------------------
# Issue #6 — Unknown name should return Gender.ANDROGYNOUS, not crash
# ---------------------------------------------------------------------------


class TestIssue6UnknownNameReturnsAndrogynous:
    """
    Issue #6 (referenced as the xfail row in test_detector.py:16-19).

    The contract documented in the petrovich-js reference implementation
    README is:

        petrovich.detect_gender('Блаблабла') // вернет 'androgynous'

    https://github.com/petrovich/petrovich-js/blob/master/README.md

    pytrovich's PetrovichGenderDetector.detect should match this contract:
    when no rule and no exception matches the input, the result must be
    Gender.ANDROGYNOUS. Currently detect() raises StopIteration at
    detector.py:97 because next(iter(joined_set)) is called on an empty
    set inside the else-branch, with no special-case for the no-match
    situation.

    The tests below expand the existing single-row xfail in
    test_detector.py to cover all three name-part keyword arguments and
    a broader set of inputs:

      * 'Блаблабла' — the canonical nonsense name from petrovich-js.
      * 'Саша' — a legitimate Russian androgynous diminutive (short for
        either Александр or Александра); a real-world failure mode.
      * '' — empty string; bypasses the None-only assert at
        detector.py:63 and reaches the same crash.
    """

    UNRECOGNIZED_NAMES = [
        "Блаблабла",  # canonical nonsense from petrovich-js README
        "Саша",  # legitimate androgynous diminutive
        "",  # empty string — separate input-validation gap
    ]

    @pytest.mark.parametrize("name", UNRECOGNIZED_NAMES)
    @pytest.mark.parametrize("name_part_kwarg", ["firstname", "lastname", "middlename"])
    @pytest.mark.xfail(
        strict=True,
        raises=StopIteration,
        reason=(
            "Issue #6: PetrovichGenderDetector.detect raises "
            "StopIteration on unrecognized names instead of returning "
            "Gender.ANDROGYNOUS as documented in the petrovich-js "
            "reference implementation."
        ),
    )
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
