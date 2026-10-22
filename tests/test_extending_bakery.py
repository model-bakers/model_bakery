from functools import partial, partialmethod

import pytest

from model_bakery import baker
from model_bakery.exceptions import (
    CustomBakerNotFound,
    InvalidCustomBaker,
    RecipeIteratorEmpty,
)
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
                assert self.rel_attrs == {"unused__name": "related"}
                assert self.rel_fields == ["unused"]
                assert self.fill_in_optional is False
                assert self.m2m_dict == {}
                self.rel_attrs = {}
                self.rel_fields = []
                self.fill_in_optional = False
                self.m2m_dict = {}
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
        person = StateAwareBaker(Person).prepare(
            name="original", age=ages, unused__name="related"
        )

        assert person.name == "custom"
        assert person.age == 30
        assert next(ages) == 20
        assert next(replacement_ages) == 31

    @pytest.mark.django_db
    @pytest.mark.parametrize("operation", ["make", "prepare"])
    def test_public_wrapper_can_read_completed_state_after_super(self, operation):
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


class TestGeneratorContext:
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

    @pytest.mark.parametrize("optional", [False, True])
    def test_skip_hook_updates_generator_optional_context_before_super(self, optional):
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

    def test_generator_hook_updates_database_context_before_super(self):
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


class TestOptionalM2MHook:
    @pytest.mark.django_db
    @pytest.mark.parametrize("fill_optional", [False, True])
    def test_optional_m2m_respects_fill_optional_set_by_hook(
        self, fill_optional, monkeypatch
    ):
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


class TestBakerFieldIsolation:
    def test_generator_field_context_survives_nested_generation(self):
        def field_context(field):
            baker.prepare(Person, _using="default", _fill_optional=False)
            return "context", (field._using, field.fill_optional)

        def generate_name(context):
            return f"{context[0]}:{context[1]}"

        generate_name.required = [field_context]

        class FieldAwareBaker(baker.Baker):
            attr_mapping = {"name": generate_name}

        person = FieldAwareBaker(Person, _using="extra").prepare(_fill_optional=True)

        assert person.name == "extra:True"

    def test_hook_observes_generator_callback_changes_across_nested_calls(
        self, monkeypatch
    ):
        nested = []

        def limit_length(field):
            monkeypatch.setattr(field, "max_length", 4)
            nested.append(factory.prepare(email="inner", _fill_optional=False))
            assert field.fill_optional is True
            return "max_length", field.max_length

        def generate_email(max_length):
            return "x" * max_length

        generate_email.required = [limit_length]

        class FieldAwareBaker(baker.Baker):
            attr_mapping = {"email": generate_email}

            def generate_value(self, field, commit=True):
                value = super().generate_value(field, commit)
                assert field.max_length == 4
                return value

        model_field = Profile._meta.get_field("email")
        original_length = model_field.max_length

        factory = FieldAwareBaker(Profile)
        profile = factory.prepare(_fill_optional=True)

        assert profile.email == "xxxx"
        assert nested[0].email == "inner"
        assert model_field.max_length == original_length

    def test_direct_generation_uses_fresh_field_context(self, monkeypatch):
        contexts = []

        def field_context(field):
            contexts.append((field._using, field.fill_optional, field.max_length))
            monkeypatch.setattr(field, "max_length", 4)
            return "max_length", field.max_length

        def generate_email(max_length):
            return "x" * max_length

        generate_email.required = [field_context]

        class FieldAwareBaker(baker.Baker):
            attr_mapping = {"email": generate_email}

        factory = FieldAwareBaker(Profile, _using="extra")
        model_field = Profile._meta.get_field("email")
        original_length = model_field.max_length

        assert factory.prepare().email == "xxxx"
        assert factory.generate_value(model_field, commit=False) == "xxxx"
        factory.fill_in_optional = True
        assert factory.generate_value(model_field, commit=False) == "xxxx"

        assert contexts == [
            ("extra", False, original_length),
            ("extra", False, original_length),
            ("extra", True, original_length),
        ]
        assert model_field.max_length == original_length


class TestPublicBakerWrappers:
    def test_wrapper_failure_keeps_completed_core_state(self):
        class RejectingBaker(baker.Baker):
            def prepare(self, **attrs):
                instance = super().prepare(**attrs)
                if instance.email == "reject@example.com":
                    raise ValueError("rejected by wrapper")
                return instance

        factory = RejectingBaker(Profile)
        factory.prepare(email="first@example.com")

        with pytest.raises(ValueError, match="rejected by wrapper"):
            factory.prepare(email="reject@example.com")

        assert factory.model_attrs["email"] == "reject@example.com"

    @pytest.mark.parametrize("class_dispatch", [False, True])
    def test_nested_success_and_failure_restore_outer_state(self, class_dispatch):
        factory = baker.Baker(Profile)
        nested = []
        create = (
            partial(baker.Baker.prepare, factory) if class_dispatch else factory.prepare
        )

        def email():
            nested.append(create(email="inner@example.com"))
            assert factory.model_attrs["email"] is email
            with pytest.raises(RecipeIteratorEmpty):
                create(email=iter(()))
            assert factory.model_attrs["email"] is email
            return "outer@example.com"

        outer = factory.prepare(email=email)

        assert outer.email == "outer@example.com"
        assert nested[0].email == "inner@example.com"
        assert factory.model_attrs["email"] == "outer@example.com"

    def test_failed_call_restores_last_completed_state(self):
        factory = baker.Baker(Profile)
        factory.prepare(email="first@example.com")

        with pytest.raises(RecipeIteratorEmpty):
            factory.prepare(email=iter(()))

        assert factory.model_attrs["email"] == "first@example.com"
        assert factory.prepare(email="next@example.com").email == "next@example.com"


class TestPublicWrapperInheritance:
    def test_super_chain_can_read_completed_state(self):
        completed = []

        class ParentBaker(baker.Baker):
            def prepare(self, **attrs):
                instance = super().prepare(**attrs)
                completed.append(("parent", self.model_attrs["email"]))
                return instance

        class ChildBaker(ParentBaker):
            def prepare(self, **attrs):
                instance = super().prepare(**attrs)
                completed.append(("child", self.model_attrs["email"]))
                return instance

        factory = ChildBaker(Profile)

        assert factory.prepare(email="first@example.com").email == "first@example.com"
        assert factory.prepare(email="next@example.com").email == "next@example.com"
        assert completed == [
            ("parent", "first@example.com"),
            ("child", "first@example.com"),
            ("parent", "next@example.com"),
            ("child", "next@example.com"),
        ]


def test_inherited_mixin_wrapper_can_read_completed_state():
    completed = []

    class AuditingMixin:
        def prepare(self, **attrs):
            instance = super().prepare(**attrs)
            completed.append(self.model_attrs["email"])
            return instance

    class CustomBaker(AuditingMixin, baker.Baker):
        pass

    factory = CustomBaker(Profile)

    assert factory.prepare(email="first@example.com").email == "first@example.com"
    assert factory.prepare(email="next@example.com").email == "next@example.com"
    assert completed == ["first@example.com", "next@example.com"]


class TestCreationMethods:
    @pytest.mark.parametrize("operation", ["make", "prepare"])
    def test_creation_methods_keep_normal_binding(self, operation):
        factory = baker.Baker(Profile)
        method = getattr(factory, operation)

        assert method.__self__ is factory
        assert method.__func__ is getattr(baker.Baker, operation)
        assert method == getattr(factory, operation)

    def test_partialmethod_keeps_nested_calls_isolated(self):
        class OptionalBaker(baker.Baker):
            prepare = partialmethod(baker.Baker.prepare, _fill_optional=True)

        factory = OptionalBaker(Person)
        inner_objects = []

        def age():
            inner_objects.append(factory.prepare(name="inner", age=10))
            assert factory.model_attrs["name"] == "outer"
            with pytest.raises(RecipeIteratorEmpty):
                factory.prepare(name=iter(()), age=10)
            assert factory.model_attrs["name"] == "outer"
            assert factory.fill_in_optional is True
            return 20

        outer = factory.prepare(name="outer", age=age)

        assert (outer.name, outer.age) == ("outer", 20)
        assert (inner_objects[0].name, inner_objects[0].age) == ("inner", 10)
        assert factory.model_attrs["name"] == "outer"
