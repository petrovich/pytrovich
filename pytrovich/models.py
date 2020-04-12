# -*- coding: utf-8 -*-
# well I've tried to use jsonpickle or something of the like but without much luck


class Rule(object):

    def __init__(self, gender: str, mods: list, test: list):
        """
            :param gender: grammatical gender
            :param mods: modifications rules list
            :param test: search rules list
        """
        self.gender = gender
        self.mods = mods
        self.test = test

    def serialize(self):
        return {"gender": self.gender,
                "mods": self.mods,
                "test": self.test}

    @staticmethod
    def parse(o: dict):
        return Rule(gender=o["gender"], mods=o["mods"], test=o["test"])


class Name(object):

    def __init__(self, exceptions: list, suffixes: list):
        """
            :param exceptions: list(Rule):
            :param suffixes: list(Rule)
        """
        self.exceptions = exceptions
        self.suffixes = suffixes

    def serialize(self):
        return {"exceptions": [e.serialize() for e in self.exceptions],
                "suffixes": [s.serialize() for s in self.suffixes]}

    @staticmethod
    def parse(o: dict):
        return Name(exceptions=[Rule.parse(e) for e in o.get("exceptions", [])],
                    suffixes=[Rule.parse(s) for s in o.get("suffixes", [])])


class Root(object):

    def __init__(self, firstname, lastname, middlename):
        self.firstname = firstname
        self.lastname = lastname
        self.middlename = middlename

    def serialize(self):
        return {"firstname": self.firstname.serialize(),
                "lastname": self.lastname.serialize(),
                "middlename": self.middlename.serialize()}

    @staticmethod
    def parse(a: dict):
        return Root(firstname=Name.parse(a["firstname"]),
                    lastname=Name.parse(a["lastname"]),
                    middlename=Name.parse(a["middlename"]))