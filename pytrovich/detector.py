# -*- coding: utf-8 -*-
import json
import sys
from os import path

from pytrovich import rules_data
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


if __name__ == "__main__":
    detector = PetrovichGenderPredictor()
    print(detector._root_rules_bean)
