# coding: utf-8

import json
import sys
from os import path

from pytrovich import rules_data
from pytrovich.enums import NamePart, Gender, Case
from pytrovich.rule_models import Root, Name, Rule


class PetrovichNormalizer(object):
    DEFAULT_PATH_TO_RULES_FILE = path.join(path.dirname(__file__), "petrovich-rules", "rules.json")
    MODS_KEEP_IT_ALL_SYMBOL = "."
    MODS_REMOVE_LETTER_SYMBOL = "-"

    def __init__(self, path_to_rules_file: str = DEFAULT_PATH_TO_RULES_FILE):
        pass
        # todo

    def normalize(self, name_part: NamePart, gender: Gender, original_name: str) -> str:
        # todo
        raise NotImplementedError
