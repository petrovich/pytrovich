import pytest

from pytrovich.detector import PetrovichGenderDetector
from pytrovich.enums import Gender


@pytest.fixture(scope='session')
def gender_detector():
    return PetrovichGenderDetector()


class TestPetrovichGenderDetector:
    @pytest.mark.parametrize('middlename,expected_gender', (
        ('Иванович', Gender.MALE),
        ('Ильинична', Gender.FEMALE),
        pytest.param('Блаблабла', Gender.ANDROGYNOUS, marks=pytest.mark.xfail(reason='Issue #6')),
    ))
    def test_detect_by_middlename(self, gender_detector, middlename, expected_gender):
        assert gender_detector.detect(middlename=middlename) == expected_gender
