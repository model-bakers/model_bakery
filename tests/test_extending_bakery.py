import pytest

from model_bakery import baker
from model_bakery.exceptions import CustomBakerNotFound, InvalidCustomBaker
from model_bakery.random_gen import gen_from_list
from tests.generic.models import Classroom, Person, Profile


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


class TestSimpleExtendBaker:
    @pytest.mark.django_db
    def test_list_generator_respects_values_from_list(self):
        experient_bakers_factory = ExperientBaker(Person)
        experient_baker = experient_bakers_factory.make()
        assert experient_baker.age in ExperientBaker.age_list


class TestLessSimpleExtendBaker:
    @pytest.mark.django_db
    def test_nonexistent_required_field(self):
        gen_opposite.required = ["house"]
        sad_people_factory = SadPeopleBaker(Person)
        with pytest.raises(AttributeError):
            sad_people_factory.make()

    @pytest.mark.django_db
    def test_string_to_generator_required(self):
        gen_opposite.required = ["default"]
        enjoy_jards_macale_field = Person._meta.get_field("enjoy_jards_macale")
        like_metal_music_field = Person._meta.get_field("like_metal_music")
        sad_people_factory = SadPeopleBaker(Person)
        person = sad_people_factory.make()
        assert person.enjoy_jards_macale is enjoy_jards_macale_field.default
        assert person.like_metal_music is like_metal_music_field.default

    @pytest.mark.django_db
    def test_kwarg_used_over_attr_mapping_generator(self):
        sad_people_factory = SadPeopleBaker(Person)
        person = sad_people_factory.make(name="test")
        assert person.name == "test"

    @pytest.mark.django_db
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


class StrictSignatureBaker(baker.Baker):
    def make(
        self,
        _save_kwargs=None,
        _refresh_after_create=False,
        _from_manager=None,
        _fill_optional=False,
    ):
        return "made"

    def prepare(self, _save_related=False, _fill_optional=False):
        return "prepared"


class StrictGenerateValueBaker(baker.Baker):
    def generate_value(self, field, commit=True):
        return super().generate_value(field, commit)


class TestCustomizeBakerClassViaSettings:
    def class_to_import_string(self, class_to_convert):
        return f"{self.__module__}.{class_to_convert.__name__}"

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

    def test_top_level_make_omits_false_full_clean_for_custom_baker(self, settings):
        settings.BAKER_CUSTOM_CLASS = self.class_to_import_string(StrictSignatureBaker)
        assert baker.make(Person) == "made"

    def test_top_level_prepare_omits_false_full_clean_for_custom_baker(self, settings):
        settings.BAKER_CUSTOM_CLASS = self.class_to_import_string(StrictSignatureBaker)
        assert baker.prepare(Person) == "prepared"

    @pytest.mark.django_db
    def test_true_full_clean_keeps_custom_generate_value_compatible(self, settings):
        settings.BAKER_CUSTOM_CLASS = self.class_to_import_string(
            StrictGenerateValueBaker
        )
        assert baker.make(Profile, _full_clean=True).pk


class TestBakerExtensionState:
    def test_subclass_can_read_and_replace_working_state(self):
        class StateAwareBaker(baker.Baker):
            def _clean_attrs(self, attrs):
                super()._clean_attrs(attrs)
                assert self.model_attrs["name"] == "original"
                assert self.iterator_attrs["age"] is ages
                self.model_attrs = {
                    **self.model_attrs,
                    "name": "custom",
                    "age": replacement_ages,
                }
                self.iterator_attrs = {"age": replacement_ages}

        ages = iter([20, 21])
        replacement_ages = iter([30, 31])
        person = StateAwareBaker(Person).prepare(name="original", age=ages)

        assert person.name == "custom"
        assert person.age == 30
        assert next(ages) == 20
        assert next(replacement_ages) == 31

    @pytest.mark.parametrize("optional", [False, True])
    def test_generator_callbacks_receive_field_context(self, optional):
        def field_context(field):
            return "context", (field._using, field.fill_optional, field.max_length)

        def generate_name(context, _using, fill_optional):
            assert context == (_using, fill_optional, 30)
            return f"{_using}:{fill_optional}"

        generate_name.required = [field_context, "_using", "fill_optional"]

        class FieldAwareBaker(baker.Baker):
            attr_mapping = {"name": generate_name}

            def generate_value(self, field, commit=True):
                assert field.fill_optional is optional
                return super().generate_value(field, commit)

        person = FieldAwareBaker(Person, _using="extra").prepare(
            _fill_optional=optional
        )

        assert person.name == f"extra:{optional}"


class TestPublicBakerWrappers:
    @pytest.mark.django_db
    @pytest.mark.parametrize("operation", ["make", "prepare"])
    def test_wrapper_can_read_completed_state(self, operation):
        completed = []

        class AuditingBaker(baker.Baker):
            def make(self, **attrs):
                instance = super().make(**attrs)
                completed.append(self.model_attrs["email"])
                return instance

            def prepare(self, **attrs):
                instance = super().prepare(**attrs)
                completed.append(self.model_attrs["email"])
                return instance

        factory = AuditingBaker(Profile)
        create = getattr(factory, operation)

        first = create(email="first@example.com")
        second = create(email="second@example.com")

        assert first.email == "first@example.com"
        assert second.email == "second@example.com"
        assert completed == ["first@example.com", "second@example.com"]


@pytest.mark.django_db
@pytest.mark.parametrize("fill_optional", [False, True])
def test_optional_m2m_respects_skip_hook_decision(fill_optional, monkeypatch):
    class OptionalM2MBaker(baker.Baker):
        def _skip_field(self, field):
            skip = super()._skip_field(field)
            if field.name == "students":
                monkeypatch.setattr(field, "fill_optional", fill_optional)
                return False
            return skip

    classroom = OptionalM2MBaker(Classroom, make_m2m=True).make()

    assert classroom.students.count() == (
        baker.MAX_MANY_QUANTITY if fill_optional else 0
    )


class TestContextChangesBeforeSuper:
    @pytest.mark.parametrize("optional", [False, True])
    def test_skip_hook_updates_generator_optional_context(self, optional):
        def field_context(field):
            return "optional", field.fill_optional

        def generate_email(optional, fill_optional):
            assert optional is fill_optional
            return str(optional)

        generate_email.required = [field_context, "fill_optional"]

        class OptionalBaker(baker.Baker):
            attr_mapping = {"email": generate_email}

            def _skip_field(self, field):
                if field.name == "email":
                    self.fill_in_optional = optional
                return super()._skip_field(field)

        instance = OptionalBaker(Profile).prepare(_fill_optional=not optional)

        assert instance.email == str(optional)

    def test_generator_hook_updates_database_context(self):
        def field_context(field):
            return "using", field._using

        def generate_email(using, _using):
            assert using == _using
            return using

        generate_email.required = [field_context, "_using"]

        class RoutingBaker(baker.Baker):
            attr_mapping = {"email": generate_email}

            def generate_value(self, field, commit=True):
                self._using = "extra"
                return super().generate_value(field, commit)

        instance = RoutingBaker(Profile).prepare()

        assert instance.email == "extra"


class TestCreationMethods:
    @pytest.mark.django_db
    def test_make_can_delegate_to_prepare(self):
        completed = []

        class StagedBaker(baker.Baker):
            def make(self, **attrs):
                instance = super().prepare(**attrs)
                assert self.model_attrs["email"] == instance.email
                completed.append(self.model_attrs["email"])
                instance.save()
                return instance

        factory = StagedBaker(Profile)

        first = factory.make(email="first@example.com")
        second = factory.make(email="second@example.com")

        assert first.pk is not None
        assert second.pk is not None
        assert first.email == "first@example.com"
        assert second.email == "second@example.com"
        assert completed == ["first@example.com", "second@example.com"]
        assert Profile.objects.count() == 2
