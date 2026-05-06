"""
Tests for the model classes in pytrovich.rule_models and
pytrovich.gender_models.

These models are simple data containers: each class has an __init__,
a parse() classmethod (dict → instance), and a serialize() method
(instance → dict). The contract is that parse and serialize are
inverses — Rule.parse(rule.serialize()) yields an equivalent Rule.

Earlier versions of the suite never exercised serialize() at all,
so any regression there (a renamed field, a dropped key, a typed
value losing its type round-trip) would have shipped silently. The
roundtrip tests below pin the contract for both module families.
"""

import json

from pytrovich import gender_models, rule_models

# ----- pytrovich.rule_models -----------------------------------------------


class TestRuleModelsRule:
    def test_serialize_returns_all_three_fields(self):
        r = rule_models.Rule(gender="male", mods=["а", "у"], test=["ов"])
        assert r.serialize() == {"gender": "male", "mods": ["а", "у"], "test": ["ов"]}

    def test_parse_serialize_roundtrip(self):
        original = {"gender": "female", "mods": ["-ы", "-е"], "test": ["а"]}
        rule = rule_models.Rule.parse(original)
        assert rule.serialize() == original

    def test_serialize_is_json_serializable(self):
        # Practical sanity: the dict produced by serialize() must
        # survive json.dumps. The rules.json round-trip relies on
        # this implicitly via Root.parse, so an unhashable field type
        # creeping in would surface here.
        r = rule_models.Rule(gender="male", mods=["а"], test=["ов"])
        json.dumps(r.serialize())


class TestRuleModelsName:
    def test_parse_serialize_roundtrip_with_both(self):
        original = {
            "exceptions": [{"gender": "male", "mods": ["."] * 5, "test": ["лев"]}],
            "suffixes": [{"gender": "male", "mods": ["а"] * 5, "test": ["ов"]}],
        }
        name = rule_models.Name.parse(original)
        assert name.serialize() == original

    def test_parse_with_missing_keys_fills_empty_lists(self):
        # Name.parse() uses dict.get(key, []) for both; an input dict
        # with only one of the two keys present should round-trip with
        # the other materialized as an empty list. That's what current
        # rules.json relies on for parts that have no exceptions.
        partial = {"suffixes": [{"gender": "male", "mods": ["а"] * 5, "test": ["ов"]}]}
        name = rule_models.Name.parse(partial)
        assert name.serialize() == {**partial, "exceptions": []}


class TestRuleModelsRoot:
    def test_parse_serialize_roundtrip(self):
        original = {
            "firstname": {
                "exceptions": [],
                "suffixes": [{"gender": "male", "mods": ["а"] * 5, "test": ["н"]}],
            },
            "lastname": {
                "exceptions": [],
                "suffixes": [{"gender": "male", "mods": ["а"] * 5, "test": ["ов"]}],
            },
            "middlename": {
                "exceptions": [],
                "suffixes": [{"gender": "male", "mods": ["а"] * 5, "test": ["ович"]}],
            },
        }
        root = rule_models.Root.parse(original)
        assert root.serialize() == original


# ----- pytrovich.gender_models ---------------------------------------------


class TestGenderModelsRule:
    def test_serialize_emits_only_populated_groups(self):
        # gender_models.Rule has separate male/female/androgynous lists
        # and serialize() omits groups that are empty/None — the rules
        # JSON does the same, so missing keys are an authoritative
        # signal of "no entries", not a default value.
        r = gender_models.Rule(male=["сева"], female=None, androgynous=None)
        assert r.serialize() == {"male": {"сева"}}

    def test_serialize_emits_all_three_when_all_populated(self):
        r = gender_models.Rule(male=["абиба"], female=["судаба"], androgynous=["иона"])
        out = r.serialize()
        assert out == {
            "male": {"абиба"},
            "female": {"судаба"},
            "androgynous": {"иона"},
        }

    def test_parse_serialize_roundtrip(self):
        # Note: gender_models.Rule stores values as sets, so the input
        # list and the output set are equal-but-not-identical. We
        # compare against the set-shaped expected value.
        original = {
            "male": ["сева", "абиба"],
            "female": ["судаба"],
            "androgynous": ["иона"],
        }
        r = gender_models.Rule.parse(original)
        assert r.serialize() == {
            "male": {"сева", "абиба"},
            "female": {"судаба"},
            "androgynous": {"иона"},
        }


class TestGenderModelsName:
    def test_serialize_with_only_exceptions(self):
        rule = gender_models.Rule(male=["сева"], female=None, androgynous=None)
        name = gender_models.Name(exceptions=rule, suffixes=None)
        assert name.serialize() == {"exceptions": {"male": {"сева"}}}

    def test_serialize_with_both_present(self):
        ex = gender_models.Rule(male=["сева"], female=None, androgynous=None)
        suf = gender_models.Rule(male=None, female=["а"], androgynous=None)
        name = gender_models.Name(exceptions=ex, suffixes=suf)
        assert name.serialize() == {
            "exceptions": {"male": {"сева"}},
            "suffixes": {"female": {"а"}},
        }


class TestGenderModelsRoot:
    def _build_minimal_root(self) -> gender_models.Root:
        rule = gender_models.Rule(male=["петр"], female=None, androgynous=None)
        name = gender_models.Name(exceptions=rule, suffixes=None)
        return gender_models.Root(firstname=name, lastname=None, middlename=None)

    def test_serialize_emits_only_populated_parts(self):
        root = self._build_minimal_root()
        assert root.serialize() == {"firstname": {"exceptions": {"male": {"петр"}}}}

    def test_str_returns_serialized_form(self):
        # Root.__str__ exists for diagnostics — debugging the loaded
        # rules tree by `print(detector._root_rules_bean)` is useful
        # enough to keep, but it had no test exercising it.
        root = self._build_minimal_root()
        s = str(root)
        # Contains the expected key, in dict-repr form. Don't pin the
        # exact output (set ordering!), just the ingredients.
        assert "firstname" in s
        assert "exceptions" in s
        assert "петр" in s
