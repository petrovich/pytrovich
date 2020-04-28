![Pytrovich](pytrovich.png)
==========================================

__pytrovich__ is a Python 3.6+ port of [petrovich library](https://github.com/petrovich) which inflects Russian names 
to a given grammatical case. It supports first names, last names and middle names inflections.

[petrovich-java](https://github.com/petrovich/petrovich-java) was the main inspiration.

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

```python
from pytrovich.enums import NamePart, Gender, Case
from pytrovich.maker import PetrovichDeclinationMaker

maker = PetrovichDeclinationMaker()
print(maker.make(NamePart.FIRSTNAME, Gender.MALE, Case.GENITIVE, "Иван"))  # Ивана
print(maker.make(NamePart.LASTNAME, Gender.MALE, Case.INSTRUMENTAL, "Иванов"))  # Ивановым
print(maker.make(NamePart.MIDDLENAME, Gender.FEMALE, Case.DATIVE, "Ивановна"))  # Ивановне
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

Also please see the alternative (earlier) implementation: [Petrovich](https://github.com/damirazo/Petrovich)  
(@alexeyev was not aware of it at the time of porting `petrovich` to Python).

### TODO

- grammatical gender detection (given the name)
- evaluation based on [petrovich-eval](https://github.com/petrovich/petrovich-eval/)

## License

This project is available under MIT license.
