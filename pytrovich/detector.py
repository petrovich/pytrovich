# -*- coding: utf-8 -*-
import json
import sys
from os import path

from pytrovich import rules_data
from pytrovich.enums import Gender
from pytrovich.gender_models import Root, Name


class PetrovichGenderDetector(object):
    DEFAULT_PATH_TO_RULES_FILE = path.join(path.dirname(__file__), "petrovich-rules", "gender.json")

    def __init__(self, path_to_rules_file: str = DEFAULT_PATH_TO_RULES_FILE):

        try:
            with open(path_to_rules_file, "r", encoding="utf-8") as fp:
                self._root_rules_bean = Root.parse(json.load(fp=fp)["gender"])
        except Exception as e:
            print("Error occurred: %s" % str(e), file=sys.stderr)
            print("Using possibly outdated rules", file=sys.stderr)
            self._root_rules_bean = Root.parse(rules_data.gender()["gender"])

    @staticmethod
    def _check_against_exceptions(name: Name, str_name: str) -> set:
        results = []

        if name.exceptions and name.exceptions.male and str_name in name.exceptions.male:
            results.append(Gender.MALE)
        if name.exceptions and name.exceptions.female and str_name in name.exceptions.female:
            results.append(Gender.FEMALE)
        if name.exceptions and name.exceptions.andro and str_name in name.exceptions.andro:
            results.append(Gender.ANDROGYNOUS)
        return set(results)

    @staticmethod
    def _check_again_suffixes(name: Name, str_name: str) -> set:

        results = []

        if name.suffixes and name.suffixes.male:
            for possible_suffix in name.suffixes.male:
                if str_name.endswith(possible_suffix):
                    results.append(Gender.MALE)
                    break

        if name.suffixes and name.suffixes.female:
            for possible_suffix in name.suffixes.female:
                if str_name.endswith(possible_suffix):
                    results.append(Gender.FEMALE)
                    break

        if name.suffixes and name.suffixes.andro:
            for possible_suffix in name.suffixes.andro:
                if str_name.endswith(possible_suffix):
                    results.append(Gender.ANDROGYNOUS)
                    break

        return set(results)

    def detect(self, firstname=None, lastname=None, middlename=None):

        assert not (firstname is None and lastname is None and middlename is None), \
            "At least one part of the name should be given."

        results_middlename, results_firstname, results_lastname = set([]), set([]), set([])

        if middlename:
            results_middlename.update(self._check_against_exceptions(self._root_rules_bean.middlename, middlename))
            results_middlename.update(self._check_again_suffixes(self._root_rules_bean.middlename, middlename))

            if len(results_middlename) > 0 and next(iter(results_middlename)) != Gender.ANDROGYNOUS:
                return next(iter(results_middlename))

        if firstname:
            results_firstname.update(self._check_against_exceptions(self._root_rules_bean.firstname, firstname))
            results_firstname.update(self._check_again_suffixes(self._root_rules_bean.firstname, firstname))

        if lastname:
            results_lastname.update(self._check_against_exceptions(self._root_rules_bean.lastname, lastname))
            results_lastname.update(self._check_again_suffixes(self._root_rules_bean.lastname, lastname))

        if firstname and lastname:
            if results_firstname and results_lastname:
                fn, ln = next(iter(results_firstname)), next(iter(results_lastname))
                if fn != Gender.ANDROGYNOUS and ln == Gender.ANDROGYNOUS:
                    return fn
                if ln != Gender.ANDROGYNOUS and fn == Gender.ANDROGYNOUS:
                    return ln

        joined_set = results_firstname.union(results_middlename).union(results_lastname)

        if len(joined_set) == 1:
            return next(iter(joined_set))
        else:
            print("Gender prediction was confused, possible gender options: %s" % str(joined_set), file=sys.stderr)
            return next(iter(joined_set))


if __name__ == "__main__":
    detector = PetrovichGenderDetector()
    print(detector.detect(firstname="Иван", lastname="Голубцов"))
    print(detector.detect(firstname="Арзу", middlename="Лутфияр кызы"))
