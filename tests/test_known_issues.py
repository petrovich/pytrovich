import pytest

from pytrovich.detector import PetrovichGenderDetector
from pytrovich.enums import Case, Gender, NamePart
from pytrovich.maker import PetrovichDeclinationMaker


@pytest.fixture(scope='module')
def maker() -> PetrovichDeclinationMaker:
    return PetrovichDeclinationMaker()


@pytest.fixture(scope='module')
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
        'Петров-Водкин',
        'Бестужев-Марлинский',
    ]

    NASTY_EXCEPTIONS_FROM_ISSUE = [
        # (lastname, gender, case, expected_correct_output)
        # Бонч is foreign-origin (German "Bontsch") and conventionally
        # indeclinable in Russian — only the second part inflects.
        ('Бонч-Бруевич', Gender.MALE, Case.GENITIVE, 'Бонч-Бруевича'),
        ('Бонч-Бруевич', Gender.MALE, Case.INSTRUMENTAL, 'Бонч-Бруевичем'),
    ]

    @pytest.mark.parametrize('case_to_use', [
        Case.GENITIVE,
        Case.DATIVE,
        Case.ACCUSATIVE,
        Case.INSTRUMENTAL,
        Case.PREPOSITIONAL,
    ])
    @pytest.mark.parametrize('lastname', SIMPLE_HYPHENATED_NAMES_FROM_ISSUE)
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
            self, maker, lastname, case_to_use,
    ):
        # The library already knows how to inflect the individual parts
        # of these names. The bug is purely in not splitting on hyphens.
        # Compute the expected output by running each part through the
        # library separately and rejoining — this is the exact "naive
        # code" approach the issue describes.
        parts = lastname.split('-')
        expected = '-'.join(
            maker.make(NamePart.LASTNAME, Gender.MALE, case_to_use, p)
            for p in parts
        )
        actual = maker.make(NamePart.LASTNAME, Gender.MALE, case_to_use, lastname)
        assert actual == expected

    @pytest.mark.parametrize(
        'lastname,gender,case_to_use,expected',
        NASTY_EXCEPTIONS_FROM_ISSUE,
    )
    def test_hyphenated_with_indeclinable_first_part(
            self, maker, lastname, gender, case_to_use, expected,
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
        'Блаблабла',  # canonical nonsense from petrovich-js README
        'Саша',  # legitimate androgynous diminutive
        '',  # empty string — separate input-validation gap
    ]

    @pytest.mark.parametrize('name', UNRECOGNIZED_NAMES)
    @pytest.mark.parametrize('name_part_kwarg', ['firstname', 'lastname', 'middlename'])
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
            self, detector, name_part_kwarg, name,
    ):
        result = detector.detect(**{name_part_kwarg: name})
        assert result == Gender.ANDROGYNOUS
