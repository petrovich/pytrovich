import logging

from . import meta
from .detector import PetrovichGenderDetector
from .enums import Case, Gender, NamePart
from .maker import PetrovichDeclinationMaker

__version__ = meta.version
__author__ = meta.authors[0]
__license__ = meta.license
__copyright__ = meta.copyright

__all__ = [
    "Case",
    "Gender",
    "NamePart",
    "PetrovichDeclinationMaker",
    "PetrovichGenderDetector",
    "__author__",
    "__copyright__",
    "__license__",
    "__version__",
]

# Library convention: attach a NullHandler so consumers who never call
# logging.basicConfig() don't see "No handlers could be found for
# logger 'pytrovich'" warnings on first emission. The host application
# remains in full control of log routing and levels.
# https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
logging.getLogger(__name__).addHandler(logging.NullHandler())
