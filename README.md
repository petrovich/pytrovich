![Pytrovich](pytrovich.png)
==========================================

__pytrovich__ is a Python 3.9+ port of [petrovich library](https://github.com/petrovich) which inflects Russian names 
to a given grammatical case. It supports first names, last names and middle names inflections. Since version 0.0.2,
gender detection is also available. 

[petrovich-java](https://github.com/petrovich/petrovich-java) was the main inspiration.

__The alternative (earlier) port__: [Petrovich](https://github.com/damirazo/Petrovich)  ([@alexeyev](https://github.com/alexeyev) was not aware of it at the time of porting `petrovich` to Python). 
The only meaningful difference we have found is that it does not support gender detection.


![Python 3x](https://img.shields.io/badge/python-3.x-blue.svg)
[![PyPI version][pypi_badge]][pypi_link]
[![Downloads](https://pepy.tech/badge/pytrovich)](https://pepy.tech/project/pytrovich)

[pypi_badge]: https://badge.fury.io/py/pytrovich.svg
[pypi_link]: https://pypi.python.org/pypi/pytrovich

## Installation
Should be as simple as that
```bash
pip install pytrovich
```

## Usage

### Inflection

```python
from pytrovich.enums import NamePart, Gender, Case
from pytrovich.maker import PetrovichDeclinationMaker

maker = PetrovichDeclinationMaker()
print(maker.make(NamePart.FIRSTNAME, Gender.MALE, Case.GENITIVE, "Иван"))  # Ивана
print(maker.make(NamePart.LASTNAME, Gender.MALE, Case.INSTRUMENTAL, "Иванов"))  # Ивановым
print(maker.make(NamePart.MIDDLENAME, Gender.FEMALE, Case.DATIVE, "Ивановна"))  # Ивановне
```

### Gender detection

```python 
from pytrovich.detector import PetrovichGenderDetector

detector = PetrovichGenderDetector()
print(detector.detect(firstname="Иван"))  # Gender.MALE
print(detector.detect(firstname="Иван", middlename="Семёнович"))  # Gender.MALE
print(detector.detect(firstname="Арзу", middlename="Лутфияр кызы"))  # Gender.FEMALE
```


### Custom rule file

You can replace default rules file with some custom one. Only JSON format is supported.
```python
maker = PetrovichDeclinationMaker("/path/to/custom/rules.file.json")
```
E.g. if `pytrovich` fails on `PetrovichDeclinationMaker` creation, 
one may consider downloading `rules.json` directly from 
[petrovich-rules repo](https://github.com/petrovich/petrovich-rules) as a fix (please create an issue if that actually happens).

### How to cite

Not neccessary, but greatly appreciated, if you use this work.

```latex
@misc{Pytrovich,
  title     = {{petrovich/pytrovich: Python3 port of Petrovich, an inflector for Russian anthroponyms}},
  year      = {2020},
  url       = {https://github.com/petrovich/pytrovich},
  language  = {english},
}
```

### More info

For more information on the project please refer to other [petrovich](https://github.com/petrovich/) repos.

### TODO

- evaluation based on [petrovich-eval](https://github.com/petrovich/petrovich-eval/)

## Accuracy

pytrovich is benchmarked against the [petrovich-eval](https://github.com/petrovich/petrovich-eval) datasets, which together contain ~250k gold-standard rows from open Russian dictionaries.

Headline numbers, latest run on master:

| Eval set | Examples | Accuracy |
|---|---:|---:|
| Inflection / firstnames | 63,680 | 99.53% |
| Inflection / surnames | 80,025 | 99.82% |
| Inflection / midnames | 81,355 | 100.00% |
| Gender / firstnames | 12,720 | 84.29% |
| Gender / surnames | 15,474 | 99.83% |
| Gender / midnames | 16,005 | 100.00% |

To reproduce locally:

```bash
git submodule update --init --recursive
python scripts/evaluate.py rules    # all three name parts
python scripts/evaluate.py gender   # all three name parts

# Just one part, just the small hand-curated subset:
python scripts/evaluate.py rules --namepart firstnames --subset misc

# Regression mode (this is what CI runs):
python scripts/evaluate.py rules \
  --regression-against eval-baseline.rules.json --tolerance 0.5
```

Per-bucket accuracy is printed and a TSV of every error (lemma, expected, actual) is written to `errors.tsv` / `errors.gender.tsv`. The CI workflow uploads these as artifacts on every run.

The accuracy ceiling is dictated by what the rule-based approach can express; the firstname-gender number in particular is suppressed by short androgynous diminutives (Саша, Женя, etc.) that the library deliberately classifies as `ANDROGYNOUS` rather than guessing.

## License

This project is available under MIT license.
