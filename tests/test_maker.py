import pytest

from pytrovich.enums import Case, NamePart, Gender
from pytrovich.maker import PetrovichDeclinationMaker


@pytest.fixture(scope='session')
def maker() -> PetrovichDeclinationMaker:
    return PetrovichDeclinationMaker()


class TestPetrovichDeclinationMaker:
    @pytest.mark.parametrize('name_part,gender,case_to_use,original_name,expected_result', (
        # firstnames
        (NamePart.FIRSTNAME, Gender.FEMALE, Case.GENITIVE, 'Мария', 'Марии'),
        (NamePart.FIRSTNAME, Gender.MALE, Case.DATIVE, 'Василий', 'Василию'),
        (NamePart.FIRSTNAME, Gender.FEMALE, Case.ACCUSATIVE, 'Ксюша', 'Ксюшу'),
        (NamePart.FIRSTNAME, Gender.MALE, Case.INSTRUMENTAL, 'Паша', 'Пашой'),
        (NamePart.FIRSTNAME, Gender.FEMALE, Case.PREPOSITIONAL, 'Елена', 'Елене'),
        # middlenames
        (NamePart.MIDDLENAME, Gender.FEMALE, Case.GENITIVE, 'Геннадиевна', 'Геннадиевны'),
        (NamePart.MIDDLENAME, Gender.MALE, Case.DATIVE, 'Васильевич', 'Васильевичу'),
        (NamePart.MIDDLENAME, Gender.FEMALE, Case.ACCUSATIVE, 'Васильевна', 'Васильевну'),
        (NamePart.MIDDLENAME, Gender.MALE, Case.INSTRUMENTAL, 'Павлович', 'Павловичем'),
        (NamePart.MIDDLENAME, Gender.FEMALE, Case.PREPOSITIONAL, 'Павловна', 'Павловне'),
        # lastnames
        (NamePart.LASTNAME, Gender.FEMALE, Case.GENITIVE, 'Цветаева', 'Цветаевой'),
        (NamePart.LASTNAME, Gender.MALE, Case.DATIVE, 'Толстой', 'Толстому'),
        (NamePart.LASTNAME, Gender.FEMALE, Case.ACCUSATIVE, 'Ахматова', 'Ахматову'),
        (NamePart.LASTNAME, Gender.MALE, Case.INSTRUMENTAL, 'Лермонтов', 'Лермонтовым'),
        (NamePart.LASTNAME, Gender.FEMALE, Case.PREPOSITIONAL, 'Баркова', 'Барковой'),
    ))
    def test_common_names(
        self,
        maker: PetrovichDeclinationMaker,
        name_part: NamePart,
        gender: Gender,
        case_to_use: Case,
        original_name: str,
        expected_result: str
    ) -> None:

        assert maker.make(name_part, gender, case_to_use, original_name) == expected_result

