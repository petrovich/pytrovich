# -*- coding: utf-8 -*-
# well I've tried to use jsonpickle or something of the like but without much luck


class Rule(object):
    """
        Exceptions/suffices as lists of strings for checking matches against ones
    """

    def __init__(self, male: list = None, female: list = None, androgynous: list = None):
        assert not male is None or not female is None or not androgynous is None
        self.male = set(male) if not male is None else []
        self.female = set(female) if not female is None else []
        self.andro = set(androgynous) if not androgynous is None else []

    def serialize(self):
        builder = {}
        if self.male and len(self.male) > 0:  builder["male"] = self.male
        if self.female and len(self.female) > 0:  builder["female"] = self.female
        if self.andro and len(self.andro) > 0:  builder["androgynous"] = self.andro
        return builder

    @staticmethod
    def parse(o: dict):
        return Rule(male=o.get("male", None), female=o.get("female", None), androgynous=o.get("androgynous", None))


class Name(object):

    def __init__(self, exceptions: Rule=None, suffixes: Rule=None):
        """
            :param exceptions: list(Rule):
            :param suffixes: list(Rule)
        """
        assert exceptions is not None or suffixes is not None
        self.exceptions = exceptions
        self.suffixes = suffixes

    def serialize(self):
        builder = {}
        if self.exceptions is not None: builder["exceptions"] = self.exceptions.serialize()
        if self.suffixes is not None: builder["suffixes"] = self.suffixes.serialize()
        return builder

    @staticmethod
    def parse(o: dict):

        return Name(exceptions=Rule.parse(o["exceptions"]) if "exceptions" in o else None,
                    suffixes=Rule.parse(o["suffixes"]) if "suffixes" in o else None)


class Root(object):

    def __init__(self, firstname: Name = None, lastname: Name = None, middlename: Name = None):
        assert not firstname is None or not lastname is None or not middlename is None
        self.firstname = firstname
        self.lastname = lastname
        self.middlename = middlename

    def serialize(self):
        builder = {}
        if not self.firstname is None: builder["firstname"] = self.firstname.serialize()
        if not self.lastname is None: builder["lastname"] = self.lastname.serialize()
        if not self.middlename is None: builder["middlename"] = self.middlename.serialize()
        return builder

    @staticmethod
    def parse(a: dict):
        return Root(firstname=Name.parse(a["firstname"]) if "firstname" in a else None,
                    lastname=Name.parse(a["lastname"]) if "lastname" in a else None,
                    middlename=Name.parse(a["middlename"]) if "middlename" in a else None)

    def __str__(self):
        return str(self.serialize())
