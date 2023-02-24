# coding: utf-8
import pytrovich
from pytrovich.detector import PetrovichGenderDetector
from pytrovich.enums import NamePart, Gender, Case
from pytrovich.maker import PetrovichDeclinationMaker
from pytrovich.normalizer import PetrovichNormalizer

print(pytrovich.__version__)

if __name__ == "__main__":

    # normalizer = PetrovichNormalizer()
    # print(normalizer.normalize(NamePart.FIRSTNAME, Gender.MALE, "Ивана"))
    # print(normalizer.normalize(NamePart.FIRSTNAME, Gender.MALE, "Александру"))
    # print(normalizer.normalize(NamePart.FIRSTNAME, Gender.FEMALE, "Александру"))

    maker = PetrovichDeclinationMaker()
    print(maker.make(NamePart.FIRSTNAME, Gender.FEMALE, Case.GENITIVE, "Ольга"))  # Ольги
    print(maker.make(NamePart.FIRSTNAME, Gender.MALE, Case.GENITIVE, "Ольга"))  # Ольгы

    print(maker.make(NamePart.FIRSTNAME, Gender.MALE, Case.GENITIVE, "Лев"))  # Льва
    print(maker.make(NamePart.LASTNAME, Gender.MALE, Case.GENITIVE, "Толстой"))  # Толстого

    # print(maker.make(NamePart.FIRSTNAME, Gender.MALE, Case.GENITIVE, "Иван"))  # Ивана
    # print(maker.make(NamePart.LASTNAME, Gender.MALE, Case.INSTRUMENTAL, "Иванов"))  # Ивановым
    # print(maker.make(NamePart.MIDDLENAME, Gender.FEMALE, Case.DATIVE, "Ивановна"))  # Ивановне
    # print(maker.make(NamePart.FIRSTNAME, Gender.MALE, Case.ACCUSATIVE, "Александр"))  # Ивана
    # print(maker.make(NamePart.LASTNAME, Gender.FEMALE, Case.INSTRUMENTAL, "Герман"))  # Ивановым
    # print(maker.make(NamePart.LASTNAME, Gender.FEMALE, Case.DATIVE, "Дюма"))  # Ивановне
    #
    # detector = PetrovichGenderDetector()
    # print(detector.detect(firstname="Иван"))  # Gender.MALE
    # print(detector.detect(firstname="Иван", middlename="Семёнович"))  # Gender.MALE
    # print(detector.detect(firstname="Арзу", middlename="Лутфияр кызы"))  # Gender.FEMALE
