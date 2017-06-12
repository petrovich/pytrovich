# -*- coding: utf-8 -*-


class Rule(object):

    def __init__(self, gender, mods, test):
        self.gender = gender
        self.mods = mods
        self.test = test


class Name(object):

    def __init__(self, exceptions, suffixes):
        """
        :param exceptions: list(Rule):
        :param suffixes: list(Rule)
        """
        self.exceptions = exceptions
        self.suffixes = suffixes


class Root(object):

    def __init__(self, firstname, lastname, middlename):

        self.firstname = firstname
        self.lastname = lastname
        self. middlename = middlename