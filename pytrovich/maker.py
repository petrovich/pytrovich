import json
import logging
from os import path

from pytrovich.enums import Case, Gender, NamePart
from pytrovich.rule_models import Name, Root, Rule

logger = logging.getLogger(__name__)


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

        exception_rule_bean: Rule = PetrovichDeclinationMaker.find_in_rule_bean_list(
            name_bean.exceptions, gender, original_name
        )
        suffix_rule_bean: Rule = PetrovichDeclinationMaker.find_in_rule_bean_list(
            name_bean.suffixes, gender, original_name
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
