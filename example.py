import pytrovich
from pytrovich.detector import PetrovichGenderDetector
from pytrovich.enums import Case, Gender, NamePart
from pytrovich.maker import PetrovichDeclinationMaker

print(pytrovich.__version__)

if __name__ == "__main__":
    maker = PetrovichDeclinationMaker()
    print(maker.make(NamePart.FIRSTNAME, Gender.MALE, Case.GENITIVE, "Иван"))  # Ивана
    print(maker.make(NamePart.LASTNAME, Gender.MALE, Case.INSTRUMENTAL, "Иванов"))  # Ивановым
    print(maker.make(NamePart.MIDDLENAME, Gender.FEMALE, Case.DATIVE, "Ивановна"))  # Ивановне
    print(maker.make(NamePart.FIRSTNAME, Gender.MALE, Case.ACCUSATIVE, "Александр"))  # Александра
    print(maker.make(NamePart.LASTNAME, Gender.FEMALE, Case.INSTRUMENTAL, "Герман"))
    print(maker.make(NamePart.LASTNAME, Gender.FEMALE, Case.DATIVE, "Дюма"))

    detector = PetrovichGenderDetector()
    print(detector.detect(firstname="Иван"))  # Gender.MALE
    print(detector.detect(firstname="Иван", middlename="Семёнович"))  # Gender.MALE
    print(detector.detect(firstname="Арзу", middlename="Лутфияр кызы"))  # Gender.FEMALE
