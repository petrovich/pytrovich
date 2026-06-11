"""
A reverse-trie data structure for fast suffix matching.

Built once at PetrovichDeclinationMaker / PetrovichGenderDetector
construction time. Replaces the O(n) linear scan over rule lists
(``for rule in rules: for test in rule.tests: if name.endswith(test)``)
with an O(L) traversal where L is the longest matched suffix.

The trie stores reversed strings: ``insert("ов")`` creates a path
``root → "в" → "о"`` with a terminal marker at "о". To find which
stored keys are suffixes of an input ``T``, walk the trie from the
LAST character of ``T`` backward; every terminal node visited
corresponds to a stored key that is a suffix of ``T``.

Why pure Python and not pyahocorasick / marisa-trie:

* The rule sets are small (≤ ~130 patterns per name part, ≤ ~10 chars
  each). Per-character dict lookup overhead in Python is comparable to
  one ``str.endswith`` call in C — the wins come from the algorithmic
  change (one walk instead of n walks), not from constant-factor
  optimization.
* No new C extension to build, vendor wheels for, or debug. The
  pytrovich install stays pure-Python and cross-platform.
* The whole module is < 100 lines and trivially picklable (nested
  dicts), which keeps construction-time caching simple.

If profiling ever shows the trie traversal as a hot spot at higher
scale (millions of names, far larger rule sets), pyahocorasick is the
recommended drop-in.
"""


class SuffixTrie:
    """
    Multi-valued suffix trie. Keys are strings; values are arbitrary
    Python objects. Multiple inserts under the same key accumulate in
    insertion order.
    """

    __slots__ = ("_root",)

    # Sentinel used as the dict key for terminal-node value lists.
    # ``None`` cannot collide with any single-character string key,
    # which is what the trie navigation uses for everything else.
    _TERMINAL = None

    def __init__(self):
        self._root = {}

    def insert(self, suffix: str, value) -> None:
        """Store *value* under *suffix*."""
        node = self._root
        for ch in reversed(suffix):
            sub = node.get(ch)
            if sub is None:
                sub = {}
                node[ch] = sub
            node = sub
        bucket = node.get(self._TERMINAL)
        if bucket is None:
            bucket = []
            node[self._TERMINAL] = bucket
        bucket.append(value)

    def find_all_matches(self, text: str):
        """
        Yield every stored value whose key is a suffix of *text*.

        Yielded in (suffix-length ascending, then insertion-order)
        order, but callers should treat the result as an unordered
        bag — both call sites in pytrovich either deduplicate via
        ``set()`` or pick a winner by some other criterion.
        """
        node = self._root
        for ch in reversed(text):
            sub = node.get(ch)
            if sub is None:
                return
            node = sub
            bucket = node.get(self._TERMINAL)
            if bucket:
                yield from bucket

    def find_longest_match(self, text: str):
        """
        Return the first-inserted value stored under the LONGEST key
        that is a suffix of *text*, or None if no key matches.

        This is the lookup petrovich-ruby's RuleSet#find_gender_rule
        performs: gender suffixes are sorted by descending length
        ("accuracy") and the first match wins, so the longest matching
        suffix decides; ties on equal-length (i.e. identical) suffixes
        resolve by insertion order.
        """
        node = self._root
        found = None
        for ch in reversed(text):
            sub = node.get(ch)
            if sub is None:
                break
            node = sub
            bucket = node.get(self._TERMINAL)
            if bucket:
                found = bucket[0]
        return found
