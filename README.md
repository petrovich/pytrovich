![Pytrovich](pytrovich.png)
==========================================

__pytrovich__ is a Python 3.9+ port of [petrovich library](https://github.com/petrovich) which inflects Russian names 
to a given grammatical case. It supports first names, last names and middle names inflections. Since version 0.0.2,
gender detection is also available. 

<details>
  <summary>It is STRONGLY RECOMMENDED to use pytrovich VERSION >=0.1.0</summary>

  *3–5× faster lookups via a suffix trie, 800× faster repeated construction via parsed-rules caching,
  deterministic gender output, correct handling of all-caps / Ё / indeclinable names that previously 
  failed silently, and refreshed rules data covering 24 upstream fixes from 2020–2024. 
  Upgrade because the old version returned wrong answers on a non-trivial slice of real Russian 
  names (try make(LASTNAME, MALE, GEN, "ИВАНОВ") or make(FIRSTNAME, MALE, GEN, "Пётр") on both --- 
  the new one is correct, the old one isn't), flapped between gender predictions across runs, 
  and crashed on unknown names; the new one is faster, deterministic, properly typed (py.typed ships), 
  and benchmarked at >99% accuracy across 270k gold-standard inflections.*
</details>

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

## License

This project is available under MIT license.
