import pytest

from model_mommy import mommy
from model_mommy.random_gen import gen_from_list
from model_mommy.exceptions import CustomMommyNotFound, InvalidCustomMommy
from tests.generic.models import Person


def gen_opposite(default):
    return not default


def gen_age():
    # forever young
    return 18


class KidMommy(mommy.Mommy):
    age_list = range(4, 12)
    attr_mapping = {'age': gen_from_list(age_list)}


class TeenagerMommy(mommy.Mommy):
    attr_mapping = {'age': gen_age}


class SadPeopleMommy(mommy.Mommy):
    attr_mapping = {'happy': gen_opposite, 'unhappy': gen_opposite}


@pytest.mark.django_db
class TestSimpleExtendMommy:
    def test_list_generator_respects_values_from_list(self):
        mom = KidMommy(Person)
        kid = mom.make()
        assert kid.age in KidMommy.age_list


@pytest.mark.django_db
class TestLessSimpleExtendMommy:
    def test_nonexistent_required_field(self):
        gen_opposite.required = ['house']
        mom = SadPeopleMommy(Person)
        with pytest.raises(AttributeError):
            mom.make()

    def test_string_to_generator_required(self):
        gen_opposite.required = ['default']
        happy_field = Person._meta.get_field('happy')
        unhappy_field = Person._meta.get_field('unhappy')
        mom = SadPeopleMommy(Person)
        person = mom.make()
        assert person.happy is not happy_field.default
        assert person.unhappy is not unhappy_field.default

    @pytest.mark.parametrize('value', [18, 18.5, [], {}, True])
    def test_fail_pass_non_string_to_generator_required(self, value):
        mom = TeenagerMommy(Person)

        gen_age.required = [value]
        with pytest.raises(ValueError):
            mom.make()


class ClassWithoutMake:
    def prepare(self):
        pass


class ClassWithoutPrepare:
    def make(self):
        pass


class MommySubclass(mommy.Mommy):
    pass


class MommyDuck:
    def __init__(*args, **kwargs):
        pass

    def make(self):
        pass

    def prepare(self):
        pass


class TestCustomizeMommyClassViaSettings:
    def class_to_import_string(self, class_to_convert):
        return '%s.%s' % (self.__module__, class_to_convert.__name__)

    def test_create_vanilla_mommy_used_by_default(self):
        mommy_instance = mommy.Mommy.create(Person)
        assert mommy_instance.__class__ == mommy.Mommy

    def test_create_fail_on_custom_mommy_load_error(self, settings):
        settings.MOMMY_CUSTOM_CLASS = 'invalid_module.invalid_class'
        with pytest.raises(CustomMommyNotFound):
            mommy.Mommy.create(Person)

    @pytest.mark.parametrize('cls', [ClassWithoutMake, ClassWithoutPrepare])
    def test_create_fail_on_missing_required_functions(self, settings, cls):
        settings.MOMMY_CUSTOM_CLASS = self.class_to_import_string(cls)
        with pytest.raises(InvalidCustomMommy):
            mommy.Mommy.create(Person)

    @pytest.mark.parametrize('cls', [MommySubclass, MommyDuck])
    def test_create_succeeds_with_valid_custom_mommy(self, settings, cls):
        settings.MOMMY_CUSTOM_CLASS = self.class_to_import_string(cls)
        assert mommy.Mommy.create(Person).__class__ == cls
