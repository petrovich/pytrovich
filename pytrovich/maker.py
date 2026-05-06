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

    def find_first_match(self, name: str, gender_label: str) -> Optional[Rule]:
        """
        Return the Rule with the lowest registration-order index that
        (a) has a test value matching as a suffix of *name* and
        (b) has gender == gender_label or gender == 'androgynous'.
        Returns None if no such rule exists.
        """
        best_index = None
        rules = self._rules
        for index in self._trie.find_all_matches(name):
            if best_index is not None and index >= best_index:
                continue
            rule_gender = rules[index].gender
            if rule_gender == gender_label or rule_gender == _ANDROGYNOUS_LABEL:
                best_index = index
        return rules[best_index] if best_index is not None else None


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
        exception_indices[part_enum] = _RuleSuffixIndex(name_bean.exceptions if name_bean else None)
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

    def make(self, name_part: NamePart, gender: Gender, case_to_use: Case, original_name: str) -> str:
        """
        Inflect *original_name* into the requested grammatical case.

        :param name_part: which part of the anthroponym we are dealing
            with — first name, last name (surname), or middle name
            (patronymic). Different parts have different rule sets.
        :param gender: grammatical gender (MALE / FEMALE / ANDROGYNOUS)
            — needed because Russian inflection diverges by gender for
            most patterns.
        :param case_to_use: target case. Note that NOMINATIVE is not a
            member: input is assumed already nominative, and `make`
            transforms it into one of the five oblique cases.
        :param original_name: the name in nominative form. Lookup is
            case-insensitive (lowercased internally for matching), but
            the original casing is preserved in the output.
        :return: the inflected form, or the original input unchanged
            if no rule and no exception matched.
        """
        result = original_name

        # Lowercase for rule lookup. The rules data uses lowercase
        # throughout (suffix tests like 'ов', 'ская'; exception names
        # like 'пётр'), so without this an input like 'ИВАНОВ' would
        # fail the suffix match and silently return unchanged, and
        # 'Пётр' would miss the explicit Ё→Е alternation exception.
        # original_name is preserved for apply_mod2name below so the
        # output's case matches the input's: 'Иван' → 'Ивана', not
        # 'Иван' → 'ивана'. Mirrors the same treatment in
        # PetrovichGenderDetector.detect.
        lookup_name = original_name.lower()

        # name_part validation. Pre-fix this fell through to
        # MIDDLENAME silently; calls like make("FIRSTNAME", ...) or
        # make(None, ...) returned the input unchanged with no
        # warning. xfail tests in tests/test_known_issues.py pinned
        # this; with the explicit TypeError those flip to xpass and
        # the regular tests in TestPetrovichDeclinationMakerKnownIssues
        # become straight assertions.
        if name_part not in self._exception_indices:
            raise TypeError(
                f"name_part must be a NamePart enum value "
                f"(NamePart.FIRSTNAME, .LASTNAME, or .MIDDLENAME); "
                f"got {type(name_part).__name__}={name_part!r}"
            )
        gender_label = gender.str()
        exception_rule_bean: Rule = self._exception_indices[name_part].find_first_match(
            lookup_name, gender_label
        )
        suffix_rule_bean: Rule = self._suffix_indices[name_part].find_first_match(lookup_name, gender_label)

        if exception_rule_bean and exception_rule_bean.gender == gender.str():
            rule_to_use: Rule = exception_rule_bean
            logger.debug("using exception rule for %r: %s", original_name, rule_to_use)
        elif suffix_rule_bean and suffix_rule_bean.gender == gender.str():
            rule_to_use: Rule = suffix_rule_bean
            logger.debug("using suffix rule for %r: %s", original_name, rule_to_use)
        else:
            rule_to_use: Rule = exception_rule_bean if exception_rule_bean else suffix_rule_bean
            if rule_to_use is None:
                # No rule matched — name passes through unchanged. This is
                # frequently a silent miss (foreign names, typos); log so
                # callers running with DEBUG can spot why a name didn't
                # decline.
                logger.debug(
                    "no rule matched for %r (name_part=%s, gender=%s)",
                    original_name,
                    name_part,
                    gender,
                )

        if rule_to_use:
            mod2apply: str = rule_to_use.mods[case_to_use.value]
            result = PetrovichDeclinationMaker.apply_mod2name(mod2apply=mod2apply, name=original_name)
            logger.debug(
                "applied mod %r to %r → %r (case=%s)",
                mod2apply,
                original_name,
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
