![Petrovich](petrovich.png) pytrovich
==========================================

__pytrovich__ is a library which inflects Russian names to given grammatical case. It supports first names, last names and middle names inflections.

__pytrovich__ is a Python implementation of Petrovich ruby gem (petrovich-ruby -> petrovich-java -> pytrovich).

## Usage

```python
maker = PetrovichDeclinationMaker.getInstance();

maker.make(NamePart.FIRSTNAME, Gender.MALE, Case.GENITIVE, "Иван");     //Ивана
maker.make(NamePart.LASTNAME, Gender.MALE, Case.INSTRUMENTAL, "Иванов");   //Ивановым
maker.make(NamePart.MIDDLENAME, Gender.FEMALE, Case.DATIVE, "Ивановна");   //Ивановне
```

### Custom rule file

You can replace default rules file with some custom one. Only JSON format supported by now.
```python
PetrovichDeclinationMaker maker = PetrovichDeclinationMaker.getInstance("/path/to/custom/rules.file.json");
```

### Accuracy

You can read about accuracy statistics in [petrovich-ruby](https://github.com/petrovich/petrovich-ruby#Оценка-аккуратности) project front page

### License

This project is available under MIT license.