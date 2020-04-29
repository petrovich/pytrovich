# -*- coding: utf-8 -*-
import json
import sys
from os import path

from pytrovich import rules_data
from pytrovich.enums import Gender
from pytrovich.gender_models import Root, Name, Rule


class PetrovichGenderPredictor(object):
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
    def _check_against_exceptions(name: Name, str_name: str):
        results = []
        if name.exceptions and name.exceptions.male and str_name in name.exceptions.male:
            results.append(Gender.MALE)
        if name.exceptions and name.exceptions.female and str_name in name.exceptions.female:
            results.append(Gender.FEMALE)
        if name.exceptions and name.exceptions.andro and str_name in name.exceptions.andro:
            results.append(Gender.ANDROGYNOUS)
        return set(results)

    def detect(self, firstname=None, lastname=None, middlename=None):
        assert not (firstname is None and lastname is None and middlename is None), \
            "At least one part of the name should be given."

        results = {}

        if middlename:
            results.update(PetrovichGenderPredictor._check_against_exceptions(self._root_rules_bean.middlename, middlename))
        if firstname:
            results.update(PetrovichGenderPredictor._check_against_exceptions(self._root_rules_bean.firstname, firstname))
        if lastname:
            results.update(PetrovichGenderPredictor._check_against_exceptions(self._root_rules_bean.lastname, lastname))
        # todo: rule check in progress

        return results


if __name__ == "__main__":
    detector = PetrovichGenderPredictor()
    # print(detector._root_rules_bean)
    print(detector.detect("Иван", "Говнов", "Семёнов оглы"))
