import json
import logging
from os import path

from pytrovich.enums import Case, Gender, NamePart
from pytrovich.rule_models import Name, Root, Rule
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

    def find_first_match(self, name: str, gender_label: str):
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


class PetrovichDeclinationMaker:
    DEFAULT_PATH_TO_RULES_FILE = path.join(path.dirname(__file__), "petrovich-rules", "rules.json")
    MODS_KEEP_IT_ALL_SYMBOL = "."
    MODS_REMOVE_LETTER_SYMBOL = "-"

    def __init__(self, path_to_rules_file: str = DEFAULT_PATH_TO_RULES_FILE):
        try:
            with open(path_to_rules_file, encoding="utf-8") as fp:
                self._root_rules_bean = Root.parse(json.load(fp=fp))
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

        # Pre-build suffix tries for each (name_part, kind). Done once at
        # construction; per-call lookup is then O(L) in the matched
        # suffix length rather than O(n) in the rule count.
        self._exception_indices = {}
        self._suffix_indices = {}
        for part_attr, part_enum in (
            ("firstname", NamePart.FIRSTNAME),
            ("lastname", NamePart.LASTNAME),
            ("middlename", NamePart.MIDDLENAME),
        ):
            name_bean = getattr(self._root_rules_bean, part_attr)
            self._exception_indices[part_enum] = _RuleSuffixIndex(
                name_bean.exceptions if name_bean else None
            )
            self._suffix_indices[part_enum] = _RuleSuffixIndex(
                name_bean.suffixes if name_bean else None
            )

    def make(self, name_part: NamePart, gender: Gender, case_to_use: Case, original_name: str) -> str:

        result = original_name

        if name_part == NamePart.FIRSTNAME:
            name_bean: Name = self._root_rules_bean.firstname
        elif name_part == NamePart.LASTNAME:
            name_bean: Name = self._root_rules_bean.lastname
        elif name_part == NamePart.MIDDLENAME:
            name_bean: Name = self._root_rules_bean.middlename
        else:
            name_bean: Name = self._root_rules_bean.middlename

        # Index lookup is keyed by NamePart; the unknown-NamePart
        # else-branch above handed back middlename's name_bean, so
        # mirror that here for the index.
        index_part = name_part if name_part in self._exception_indices else NamePart.MIDDLENAME
        gender_label = gender.str()
        exception_rule_bean: Rule = self._exception_indices[index_part].find_first_match(
            original_name, gender_label
        )
        suffix_rule_bean: Rule = self._suffix_indices[index_part].find_first_match(
            original_name, gender_label
        )

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

        result = name

        # if modification is not needed
        if mod2apply != PetrovichDeclinationMaker.MODS_KEEP_IT_ALL_SYMBOL:
            # if modification is needed according to rules
            if PetrovichDeclinationMaker.MODS_REMOVE_LETTER_SYMBOL in mod2apply:
                for i in range(len(mod2apply)):
                    # if special character "-", removing the last letter
                    if mod2apply[i] == PetrovichDeclinationMaker.MODS_REMOVE_LETTER_SYMBOL:
                        result = result[0 : len(result) - 1]
                    # if not a special character "-", adding the rest of the modifier to the result
                    else:
                        result += mod2apply[i:]
                        break
            else:
                result = name + mod2apply

        return result

    @staticmethod
    def find_in_rule_bean_list(rule_bean_list: list, gender: Gender, original_name: str) -> Rule:

        result = None
        done = False

        if rule_bean_list is not None:
            # traversing all rules available
            for rule_bean in rule_bean_list:
                if done:
                    break
                # traversing all available checks for word ends
                for test in rule_bean.test:
                    # if match found
                    if original_name.endswith(test):
                        # if angrogynous OR gender match -- we're done, escaping both loops
                        if rule_bean.gender == Gender.ANDROGYNOUS.str() or rule_bean.gender == gender.str():
                            result = rule_bean
                            done = True
                            break
        return result
