import json
import logging
from functools import lru_cache
from os import path
from typing import Optional

from pytrovich.enums import Case, Gender, NamePart
from pytrovich.rule_models import Root, Rule
from pytrovich.suffix_trie import SuffixTrie

logger = logging.getLogger(__name__)

_ANDROGYNOUS_LABEL = Gender.ANDROGYNOUS.str()
_FEMALE_LABEL = Gender.FEMALE.str()


def _gender_matches(rule_gender: str, match_gender: str, known_gender: bool) -> bool:
    """
    petrovich-ruby's Case::Rule#match? gender filter
    (lib/petrovich/case/rule.rb).

    When the gender is *known* (explicitly supplied by the caller) the
    rule's gender must equal it exactly — in particular, androgynous
    rules do NOT apply to a known male/female name on the first pass;
    they are only reachable through the androgynous fallback pass in
    _inflect_piece.

    When the gender was *detected* (known_gender=False) the filter is
    asymmetric: female rules apply only to female targets, and
    non-female (male or androgynous) rules apply only to non-female
    targets.
    """
    if known_gender:
        return rule_gender == match_gender
    if rule_gender != _FEMALE_LABEL and match_gender == _FEMALE_LABEL:
        return False
    if rule_gender == _FEMALE_LABEL and match_gender != _FEMALE_LABEL:
        return False
    return True


class _RuleSuffixIndex:
    """
    Wraps a SuffixTrie + the original ordered rule list to implement
    'find the first rule (by registration order) whose .test contains
    a suffix of *name* and whose .gender is compatible with the
    requested gender'.

    Two trie inserts share a hash-tree path when their suffixes share
    a tail (e.g. -ов and -нов collapse on the trailing 'в'), which is
    where the algorithmic win over the previous linear scan comes
    from.
    """

    __slots__ = ("_rules", "_trie")

    def __init__(self, rules):
        self._rules = list(rules) if rules else []
        self._trie = SuffixTrie()
        for index, rule in enumerate(self._rules):
            for test in rule.test:
                self._trie.insert(test, index)

    def find_first_match(self, name: str, gender_label: str, known_gender: bool) -> Optional[Rule]:
        """
        Return the Rule with the lowest registration-order index that
        (a) has a test value matching as a suffix of *name* and
        (b) passes the Ruby gender filter for *gender_label* /
            *known_gender* (see _gender_matches).
        Returns None if no such rule exists.
        """
        best_index = None
        rules = self._rules
        for index in self._trie.find_all_matches(name):
            if best_index is not None and index >= best_index:
                continue
            if _gender_matches(rules[index].gender, gender_label, known_gender):
                best_index = index
        return rules[best_index] if best_index is not None else None


class _RuleExactIndex:
    """
    Whole-word lookup for *exception* rules.

    petrovich-ruby anchors exception tests at both ends (the regexp it
    builds is ``^лев$``), so the first-name exception ``лев`` never
    fires for Королев, and the 2024-rules exception ``алия`` never
    fires for Наталия. Matching exceptions through the SuffixTrie (as
    suffixes) reproduced exactly those mis-fires — e.g. Ельцин hit the
    lastname exception ``цин`` and declined to Ельцином instead of
    Ельциным.
    """

    __slots__ = ("_rules", "_by_word")

    def __init__(self, rules):
        self._rules = list(rules) if rules else []
        self._by_word = {}
        for index, rule in enumerate(self._rules):
            for test in rule.test:
                self._by_word.setdefault(test, []).append(index)

    def find_first_match(self, name: str, gender_label: str, known_gender: bool) -> Optional[Rule]:
        """
        Same contract as _RuleSuffixIndex.find_first_match, except a
        rule's test must equal *name* exactly (whole-word match).
        """
        for index in self._by_word.get(name, ()):
            rule = self._rules[index]
            if _gender_matches(rule.gender, gender_label, known_gender):
                return rule
        return None


@lru_cache(maxsize=8)
def _load_and_index_rules(path_to_rules_file: str):
    """
    Module-level cache for the parsed rules tree + the per-name-part
    suffix indices. Keyed by file path. Both the JSON parse and the
    six SuffixTrie builds happen exactly once per unique path,
    regardless of how many PetrovichDeclinationMaker instances are
    constructed against it. The cached objects are read-only after
    construction so sharing across instances is safe.

    Returns (root, exception_indices, suffix_indices).
    """
    with open(path_to_rules_file, encoding="utf-8") as fp:
        root = Root.parse(json.load(fp))
    exception_indices = {}
    suffix_indices = {}
    for part_attr, part_enum in (
        ("firstname", NamePart.FIRSTNAME),
        ("lastname", NamePart.LASTNAME),
        ("middlename", NamePart.MIDDLENAME),
    ):
        name_bean = getattr(root, part_attr)
        exception_indices[part_enum] = _RuleExactIndex(name_bean.exceptions if name_bean else None)
        suffix_indices[part_enum] = _RuleSuffixIndex(name_bean.suffixes if name_bean else None)
    return root, exception_indices, suffix_indices


class PetrovichDeclinationMaker:
    DEFAULT_PATH_TO_RULES_FILE = path.join(path.dirname(__file__), "petrovich-rules", "rules.json")
    MODS_KEEP_IT_ALL_SYMBOL = "."
    MODS_REMOVE_LETTER_SYMBOL = "-"

    def __init__(self, path_to_rules_file: str = DEFAULT_PATH_TO_RULES_FILE):
        try:
            (
                self._root_rules_bean,
                self._exception_indices,
                self._suffix_indices,
            ) = _load_and_index_rules(path_to_rules_file)
            logger.debug("loaded declination rules from %s", path_to_rules_file)
        except FileNotFoundError as e:
            raise RuntimeError(
                f"pytrovich rules file not found at {path_to_rules_file!r}. "
                f"If you are running from a source checkout, run "
                f"`git submodule update --init --recursive`. If installed "
                f"from PyPI, try reinstalling pytrovich."
            ) from e
        except (json.JSONDecodeError, KeyError) as e:
            raise RuntimeError(
                f"pytrovich rules file at {path_to_rules_file!r} is "
                f"malformed: {e}. If installed from PyPI, try reinstalling; "
                f"if you are pointing at a custom rules file, regenerate it "
                f"from petrovich-rules upstream."
            ) from e

    def make(
        self,
        name_part: NamePart,
        gender: Gender,
        case_to_use: Case,
        original_name: str,
        known_gender: bool = True,
    ) -> str:
        """
        Inflect *original_name* into the requested grammatical case.

        :param name_part: which part of the anthroponym we are dealing
            with — first name, last name (surname), or middle name
            (patronymic). Different parts have different rule sets.
        :param gender: grammatical gender (MALE / FEMALE / ANDROGYNOUS)
            — needed because Russian inflection diverges by gender for
            most patterns.
        :param case_to_use: target case. NOMINATIVE is the identity
            transformation (returns the input as-is) so callers can
            iterate over all six members of `Case` uniformly when
            generating a full declension table — same convention as
            petrovich-ruby.
        :param original_name: the name in nominative form. Lookup is
            case-insensitive (lowercased internally for matching), but
            the original casing is preserved in the output. Hyphenated
            double names (Салтыков-Щедрин, Анна-Мария) are split and
            each component is inflected with its own rule, matching
            petrovich-ruby's Inflector#inflect.
        :param known_gender: True (default) when *gender* is an
            explicit fact supplied by the caller; pass False when it
            came out of PetrovichGenderDetector. Mirrors
            petrovich-ruby's known_gender? flag: a known gender
            restricts rules to that exact gender, a detected one uses
            the looser female / non-female filter. Either way it
            applies only to the final hyphen-separated component.
        :return: the inflected form, or the original input unchanged
            if no rule and no exception matched.
        """
        # name_part validation runs before any case-based dispatch so
        # buggy callers get a TypeError regardless of which case they
        # asked for. Putting this after the NOMINATIVE short-circuit
        # would silently accept a string-or-None name_part whenever
        # the caller happened to ask for nominative — exactly the kind
        # of intermittent fall-through this validation exists to
        # prevent.
        if name_part not in self._exception_indices:
            raise TypeError(
                f"name_part must be a NamePart enum value "
                f"(NamePart.FIRSTNAME, .LASTNAME, or .MIDDLENAME); "
                f"got {type(name_part).__name__}={name_part!r}"
            )

        # Nominative is the identity transformation — input is already
        # in nominative form by API contract. Short-circuit before any
        # rule lookup so we never index mods[5] (mods arrays are
        # 5-element, indexed by Case.GENITIVE .. .PREPOSITIONAL).
        if case_to_use == Case.NOMINATIVE:
            return original_name

        # petrovich-ruby splits double (hyphenated) names and inflects
        # each component with its own rule — Салтыков-Щедрин declines
        # on both sides (Салтыкову-Щедрину), and the indeclinable
        # exception Бонч still holds in Бонч-Бруевич. A known gender
        # counts as known only for the final component, mirroring
        # Petrovich::Inflector#inflect.
        pieces = original_name.split("-")
        last_index = len(pieces) - 1
        return "-".join(
            self._inflect_piece(
                name_part,
                gender,
                case_to_use,
                piece,
                known_gender and index == last_index,
            )
            for index, piece in enumerate(pieces)
        )

    def _inflect_piece(
        self,
        name_part: NamePart,
        gender: Gender,
        case_to_use: Case,
        piece: str,
        known_gender: bool,
    ) -> str:
        """
        Inflect one hyphen-free component of a name.

        Rule resolution follows petrovich-ruby's RuleSet#find_case_rule:
        the combined rule list is exceptions (in file order) followed
        by suffixes (in file order); the first rule that passes the
        gender filter and whose test matches wins. Exceptions match the
        whole word, suffixes match the ending. If nothing matched, a
        second pass runs with an androgynous, not-known gender — which,
        per _gender_matches, admits male and androgynous rules but not
        female ones. Because every exception precedes every suffix in
        the combined order, 'first match over the combined list' is
        exactly 'exception match if any, else suffix match'.
        """
        # Lowercase for rule lookup. The rules data uses lowercase
        # throughout (suffix tests like 'ов', 'ская'; exception names
        # like 'пётр'), so without this an input like 'ИВАНОВ' would
        # fail the suffix match and silently return unchanged, and
        # 'Пётр' would miss the explicit Ё→Е alternation exception.
        # *piece* keeps its original casing for apply_mod2name below so
        # the output's case matches the input's: 'Иван' → 'Ивана', not
        # 'Иван' → 'ивана'. Mirrors the same treatment in
        # PetrovichGenderDetector.detect.
        lookup_name = piece.lower()
        gender_label = gender.str()

        rule_to_use: Optional[Rule] = (
            self._exception_indices[name_part].find_first_match(lookup_name, gender_label, known_gender)
            or self._suffix_indices[name_part].find_first_match(lookup_name, gender_label, known_gender)
            or self._exception_indices[name_part].find_first_match(lookup_name, _ANDROGYNOUS_LABEL, False)
            or self._suffix_indices[name_part].find_first_match(lookup_name, _ANDROGYNOUS_LABEL, False)
        )

        if rule_to_use is None:
            # No rule matched — the component passes through unchanged.
            # This is frequently a silent miss (foreign names, typos);
            # log so callers running with DEBUG can spot why a name
            # didn't decline.
            logger.debug(
                "no rule matched for %r (name_part=%s, gender=%s)",
                piece,
                name_part,
                gender,
            )
            return piece

        logger.debug(
            "selected rule for %r: gender=%s, test=%s",
            piece,
            rule_to_use.gender,
            rule_to_use.test,
        )
        mod2apply: str = rule_to_use.mods[case_to_use]
        result = PetrovichDeclinationMaker.apply_mod2name(mod2apply=mod2apply, name=piece)
        logger.debug(
            "applied mod %r to %r → %r (case=%s)",
            mod2apply,
            piece,
            result,
            case_to_use,
        )
        return result

    @staticmethod
    def apply_mod2name(mod2apply: str, name: str) -> str:
        # Mod-string format from petrovich-rules: a "." means keep
        # the name as-is; otherwise leading "-" characters are
        # remove-last-letter markers, and anything after them is the
        # suffix to append. Examples seen in rules.json:
        #   "."        → keep
        #   "а"        → name + "а"
        #   "-я"       → name[:-1] + "я"
        #   "--ой"     → name[:-2] + "ой"
        #   "---етра"  → name[:-3] + "етра"
        # Verified against the full rules data: every '-' in every
        # mod is leading. The previous character-by-character loop
        # was equivalent but harder to read.
        if mod2apply == PetrovichDeclinationMaker.MODS_KEEP_IT_ALL_SYMBOL:
            return name
        n_remove = mod2apply.count(PetrovichDeclinationMaker.MODS_REMOVE_LETTER_SYMBOL)
        suffix = mod2apply[n_remove:]
        return (name[:-n_remove] if n_remove else name) + suffix
