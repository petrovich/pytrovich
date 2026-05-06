import json
import logging
from functools import lru_cache
from os import path

from pytrovich.enums import Gender
from pytrovich.gender_models import Name, Root
from pytrovich.suffix_trie import SuffixTrie

logger = logging.getLogger(__name__)


def _pick(candidates):
    """
    Deterministically choose one Gender from a non-empty iterable of
    candidates. Genders are compared by their integer enum values
    (MALE=0, FEMALE=1, ANDROGYNOUS=2), so a definite gender always
    wins over ANDROGYNOUS — which matches the existing intent of the
    surrounding code in detect() and replaces the previous reliance
    on Python's randomized set iteration order. Tied definite
    genders fall back to MALE-before-FEMALE; that case only arises
    in the multi-candidate joined_set branch where one of the two is
    going to be wrong by definition, and the caller has already
    logged a WARNING about the ambiguity.
    """
    return min(candidates, key=lambda g: g.value)


class _GenderSuffixIndex:
    """
    Combines all male / female / androgynous suffix patterns for one
    name part into a single SuffixTrie tagged with the resulting
    Gender. One traversal yields the set of genders matched, replacing
    three separate linear scans (one per gender) in the previous
    implementation.
    """

    __slots__ = ("_trie",)

    def __init__(self, name_obj):
        self._trie = SuffixTrie()
        suffixes = name_obj.suffixes if name_obj is not None else None
        if suffixes is not None:
            for s in suffixes.male or ():
                self._trie.insert(s, Gender.MALE)
            for s in suffixes.female or ():
                self._trie.insert(s, Gender.FEMALE)
            for s in suffixes.andro or ():
                self._trie.insert(s, Gender.ANDROGYNOUS)

    def detect_genders(self, str_name: str) -> set:
        return set(self._trie.find_all_matches(str_name))


@lru_cache(maxsize=8)
def _load_and_index_gender_rules(path_to_rules_file: str):
    """
    Module-level cache for the parsed gender-rules tree + the per-
    name-part suffix indices. Same shape as the maker's loader: parse
    once per unique path, share across instances. Read-only after
    construction so sharing is safe.

    Returns (root, suffix_indices).
    """
    with open(path_to_rules_file, encoding="utf-8") as fp:
        root = Root.parse(json.load(fp)["gender"])
    suffix_indices = {
        "firstname": _GenderSuffixIndex(root.firstname),
        "lastname": _GenderSuffixIndex(root.lastname),
        "middlename": _GenderSuffixIndex(root.middlename),
    }
    return root, suffix_indices


class PetrovichGenderDetector:
    DEFAULT_PATH_TO_RULES_FILE = path.join(path.dirname(__file__), "petrovich-rules", "gender.json")

    def __init__(self, path_to_rules_file: str = DEFAULT_PATH_TO_RULES_FILE):
        try:
            self._root_rules_bean, self._suffix_indices = _load_and_index_gender_rules(path_to_rules_file)
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

    def detect(self, firstname=None, lastname=None, middlename=None):
        """
        Predict the grammatical gender of the supplied name parts.

        At least one of the three keyword arguments must be non-empty.
        When more than one is given the parts cross-check each other:
        a confident middlename answer wins outright (patronymics are
        gender-specific by construction); otherwise a definite
        firstname/lastname gender beats an ANDROGYNOUS one. Truly
        ambiguous combinations log a WARNING and return a
        deterministic best guess.

        :param firstname: first name (Иван, Анна, …). Optional.
        :param lastname: last name / surname (Иванов, Иванова, …). Optional.
        :param middlename: patronymic / middle name (Иванович,
            Ивановна, …). Optional.
        :return: Gender.MALE, Gender.FEMALE, or Gender.ANDROGYNOUS.
            ANDROGYNOUS is also the fallback when no rule matches —
            see Issue #6 / petrovich-ruby for the rationale.
        """
        if firstname is None and lastname is None and middlename is None:
            raise ValueError("at least one of firstname, lastname, middlename must be given")

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
            results_middlename.update(self._suffix_indices["middlename"].detect_genders(middlename))
            logger.debug("middlename %r matched %s", middlename, results_middlename)

            # Middlename is the strongest signal: Russian patronymics
            # are gender-specific by construction (Иванович vs
            # Ивановна). If matching produced any definite gender,
            # take it and stop. Previously this used next(iter(...))
            # twice and could mis-fire on ANDROGYNOUS even when a
            # definite match was also present, by picking ANDRO first.
            non_andro = results_middlename - {Gender.ANDROGYNOUS}
            if non_andro:
                return _pick(non_andro)

        if firstname:
            results_firstname.update(
                self._check_against_exceptions(self._root_rules_bean.firstname, firstname)
            )
            results_firstname.update(self._suffix_indices["firstname"].detect_genders(firstname))
            logger.debug("firstname %r matched %s", firstname, results_firstname)

        if lastname:
            results_lastname.update(self._check_against_exceptions(self._root_rules_bean.lastname, lastname))
            results_lastname.update(self._suffix_indices["lastname"].detect_genders(lastname))
            logger.debug("lastname %r matched %s", lastname, results_lastname)

        if firstname and lastname:
            if results_firstname and results_lastname:
                fn, ln = _pick(results_firstname), _pick(results_lastname)
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
            return _pick(joined_set)

        # Multiple candidates from different name parts — _pick
        # deterministically prefers a definite gender over
        # ANDROGYNOUS (and falls back to MALE-before-FEMALE when
        # both are definite, an inherently uncertain case the
        # caller can recover from via the WARNING below).
        logger.warning(
            "gender prediction ambiguous for firstname=%r lastname=%r middlename=%r — candidates: %s",
            firstname,
            lastname,
            middlename,
            joined_set,
        )
        return _pick(joined_set)


if __name__ == "__main__":
    detector = PetrovichGenderDetector()
    print(detector.detect(firstname="Иван", lastname="Голубцов"))
    print(detector.detect(firstname="Арзу", middlename="Лутфияр кызы"))
