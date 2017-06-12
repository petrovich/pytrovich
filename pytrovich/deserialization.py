import json

from pytrovich import rules_data
from pytrovich.models import Root


def deserialize_name(map):
    return ""


def deserialize_rule(map):
    return ""


def deserialize_root(string):
    rootmap = json.loads(string)

    lastname = None
    firstname = None
    middlename = None

    if "lastname" in rootmap:
        lastname = deserialize_name(rootmap["lastname"])

    if "firstname" in rootmap:
        firstname = deserialize_name(rootmap["firstname"])

    if "middlename" in rootmap:
        middlename = deserialize_name(rootmap["middlename"])

    root = Root(firstname, lastname, middlename)

    return root


if __name__ == "__main__":
    deserialize_root(rules_data.rules_as_json_string)
