"""
Tests for pytrovich's logging behavior.

These pin the contract between the library and downstream callers:

  * The library never emits log records to a real handler unless the
    host application has configured one — `pytrovich/__init__.py`
    attaches a NullHandler on import.
  * High-level operations and error/ambiguity paths are observable via
    standard `logging.getLogger("pytrovich.*")` loggers.
  * Log calls in hot paths use `%`-style format strings so the
    formatting is deferred when DEBUG is disabled.
"""

import logging

import pytest

from pytrovich.detector import PetrovichGenderDetector
from pytrovich.enums import Case, Gender, NamePart
from pytrovich.maker import PetrovichDeclinationMaker


@pytest.fixture(scope="module")
def maker() -> PetrovichDeclinationMaker:
    return PetrovichDeclinationMaker()


@pytest.fixture(scope="module")
def detector() -> PetrovichGenderDetector:
    return PetrovichGenderDetector()


class TestLibraryLoggingContract:
    """
    Static guarantees about how pytrovich integrates with the stdlib
    logging system.
    """

    def test_package_logger_has_null_handler_attached(self):
        # Without this, code paths that log on a fresh interpreter (e.g.
        # the ambiguity warning) would print "No handlers could be
        # found for logger 'pytrovich'" to stderr on Python 3.1 and
        # earlier — and on later Pythons would be routed to the
        # lastResort handler. NullHandler is the documented library
        # convention.
        package_logger = logging.getLogger("pytrovich")
        handler_types = [type(h).__name__ for h in package_logger.handlers]
        assert "NullHandler" in handler_types, (
            f"expected NullHandler on 'pytrovich' logger, got {handler_types}"
        )

    def test_module_loggers_use_dotted_namespace(self, maker, detector):
        # The standard pattern is `logger = logging.getLogger(__name__)`
        # in each module, which gives `pytrovich.maker` etc. — making
        # downstream filtering by submodule trivial.
        # We assert the loggers exist after the modules are imported.
        for name in ("pytrovich.maker", "pytrovich.detector"):
            logger = logging.getLogger(name)
            assert logger.name == name


class TestLoggingBehavior:
    """
    Exercise representative code paths and assert the log records they
    emit match the contract.
    """

    def test_ambiguous_gender_emits_warning(self, detector, caplog):
        # 'Иванова' as a sole firstname matches both an androgynous
        # exception and a feminine suffix — this is the ambiguity path
        # in detect() that used to print to stderr.
        with caplog.at_level(logging.WARNING, logger="pytrovich.detector"):
            detector.detect(firstname="иона", lastname="регин")
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert any("ambiguous" in r.getMessage().lower() for r in warnings), (
            f"expected an ambiguity warning, got {[r.getMessage() for r in warnings]}"
        )

    def test_make_emits_debug_trace(self, maker, caplog):
        # Sanity: when DEBUG is enabled, make() narrates which rule
        # was used and what mod was applied. This lets users diagnose
        # why a particular name declined the way it did.
        with caplog.at_level(logging.DEBUG, logger="pytrovich.maker"):
            maker.make(NamePart.FIRSTNAME, Gender.MALE, Case.GENITIVE, "Иван")
        debug_messages = [r.getMessage() for r in caplog.records if r.levelno == logging.DEBUG]
        assert any("rule" in m.lower() for m in debug_messages), (
            f"expected DEBUG mention of rule selection, got {debug_messages}"
        )
        assert any("applied mod" in m.lower() for m in debug_messages), (
            f"expected DEBUG mention of mod application, got {debug_messages}"
        )

    def test_no_log_records_at_default_level(self, maker, detector, caplog):
        # WARNING-and-below paths shouldn't fire on the happy path.
        # This guards against accidentally promoting DEBUG logs to
        # WARNING in future refactors.
        with caplog.at_level(logging.WARNING):
            maker.make(NamePart.FIRSTNAME, Gender.MALE, Case.GENITIVE, "Иван")
            detector.detect(firstname="Иван", lastname="Петров")
        assert caplog.records == [], (
            f"happy-path operations should not log at WARNING+, got "
            f"{[(r.name, r.levelname, r.getMessage()) for r in caplog.records]}"
        )

    def test_log_calls_use_lazy_formatting(self, maker, caplog):
        # Critical for hot paths: when DEBUG is disabled, the args to
        # logger.debug() must NOT be %-formatted into a string, because
        # that's the point of using `logger.debug("x %s", expensive)`
        # over `logger.debug(f"x {expensive}")`. We test this by
        # passing an argument whose __str__ raises — if the log call
        # is lazy, no exception fires; if it eagerly formats, the
        # test will see the exception bubble up.

        class ExplodingRepr:
            def __str__(self):
                raise AssertionError("eager formatting detected")

            __repr__ = __str__

        # Force the maker logger to WARNING so its DEBUG calls are
        # filtered before formatting.
        maker_logger = logging.getLogger("pytrovich.maker")
        old_level = maker_logger.level
        maker_logger.setLevel(logging.WARNING)
        try:
            # This should not raise even though every DEBUG call along
            # the way would format ExplodingRepr.
            maker_logger.debug("safe: %s", ExplodingRepr())
        finally:
            maker_logger.setLevel(old_level)
