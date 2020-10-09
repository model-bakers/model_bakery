import pytest

from model_bakery import baker
from model_bakery.exceptions import CustomBakerNotFound, InvalidCustomBaker
from model_bakery.random_gen import gen_from_list
from tests.generic.models import Person


def gen_opposite(default):
    return not default


def gen_age():
    # forever young
    return 18


class ExperientBaker(baker.Baker):
    age_list = range(40, 60)
    attr_mapping = {"age": gen_from_list(age_list)}


class TeenagerBaker(baker.Baker):
    attr_mapping = {"age": gen_age}


class SadPeopleBaker(baker.Baker):
    attr_mapping = {
        "enjoy_jards_macale": gen_opposite,
        "like_metal_music": gen_opposite,
        "name": gen_opposite,  # Use a field without `default`
    }


@pytest.mark.django_db
class TestSimpleExtendBaker:
    def test_list_generator_respects_values_from_list(self):
        experient_bakers_factory = ExperientBaker(Person)
        experient_baker = experient_bakers_factory.make()
        assert experient_baker.age in ExperientBaker.age_list


@pytest.mark.django_db
class TestLessSimpleExtendBaker:
    def test_nonexistent_required_field(self):
        gen_opposite.required = ["house"]
        sad_people_factory = SadPeopleBaker(Person)
        with pytest.raises(AttributeError):
            sad_people_factory.make()

    def test_string_to_generator_required(self):
        gen_opposite.required = ["default"]
        enjoy_jards_macale_field = Person._meta.get_field("enjoy_jards_macale")
        like_metal_music_field = Person._meta.get_field("like_metal_music")
        sad_people_factory = SadPeopleBaker(Person)
        person = sad_people_factory.make()
        assert person.enjoy_jards_macale is enjoy_jards_macale_field.default
        assert person.like_metal_music is like_metal_music_field.default

    def test_kwarg_used_over_attr_mapping_generator(self):
        sad_people_factory = SadPeopleBaker(Person)
        person = sad_people_factory.make(name="test")
        assert person.name == "test"

    @pytest.mark.parametrize("value", [18, 18.5, [], {}, True])
    def test_fail_pass_non_string_to_generator_required(self, value):
        teens_bakers_factory = TeenagerBaker(Person)

        gen_age.required = [value]
        with pytest.raises(ValueError):
            teens_bakers_factory.make()


class ClassWithoutMake:
    def prepare(self):
        pass


class ClassWithoutPrepare:
    def make(self):
        pass


class BakerSubclass(baker.Baker):
    pass


class BakerDuck:
    def __init__(*args, **kwargs):
        pass

    def make(self):
        pass

    def prepare(self):
        pass


class TestCustomizeBakerClassViaSettings:
    def class_to_import_string(self, class_to_convert):
        return "%s.%s" % (self.__module__, class_to_convert.__name__)

    def test_create_vanilla_baker_used_by_default(self):
        baker_instance = baker.Baker.create(Person)
        assert baker_instance.__class__ == baker.Baker

    def test_create_fail_on_custom_baker_load_error(self, settings):
        settings.BAKER_CUSTOM_CLASS = "invalid_module.invalid_class"
        with pytest.raises(CustomBakerNotFound):
            baker.Baker.create(Person)

    @pytest.mark.parametrize("cls", [ClassWithoutMake, ClassWithoutPrepare])
    def test_create_fail_on_missing_required_functions(self, settings, cls):
        settings.BAKER_CUSTOM_CLASS = self.class_to_import_string(cls)
        with pytest.raises(InvalidCustomBaker):
            baker.Baker.create(Person)

    @pytest.mark.parametrize("cls", [BakerSubclass, BakerDuck])
    def test_create_succeeds_with_valid_custom_baker(self, settings, cls):
        settings.BAKER_CUSTOM_CLASS = self.class_to_import_string(cls)
        assert baker.Baker.create(Person).__class__ == cls
