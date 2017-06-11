# -*- coding: utf-8 -*-

from enum import Enum


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

    names = {
        MALE: "male",
        FEMALE: "female",
        ANDROGYNOUS: "androgynous"
    }


class NamePart(Enum):

    LASTNAME = 0
    FIRSTNAME = 1
    MIDDLENAME = 2

    names = {
        LASTNAME: "lastname",
        FIRSTNAME: "firstname",
        MIDDLENAME: "middlename"
    }