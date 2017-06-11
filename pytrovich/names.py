# -*- coding: utf-8 -*-

from pytrovich.enums import NamePart
import json

class PetrovichDeclinationMaker(object):


    self.DEFAULT_PATH_TO_RULES_FILE = "src/main/resources/rules.json"
    self.MODS_KEEP_IT_ALL_SYMBOL = "."
    self.MODS_REMOVE_LETTER_SYMBOL = "-"

    self._root_rules_bean = None

    self._male = new GenderCurryedMaker(Gender.MALE)
    self._female = new GenderCurryedMaker(Gender.FEMALE)
    self._androgynous = new GenderCurryedMaker(Gender.ANDROGYNOUS)


    def __init__(self, path_to_rules_file):
        data = open(path_to_rules_file, "r+").read()
        deserialize()
        _root_rules_bean = JSON.std.beanFrom(RootBean.class, data);
    }

    class __GenderCurryedMaker(object):

        def __init__(self, gender):
            self.gender = gender

        def as_firstname(self):
            return __GenderAndNamePartCurryedMaker(self.gender, NamePart.FIRSTNAME)

        def as_lastname(self):
            return __GenderAndNamePartCurryedMaker(self.gender, NamePart.LASTNAME)

        def as_middlename(self):
            return __GenderAndNamePartCurryedMaker(self.gender, NamePart.MIDDLENAME)

    class __GenderAndNamePartCurryedMaker:

        def __init__(self, gender, namePart):
            self.gender = gender
            self.namePart = namePart

        def to_genitive(self, name):
            return make(self.namePart, self.gender, Case.GENITIVE, name)

        def to_accusative(self, name):
            return make(self.namePart, self.gender, Case.ACCUSATIVE, name)

        def to_dative(self, name):
            return make(self.namePart, self.gender, Case.DATIVE, name)

        def to_prepositional(self, name):
            return make(self.namePart, self.gender, Case.PREPOSITIONAL, name)

        def to_instrumental(self, name):
            return make(self.namePart, self.gender, Case.INSTRUMENTAL, name)

    def make(self, name_part, gender, case_to_use, original_name):

        result = original_name

        name_bean = None

        if name_part == NamePart.FIRSTNAME:
            name_bean = self.root_rules_bean.get_first_name()
        elif name_part == NamePart.LASTNAME:
            name_bean = self.root_rules_bean.get_last_name()
        elif name_part == NamePart.MIDDLENAME:
            name_bean = self.root_rules_bean.get_middle_name()
        else:
            name_bean = self.root_rules_bean.get_middle_name()

        rule_to_use = None
        
        exception_rule_bean = self.find_in_rule_bean_list(name_bean.get_exceptions(), gender, original_name)
        suffix_rule_bean = self.find_in_rule_bean_list(name_bean.get_suffixes(), gender, original_name)

        mod2apply = None

        if exception_rule_bean and exception_rule_bean.get_gender() == gender.get_value():
            rule_to_use = exception_rule_bean
        elif suffix_rule_bean and suffix_rule_bean.get_gender().equals(gender.get_value()):
            rule_to_use = suffix_rule_bean
        else:
            rule_to_use = exception_rule_bean if exception_rule_bean else suffix_rule_bean

        if rule_to_use:
            mod2apply = rule_to_use.get_mods().get(case_to_use.get_value())
            result = self.apply_mod2name(mod2apply, original_name)

        return result