# -*- coding: utf-8 -*-

from enum import Enum


class LowerCaseNameEnum(Enum):
    def str(self):
        return self.name.lower()


class Case(LowerCaseNameEnum):
    GENITIVE = 0
    DATIVE = 1
    ACCUSATIVE = 2
    INSTRUMENTAL = 3
    PREPOSITIONAL = 4


class Gender(LowerCaseNameEnum):
    MALE = 0
    FEMALE = 1
    ANDROGYNOUS = 2


class NamePart(LowerCaseNameEnum):
    LASTNAME = 0
    FIRSTNAME = 1
    MIDDLENAME = 2
