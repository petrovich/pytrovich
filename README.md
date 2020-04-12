![Petrovich](petrovich.png) pytrovich
==========================================

__pytrovich__ is a library which inflects Russian names to given grammatical case. It supports first names, last names and middle names inflections.

__pytrovich__ is a Python implementation of Petrovich ruby gem 
([petrovich-java](https://github.com/petrovich/petrovich-java) being the main inspiration)

## Usage

```python
from pytrovich.enums import NamePart, Gender, Case
from pytrovich.names import PetrovichDeclinationMaker

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

For more info please refer to [petrovich](https://github.com/petrovich/) repos.

### License

This project is available under MIT license.