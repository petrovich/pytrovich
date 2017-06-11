# -*- coding: utf-8 -*-
"""
    Pytrovich: petrovich inflector Python port
     This is a command line interface to the package
"""
from __future__ import print_function

import fileinput
import json
import sys


def main(args=None):

    if sys.stdin.isatty():
        return

    # todo: implement command-line interface

    print("CLI has not been implemented yet")

if __name__ == '__main__':
    main()