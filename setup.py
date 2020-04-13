# -*- coding: utf-8 -*-

from distutils.core import setup

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pytrovich",
    packages=setuptools.find_packages(),
    version="0.0.1post2",
    description="pytrovich: a Python port of an inflector for Russian anthroponyms developed by petrovich team: "
                "https://github.com/petrovich",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Anton Alekseev",
    author_email="anton.m.alexeye@gmail.com",
    url="https://github.com/alexeyev/pytrovich",
    keywords=["nlp", "morphology", "russian language"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    zip_safe=False,
    include_package_data=True,
    python_requires=">=3.6",
)
