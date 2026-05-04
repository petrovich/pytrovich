import json
import logging
from os import path

from pytrovich.enums import Gender
from pytrovich.gender_models import Name, Root

logger = logging.getLogger(__name__)


class PetrovichGenderDetector:
    DEFAULT_PATH_TO_RULES_FILE = path.join(path.dirname(__file__), "petrovich-rules", "gender.json")

    def __init__(self, path_to_rules_file: str = DEFAULT_PATH_TO_RULES_FILE):
        try:
            with open(path_to_rules_file, encoding="utf-8") as fp:
                self._root_rules_bean = Root.parse(json.load(fp=fp)["gender"])
            logger.debug("loaded gender rules from %s", path_to_rules_file)
        except FileNotFoundError as e:
            raise RuntimeError(
                f"pytrovich gender rules file not found at "
                f"{path_to_rules_file!r}. If you are running from a source "
                f"checkout, run `git submodule update --init --recursive`. "
                f"If installed from PyPI, try reinstalling pytrovich."
            ) from e
        except (json.JSONDecodeError, KeyError) as e:
            raise RuntimeError(
                f"pytrovich gender rules file at {path_to_rules_file!r} is "
                f"malformed: {e}. If installed from PyPI, try reinstalling; "
                f"if you are pointing at a custom file, regenerate it from "
                f"petrovich-rules upstream."
            ) from e

    @staticmethod
    def _check_against_exceptions(name: Name, str_name: str) -> set:
        results = []

        if name.exceptions and name.exceptions.male and str_name in name.exceptions.male:
            results.append(Gender.MALE)
        if name.exceptions and name.exceptions.female and str_name in name.exceptions.female:
            results.append(Gender.FEMALE)
        if name.exceptions and name.exceptions.andro and str_name in name.exceptions.andro:
            results.append(Gender.ANDROGYNOUS)
        return set(results)

    @staticmethod
    def _check_again_suffixes(name: Name, str_name: str) -> set:

        results = []

        if name.suffixes and name.suffixes.male:
            for possible_suffix in name.suffixes.male:
                if str_name.endswith(possible_suffix):
                    results.append(Gender.MALE)
                    break

        if name.suffixes and name.suffixes.female:
            for possible_suffix in name.suffixes.female:
                if str_name.endswith(possible_suffix):
                    results.append(Gender.FEMALE)
                    break

        if name.suffixes and name.suffixes.andro:
            for possible_suffix in name.suffixes.andro:
                if str_name.endswith(possible_suffix):
                    results.append(Gender.ANDROGYNOUS)
                    break

        return set(results)

    def detect(self, firstname=None, lastname=None, middlename=None):

        assert not (firstname is None and lastname is None and middlename is None), (
            "At least one part of the name should be given."
        )

        logger.debug(
            "detect(firstname=%r, lastname=%r, middlename=%r)",
            firstname,
            lastname,
            middlename,
        )

        # Normalize case for rule lookup. The rules data uses lowercase
        # throughout — both exception lists ('савва', 'иона', ...) and
        # suffix tests ('ов', 'ская', 'а', ...). Without normalization
        # an input like 'Савва' misses the exception list and an input
        # like 'ИВАНОВ' fails str.endswith('ов'). The Ruby reference
        # implementation rolls its own Cyrillic downcase
        # (lib/petrovich/unicode.rb) for the same reason; Python's
        # str.lower() handles the full Cyrillic alphabet (including Ё)
        # correctly out of the box.
        if firstname is not None:
            firstname = firstname.lower()
        if lastname is not None:
            lastname = lastname.lower()
        if middlename is not None:
            middlename = middlename.lower()

        results_middlename, results_firstname, results_lastname = set([]), set([]), set([])

        if middlename:
            results_middlename.update(
                self._check_against_exceptions(self._root_rules_bean.middlename, middlename)
            )
            results_middlename.update(
                self._check_again_suffixes(self._root_rules_bean.middlename, middlename)
            )
            logger.debug("middlename %r matched %s", middlename, results_middlename)

            if len(results_middlename) > 0 and next(iter(results_middlename)) != Gender.ANDROGYNOUS:
                return next(iter(results_middlename))

        if firstname:
            results_firstname.update(
                self._check_against_exceptions(self._root_rules_bean.firstname, firstname)
            )
            results_firstname.update(self._check_again_suffixes(self._root_rules_bean.firstname, firstname))
            logger.debug("firstname %r matched %s", firstname, results_firstname)

        if lastname:
            results_lastname.update(self._check_against_exceptions(self._root_rules_bean.lastname, lastname))
            results_lastname.update(self._check_again_suffixes(self._root_rules_bean.lastname, lastname))
            logger.debug("lastname %r matched %s", lastname, results_lastname)

        if firstname and lastname:
            if results_firstname and results_lastname:
                fn, ln = next(iter(results_firstname)), next(iter(results_lastname))
                if fn != Gender.ANDROGYNOUS and ln == Gender.ANDROGYNOUS:
                    return fn
                if ln != Gender.ANDROGYNOUS and fn == Gender.ANDROGYNOUS:
                    return ln

        joined_set = results_firstname.union(results_middlename).union(results_lastname)

        if not joined_set:
            # No rule and no exception matched any of the supplied name
            # parts. Per the canonical Ruby reference implementation
            # (Petrovich.detect_gender('блаблабла') => :androgynous,
            # documented at rubydoc.info/gems/petrovich), the contract
            # is to return ANDROGYNOUS rather than raise. Previously
            # this path fell through to next(iter(empty_set)), which
            # raised StopIteration — Issue #6.
            logger.debug(
                "no rule matched for firstname=%r lastname=%r middlename=%r — returning ANDROGYNOUS",
                firstname,
                lastname,
                middlename,
            )
            return Gender.ANDROGYNOUS

        if len(joined_set) == 1:
            return next(iter(joined_set))

        # Multiple candidates from different name parts — the library
        # picks one (set iteration order — non-deterministic) but
        # warns so callers can recover or surface the ambiguity.
        logger.warning(
            "gender prediction ambiguous for firstname=%r lastname=%r middlename=%r — candidates: %s",
            firstname,
            lastname,
            middlename,
            joined_set,
        )
        return next(iter(joined_set))


if __name__ == "__main__":
    detector = PetrovichGenderDetector()
    print(detector.detect(firstname="Иван", lastname="Голубцов"))
    print(detector.detect(firstname="Арзу", middlename="Лутфияр кызы"))
