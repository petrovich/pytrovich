"""
Pins consistency between the two places pytrovich's version is
declared.

Background: ``pytrovich/meta.py`` exports ``version`` (which is what
``pytrovich.__version__`` resolves to at runtime) and ``setup.py``
passes a ``version=`` kwarg to ``setuptools.setup()``. Both currently
hold a string literal; nothing keeps them in sync. A release where
``meta.py`` is bumped but ``setup.py`` is forgotten (or vice versa)
ships a wheel whose internal version disagrees with its package
metadata, which breaks anything that introspects
``importlib.metadata.version("pytrovich")``.

This test reads ``setup.py`` as text and walks its AST to find the
literal passed to ``version=``, then compares it to ``meta.version``.
Going through the AST instead of executing setup.py keeps the test
independent of setuptools internals and avoids importing distutils
(which emits noisy deprecation warnings on modern Python).

If the two diverge, fix by editing both files. If you'd rather
remove the duplication outright, a small ``setup.py`` change can
read ``version`` from ``pytrovich/meta.py`` directly — but that's
out of scope for this test, which just guards the existing layout.
"""

import ast
from pathlib import Path

import pytest

from pytrovich import meta

REPO_ROOT = Path(__file__).resolve().parent.parent
SETUP_PY = REPO_ROOT / "setup.py"


def _extract_setup_kwarg(source: str, kwarg_name: str) -> str:
    """
    Return the literal value passed as ``kwarg_name=...`` to the
    top-level ``setup()`` call in *source*. Raises ValueError if the
    call cannot be found, the kwarg is absent, or the value isn't a
    plain string literal.
    """
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        # Match either `setup(...)` or `setuptools.setup(...)` —
        # both shapes appear in the wild.
        func = node.func
        is_setup = (isinstance(func, ast.Name) and func.id == "setup") or (
            isinstance(func, ast.Attribute) and func.attr == "setup"
        )
        if not is_setup:
            continue
        for kw in node.keywords:
            if kw.arg == kwarg_name:
                if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    return kw.value.value
                raise ValueError(f"setup() {kwarg_name}= must be a string literal (got {ast.dump(kw.value)})")
    raise ValueError(f"could not find setup({kwarg_name}=...) in source")


class TestVersionConsistency:
    @pytest.fixture(scope="class")
    def setup_version(self) -> str:
        return _extract_setup_kwarg(SETUP_PY.read_text(encoding="utf-8"), "version")

    def test_setup_py_version_matches_meta(self, setup_version: str):
        assert setup_version == meta.version, (
            f"version drift between setup.py ({setup_version!r}) and "
            f"pytrovich/meta.py ({meta.version!r}) — bump both or "
            f"refactor setup.py to read from meta.py."
        )

    def test_setup_py_name_matches_meta(self):
        # While we're parsing setup.py, also pin the package-name
        # field. Same drift hazard, same one-liner check.
        setup_name = _extract_setup_kwarg(SETUP_PY.read_text(encoding="utf-8"), "name")
        assert setup_name == meta.package, (
            f"package-name drift between setup.py ({setup_name!r}) and pytrovich/meta.py ({meta.package!r})."
        )
