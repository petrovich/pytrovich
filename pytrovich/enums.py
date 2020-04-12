# -*- coding: utf-8 -*-

from enum import Enum
from functools import lru_cache


class Case(Enum):
    GENITIVE = 0
    DATIVE = 1
    ACCUSATIVE = 2
    INSTRUMENTAL = 3
    PREPOSITIONAL = 4


class Gender(Enum):
    MALE = 0
    FEMALE = 1
    ANDROGYNOUS = 2

    @staticmethod
    @lru_cache(100)
    def names(x):
        return {
            Gender.MALE: "male",
            Gender.FEMALE: "female",
            Gender.ANDROGYNOUS: "androgynous"
        }[x]


class NamePart(Enum):
    LASTNAME = 0
    FIRSTNAME = 1
    MIDDLENAME = 2

    @staticmethod
    @lru_cache(100)
    def names(x):
        return {
            NamePart.LASTNAME: "lastname",
            NamePart.FIRSTNAME: "firstname",
            NamePart.MIDDLENAME: "middlename"
        }[x]