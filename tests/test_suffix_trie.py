"""
Unit tests for pytrovich.suffix_trie.SuffixTrie.

Pins the contract that PetrovichDeclinationMaker._RuleSuffixIndex and
PetrovichGenderDetector._GenderSuffixIndex rely on.
"""

import pytest

from pytrovich.suffix_trie import SuffixTrie


class TestSuffixTrieBasic:
    def test_empty_trie_returns_no_matches(self):
        t = SuffixTrie()
        assert list(t.find_all_matches("Иванов")) == []
        assert list(t.find_all_matches("")) == []

    def test_single_suffix_matches(self):
        t = SuffixTrie()
        t.insert("ов", 1)
        assert list(t.find_all_matches("Иванов")) == [1]

    def test_single_suffix_does_not_match_unrelated_text(self):
        t = SuffixTrie()
        t.insert("ов", 1)
        assert list(t.find_all_matches("Петрова")) == []

    def test_full_string_match_when_text_equals_suffix(self):
        t = SuffixTrie()
        t.insert("ов", 1)
        assert list(t.find_all_matches("ов")) == [1]

    def test_text_shorter_than_any_suffix(self):
        t = SuffixTrie()
        t.insert("ович", 1)
        assert list(t.find_all_matches("ва")) == []


class TestSuffixTrieMultipleMatches:
    def test_overlapping_suffixes_all_match(self):
        # "Иванов" ends with all three: -в, -ов, -нов
        t = SuffixTrie()
        t.insert("в", "v")
        t.insert("ов", "ov")
        t.insert("нов", "nov")
        assert set(t.find_all_matches("Иванов")) == {"v", "ov", "nov"}

    def test_non_overlapping_suffixes_only_matching_one_returned(self):
        t = SuffixTrie()
        t.insert("ов", 1)
        t.insert("ова", 2)
        t.insert("ская", 3)
        assert list(t.find_all_matches("Иванов")) == [1]
        assert list(t.find_all_matches("Иванова")) == [2]
        assert list(t.find_all_matches("Толстовская")) == [3]

    def test_duplicate_suffix_yields_in_insertion_order(self):
        # Two values registered under the same key must come back in
        # the order they were inserted — this is the contract that
        # _RuleSuffixIndex relies on for "first registered rule wins".
        t = SuffixTrie()
        t.insert("ов", "first")
        t.insert("ов", "second")
        t.insert("ов", "third")
        assert list(t.find_all_matches("Иванов")) == ["first", "second", "third"]

    def test_shorter_suffix_yielded_before_longer(self):
        # The trie traversal walks from the LAST character backward,
        # visiting terminals in increasing-suffix-length order. Useful
        # when a caller wants to prefer the most-specific match.
        t = SuffixTrie()
        t.insert("ов", "short")
        t.insert("анов", "long")
        result = list(t.find_all_matches("Иванов"))
        assert result == ["short", "long"]


class TestSuffixTrieCyrillic:
    def test_yo_letter_distinct_from_ye(self):
        # Ё (U+0401 / U+0451) and Е (U+0415 / U+0435) are different
        # codepoints. The trie must treat them as distinct keys —
        # matching them despite their visual similarity would
        # silently corrupt rule lookup.
        t = SuffixTrie()
        t.insert("ёва", 1)
        assert list(t.find_all_matches("Лёва")) == [1]
        assert list(t.find_all_matches("Лева")) == []

    def test_case_sensitive_by_default(self):
        # Trie keys and inputs are compared by Unicode codepoint —
        # callers who need case-insensitivity must lowercase before
        # querying. This is exactly what PetrovichGenderDetector.detect
        # does, and what the rule data assumes.
        t = SuffixTrie()
        t.insert("ов", 1)
        assert list(t.find_all_matches("ИВАНОВ")) == []
        assert list(t.find_all_matches("иванов")) == [1]

    def test_full_realistic_lastname_set(self):
        # Smoke test against a representative slice of suffixes from
        # the real rules.json — confirms the trie composes correctly
        # with overlapping Cyrillic prefixes/suffixes.
        t = SuffixTrie()
        for s, v in (
            ("ов", "M_OV"),
            ("ова", "F_OVA"),
            ("ев", "M_EV"),
            ("ева", "F_EVA"),
            ("ин", "M_IN"),
            ("ина", "F_INA"),
            ("ский", "M_SKY"),
            ("ская", "F_SKAYA"),
            ("их", "INDECL_IH"),
        ):
            t.insert(s, v)
        assert list(t.find_all_matches("Иванов")) == ["M_OV"]
        assert list(t.find_all_matches("Иванова")) == ["F_OVA"]
        assert list(t.find_all_matches("Григорьев")) == ["M_EV"]
        assert list(t.find_all_matches("Пушкин")) == ["M_IN"]
        assert list(t.find_all_matches("Толстовская")) == ["F_SKAYA"]
        assert list(t.find_all_matches("Гремитских")) == ["INDECL_IH"]


class TestSuffixTrieEdgeCases:
    def test_empty_suffix_matches_everything(self):
        # Storing the empty string is unusual but not invalid; it
        # acts as a wildcard match against any input.
        t = SuffixTrie()
        t.insert("", "wildcard")
        assert list(t.find_all_matches("Иванов")) == ["wildcard"]
        assert list(t.find_all_matches("")) == ["wildcard"]

    def test_single_character_suffix(self):
        t = SuffixTrie()
        t.insert("а", "ends_with_a")
        assert list(t.find_all_matches("Анна")) == ["ends_with_a"]
        assert list(t.find_all_matches("Иван")) == []

    @pytest.mark.parametrize(
        "value",
        [None, 0, "", [], (), {}, False, object()],
    )
    def test_falsy_values_are_preserved(self, value):
        # An earlier draft of find_all_matches used `if bucket:` on
        # the value list itself, which would have skipped retrieving
        # falsy *contents*. The current implementation distinguishes
        # 'no bucket' (None from dict.get) from 'bucket exists, may
        # contain falsy values' — pin that.
        t = SuffixTrie()
        t.insert("ов", value)
        result = list(t.find_all_matches("Иванов"))
        assert len(result) == 1
        assert result[0] is value or result[0] == value
