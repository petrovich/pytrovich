# coding: utf-8
from pytrovich.enums import NamePart, Gender, Case
from pytrovich.names import PetrovichDeclinationMaker

if __name__ == "__main__":
    maker = PetrovichDeclinationMaker()
    print(maker.make(NamePart.FIRSTNAME, Gender.MALE, Case.GENITIVE, "Иван"))  # Ивана
    print(maker.make(NamePart.LASTNAME, Gender.MALE, Case.INSTRUMENTAL, "Иванов"))  # Ивановым
    print(maker.make(NamePart.MIDDLENAME, Gender.FEMALE, Case.DATIVE, "Ивановна"))  # Ивановне
