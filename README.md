![Pytrovich](pytrovich.png)
==========================================

__pytrovich__ is a Python 3.6+ port of [petrovich library](https://github.com/petrovich) which inflects Russian names 
to a given grammatical case. It supports first names, last names and middle names inflections.

[petrovich-java](https://github.com/petrovich/petrovich-java) was the main inspiration.

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

### More info

For more info please refer to other [petrovich](https://github.com/petrovich/) repos.

### TODO

- grammatical gender detection (given the name)
- `How to cite us` section

### License

This project is available under MIT license.