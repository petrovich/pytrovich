import json
import logging
from functools import lru_cache
from os import path

from pytrovich.enums import Gender
from pytrovich.gender_models import Name, Root
from pytrovich.suffix_trie import SuffixTrie

logger = logging.getLogger(__name__)


class _GenderSuffixIndex:
    """
    Combines all male / female / androgynous suffix patterns for one
    name part into a single SuffixTrie tagged with the resulting
    Gender. Insertion order is androgynous → male → female, matching
    petrovich-ruby's GENDERS constant, so that when the same suffix
    string appears under two genders the tie resolves the same way the
    Ruby implementation's stable ordering does.
    """

    __slots__ = ("_trie",)

    def __init__(self, name_obj):
        self._trie = SuffixTrie()
        suffixes = name_obj.suffixes if name_obj is not None else None
        if suffixes is not None:
            for s in suffixes.andro or ():
                self._trie.insert(s, Gender.ANDROGYNOUS)
            for s in suffixes.male or ():
                self._trie.insert(s, Gender.MALE)
            for s in suffixes.female or ():
                self._trie.insert(s, Gender.FEMALE)

    def detect_longest(self, str_name: str):
        """
        Gender of the LONGEST suffix matching *str_name*, or None.
        petrovich-ruby's find_gender_rule sorts suffix rules by
        descending length and takes the first match — i.e. the longest
        matching suffix decides the gender.
        """
        return self._trie.find_longest_match(str_name)


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
    def _exception_gender(name: Name, str_name: str):
        """
        Exact (whole-word) exception lookup for one hyphen-free name
        component. Returns a Gender or None.

        petrovich-ruby builds a hash keyed by the exception string,
        filled in GENDERS order (androgynous, male, female), so for a
        string listed under more than one gender the LAST write wins.
        Checking female → male → androgynous here is equivalent.
        """
        if name is None or not name.exceptions:
            return None
        exceptions = name.exceptions
        if exceptions.female and str_name in exceptions.female:
            return Gender.FEMALE
        if exceptions.male and str_name in exceptions.male:
            return Gender.MALE
        if exceptions.andro and str_name in exceptions.andro:
            return Gender.ANDROGYNOUS
        return None

    def _detect_part(self, part_key: str, value: str) -> Gender:
        """
        Gender contributed by one whole name part, which may be
        hyphenated. As in petrovich-ruby, each hyphen-separated
        component is resolved independently (exact exception first,
        then longest matching suffix) and the LAST component's result
        is taken; a component with no match counts as ANDROGYNOUS.
        """
        name_bean = getattr(self._root_rules_bean, part_key)
        index = self._suffix_indices[part_key]
        result = Gender.ANDROGYNOUS
        for component in value.split("-"):
            gender = self._exception_gender(name_bean, component)
            if gender is None:
                gender = index.detect_longest(component)
            result = gender if gender is not None else Gender.ANDROGYNOUS
        return result

    def detect(self, firstname=None, lastname=None, middlename=None):
        """
        Predict the grammatical gender of the supplied name parts.

        At least one of the three keyword arguments must be non-empty.
        When more than one is given the parts cross-check each other,
        following petrovich-ruby's Petrovich::Gender: a confident
        middlename answer wins outright (patronymics are
        gender-specific by construction); otherwise a definite
        firstname/lastname gender beats an ANDROGYNOUS one. A genuine
        male-vs-female conflict logs a WARNING and returns
        ANDROGYNOUS (where the Ruby reference returns nil).
        Hyphenated components are resolved independently and the last
        component decides, again as in the Ruby reference.

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

        per_part = {}
        # Insertion order matches petrovich-ruby's Petrovich::Gender:
        # lastname, firstname, middlename.
        if lastname:
            per_part["lastname"] = self._detect_part("lastname", lastname)
        if firstname:
            per_part["firstname"] = self._detect_part("firstname", firstname)
        if middlename:
            per_part["middlename"] = self._detect_part("middlename", middlename)
        logger.debug("per-part genders: %s", per_part)

        if not per_part:
            # Only empty strings were supplied — nothing to match.
            # Per the canonical Ruby reference implementation
            # (Petrovich.detect_gender('блаблабла') => :androgynous,
            # documented at rubydoc.info/gems/petrovich), the contract
            # is to return ANDROGYNOUS rather than raise.
            logger.debug(
                "no rule matched for firstname=%r lastname=%r middlename=%r — returning ANDROGYNOUS",
                firstname,
                lastname,
                middlename,
            )
            return Gender.ANDROGYNOUS

        middlename_gender = per_part.get("middlename")
        if middlename_gender is not None and middlename_gender != Gender.ANDROGYNOUS:
            # Middlename is the strongest signal: Russian patronymics
            # are gender-specific by construction (Иванович vs
            # Ивановна). A definite middlename answer wins outright.
            return middlename_gender

        distinct = set(per_part.values())
        firstname_gender = per_part.get("firstname")
        lastname_gender = per_part.get("lastname")
        if len(distinct) > 1:
            # A definite firstname/lastname beats an ANDROGYNOUS
            # counterpart (Саша Иванов → MALE). Note `x == ANDROGYNOUS`
            # is False when x is None (part not supplied), which is
            # exactly the guard petrovich-ruby's nil gets for free.
            if (
                firstname_gender is not None
                and firstname_gender != Gender.ANDROGYNOUS
                and lastname_gender == Gender.ANDROGYNOUS
            ):
                return firstname_gender
            if (
                lastname_gender is not None
                and lastname_gender != Gender.ANDROGYNOUS
                and firstname_gender == Gender.ANDROGYNOUS
            ):
                return lastname_gender

        if len(distinct) == 1:
            return next(iter(distinct))

        # Parts disagree with no androgynous side to defer to (e.g. a
        # female-looking firstname against a male-looking lastname).
        # petrovich-ruby returns nil here; pytrovich's contract is a
        # total function, so map that to ANDROGYNOUS — the same
        # totalization Issue #6 established for the no-match case.
        logger.warning(
            "gender prediction ambiguous for firstname=%r lastname=%r middlename=%r — per-part: %s",
            firstname,
            lastname,
            middlename,
            per_part,
        )
        return Gender.ANDROGYNOUS


if __name__ == "__main__":
    detector = PetrovichGenderDetector()
    print(detector.detect(firstname="Иван", lastname="Голубцов"))
    print(detector.detect(firstname="Арзу", middlename="Лутфияр кызы"))
