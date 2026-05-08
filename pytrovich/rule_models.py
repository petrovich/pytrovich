"""
Data models for the inflection rules tree (rules.json).

The shape on disk:

    {
        "firstname": {"exceptions": [Rule, ...], "suffixes": [Rule, ...]},
        "lastname":  {"exceptions": [Rule, ...], "suffixes": [Rule, ...]},
        "middlename": {"exceptions": [Rule, ...], "suffixes": [Rule, ...]}
    }

Each Rule's `mods` field is a 5-element JSON array, one entry per
oblique case. The mapping between array position and Case enum
member is declared once below as ``_MODS_CASE_ORDER``; nothing else
in the codebase encodes that layout. Previously the maker did
``mods[case_to_use.value]``, which silently coupled JSON list
ordering to the integer values of the Case enum — a renumbering of
either side would have applied the wrong modifier with no error.
"""

from pytrovich.enums import Case

# The canonical ordering of oblique cases as laid out in
# petrovich-rules/rules.json's mods arrays. NOMINATIVE is absent
# because it is the identity transformation and the maker
# short-circuits before any mods lookup; if you change rules.json's
# layout, change this tuple to match (and only this tuple).
_MODS_CASE_ORDER = (
    Case.GENITIVE,
    Case.DATIVE,
    Case.ACCUSATIVE,
    Case.INSTRUMENTAL,
    Case.PREPOSITIONAL,
)


class Rule:
    def __init__(self, gender: str, mods, test: list):
        """
        :param gender: grammatical gender
        :param mods: modifications, one per oblique case. Accepted
            as either a positional list (the rules.json shape,
            ordered per ``_MODS_CASE_ORDER``) or a dict keyed by
            Case. Stored internally as a dict.
        :param test: search rules list (suffix patterns or full
            exception names, lowercase)
        """
        self.gender = gender
        self.test = test
        if isinstance(mods, dict):
            self.mods = dict(mods)
        else:
            # Positional list. Pair each element with its
            # canonical Case key. Tolerates short lists (some
            # unit tests do this) by leaving extra Case keys
            # unmapped — runtime callers always pass full-length
            # mods so this never bites in production.
            self.mods = dict(zip(_MODS_CASE_ORDER, mods))

    def serialize(self):
        # Emit the positional list shape that rules.json expects.
        # Missing entries become None; in real data this never
        # happens, but it keeps the round-trip honest in tests.
        return {
            "gender": self.gender,
            "mods": [self.mods.get(c) for c in _MODS_CASE_ORDER],
            "test": self.test,
        }

    @staticmethod
    def parse(o: dict):
        return Rule(gender=o["gender"], mods=o["mods"], test=o["test"])


class Name:
    def __init__(self, exceptions: list, suffixes: list):
        """
        :param exceptions: list(Rule):
        :param suffixes: list(Rule)
        """
        self.exceptions = exceptions
        self.suffixes = suffixes

    def serialize(self):
        return {
            "exceptions": [e.serialize() for e in self.exceptions],
            "suffixes": [s.serialize() for s in self.suffixes],
        }

    @staticmethod
    def parse(o: dict):
        return Name(
            exceptions=[Rule.parse(e) for e in o.get("exceptions", [])],
            suffixes=[Rule.parse(s) for s in o.get("suffixes", [])],
        )


class Root:
    def __init__(self, firstname, lastname, middlename):
        self.firstname = firstname
        self.lastname = lastname
        self.middlename = middlename

    def serialize(self):
        return {
            "firstname": self.firstname.serialize(),
            "lastname": self.lastname.serialize(),
            "middlename": self.middlename.serialize(),
        }

    @staticmethod
    def parse(a: dict):
        return Root(
            firstname=Name.parse(a["firstname"]),
            lastname=Name.parse(a["lastname"]),
            middlename=Name.parse(a["middlename"]),
        )
