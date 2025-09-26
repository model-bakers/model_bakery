import datetime
import itertools
from decimal import Decimal
from unittest.mock import patch

from django.apps import apps
from django.conf import settings
from django.db.models import Manager
from django.db.models.signals import m2m_changed
from django.test import TestCase, override_settings

import pytest

from model_bakery import baker, random_gen
from model_bakery.baker import BAKER_CONTENTTYPES, MAX_MANY_QUANTITY
from model_bakery.exceptions import (
    AmbiguousModelName,
    InvalidQuantityException,
    ModelNotFound,
)
from model_bakery.timezone import tz_aware
from tests.generic import baker_recipes, models
from tests.generic.forms import DummyGenericIPAddressFieldForm


def test_import_seq_from_baker():
    """Test import seq method from baker module."""
    try:
        from model_bakery.baker import seq  # NoQA
    except ImportError:
        pytest.fail(f"{ImportError.__name__} raised")


class TestsModelFinder:
    def test_unicode_regression(self):
        obj = baker.prepare("generic.Person")
        assert isinstance(obj, models.Person)

    def test_model_class(self):
        obj = baker.prepare(models.Person)
        assert isinstance(obj, models.Person)

    def test_app_model_string(self):
        obj = baker.prepare("generic.Person")
        assert isinstance(obj, models.Person)

    def test_model_string(self):
        obj = baker.prepare("Person")
        assert isinstance(obj, models.Person)

    def test_raise_on_ambiguous_model_string(self):
        with pytest.raises(AmbiguousModelName):
            baker.prepare("Ambiguous")

    def test_raise_model_not_found(self):
        with pytest.raises(ModelNotFound):
            baker.Baker("non_existing.Model")

        with pytest.raises(ModelNotFound):
            baker.Baker("NonExistingModel")


class TestRecipeFinder:
    def test_from_app_module(self):
        obj = baker.prepare_recipe("generic.person")
        assert isinstance(obj, models.Person)
        assert obj.name == "John Doe"

    def test_full_path_from_app_module(self):
        obj = baker.prepare_recipe("tests.generic.person")
        assert isinstance(obj, models.Person)
        assert obj.name == "John Doe"

    def test_from_non_app_module(self):
        obj = baker.prepare_recipe("uninstalled.person")
        assert isinstance(obj, models.Person)
        assert obj.name == "Uninstalled"

    def test_full_path_from_non_app_module(self):
        obj = baker.prepare_recipe("tests.uninstalled.person")
        assert isinstance(obj, models.Person)
        assert obj.name == "Uninstalled"

    def test_raise_on_non_module_path(self):
        # Error trying to parse "app_name" + "recipe_name" from provided string
        with pytest.raises(ValueError):
            baker.prepare_recipe("person")


@pytest.mark.django_db
class TestsBakerCreatesSimpleModel:
    def test_consider_real_django_fields_only(self):
        id_ = models.ModelWithImpostorField._meta.get_field("id")
        with patch.object(baker.Baker, "get_fields") as mock:
            f = Manager()
            f.name = "foo"
            mock.return_value = [id_, f]
            try:
                baker.make(models.ModelWithImpostorField)
            except TypeError:
                raise AssertionError("TypeError raised")

    def test_make_should_create_one_object(self):
        person = baker.make(models.Person)
        assert isinstance(person, models.Person)

        # makes sure it is the person we created
        assert models.Person.objects.filter(id=person.id).exists()

    def test_prepare_should_not_persist_one_object(self):
        person = baker.prepare(models.Person)
        assert isinstance(person, models.Person)

        # makes sure database is clean
        assert not models.Person.objects.all().exists()
        assert person.id is None

    def test_non_abstract_model_creation(self):
        person = baker.make(
            models.NonAbstractPerson, name="bob", enjoy_jards_macale=False
        )
        assert isinstance(person, models.NonAbstractPerson)
        assert person.name == "bob"
        assert person.enjoy_jards_macale is False

    def test_abstract_model_subclass_creation(self):
        instance = baker.make(models.SubclassOfAbstract)
        assert isinstance(instance, models.SubclassOfAbstract)
        assert isinstance(instance, models.AbstractModel)
        assert isinstance(instance.name, str)
        assert len(instance.name) == 30
        assert isinstance(instance.height, int)

    def test_multiple_inheritance_creation(self):
        multiple = baker.make(models.DummyMultipleInheritanceModel)
        assert isinstance(multiple, models.DummyMultipleInheritanceModel)
        assert models.Person.objects.filter(id=multiple.id).exists()
        assert models.DummyDefaultFieldsModel.objects.filter(
            default_id=multiple.default_id
        ).exists()


@pytest.mark.django_db
class TestsBakerRepeatedCreatesSimpleModel(TestCase):
    def test_make_should_create_objects_respecting_quantity_parameter(self):
        with self.assertNumQueries(5):
            baker.make(models.Person, _quantity=5)
        assert models.Person.objects.count() == 5

        with self.assertNumQueries(5):
            people = baker.make(models.Person, _quantity=5, name="George Washington")
            assert all(p.name == "George Washington" for p in people)

    def test_make_quantity_respecting_bulk_create_parameter(self):
        query_count = 1
        with self.assertNumQueries(query_count):
            baker.make(models.Person, _quantity=5, _bulk_create=True)
        assert models.Person.objects.count() == 5

        with self.assertNumQueries(query_count):
            people = baker.make(
                models.Person, name="George Washington", _quantity=5, _bulk_create=True
            )
            assert all(p.name == "George Washington" for p in people)

        with self.assertNumQueries(query_count):
            baker.make(models.NonStandardManager, _quantity=3, _bulk_create=True)
            assert getattr(models.NonStandardManager, "objects", None) is None
            assert (
                models.NonStandardManager._base_manager
                == models.NonStandardManager.manager
            )
            assert (
                models.NonStandardManager._default_manager
                == models.NonStandardManager.manager
            )
        assert models.NonStandardManager.manager.count() == 3

    def test_make_raises_correct_exception_if_invalid_quantity(self):
        with pytest.raises(InvalidQuantityException):
            baker.make(_model=models.Person, _quantity="hi")
        with pytest.raises(InvalidQuantityException):
            baker.make(_model=models.Person, _quantity=-1)
        with pytest.raises(InvalidQuantityException):
            baker.make(_model=models.Person, _quantity=0)

    def test_prepare_should_create_objects_respecting_quantity_parameter(self):
        people = baker.prepare(models.Person, _quantity=5)
        assert len(people) == 5
        assert all(not p.id for p in people)

        people = baker.prepare(models.Person, _quantity=5, name="George Washington")
        assert all(p.name == "George Washington" for p in people)

    def test_prepare_raises_correct_exception_if_invalid_quantity(self):
        with pytest.raises(InvalidQuantityException):
            baker.prepare(_model=models.Person, _quantity="hi")
        with pytest.raises(InvalidQuantityException):
            baker.prepare(_model=models.Person, _quantity=-1)
        with pytest.raises(InvalidQuantityException):
            baker.prepare(_model=models.Person, _quantity=0)

    def test_accepts_generators_with_quantity(self):
        baker.make(
            models.Person,
            name=itertools.cycle(["a", "b", "c"]),
            id_document=itertools.cycle(["d1", "d2", "d3", "d4", "d5"]),
            _quantity=5,
        )
        assert models.Person.objects.count() == 5
        p1, p2, p3, p4, p5 = models.Person.objects.all().order_by("pk")
        assert p1.name == "a"
        assert p1.id_document == "d1"
        assert p2.name == "b"
        assert p2.id_document == "d2"
        assert p3.name == "c"
        assert p3.id_document == "d3"
        assert p4.name == "a"
        assert p4.id_document == "d4"
        assert p5.name == "b"
        assert p5.id_document == "d5"

    def test_accepts_generators_with_quantity_for_unique_fields(self):
        baker.make(
            models.DummyUniqueIntegerFieldModel,
            value=itertools.cycle([1, 2, 3]),
            _quantity=3,
        )
        assert models.DummyUniqueIntegerFieldModel.objects.count() == 3
        num_1, num_2, num_3 = models.DummyUniqueIntegerFieldModel.objects.all()
        assert num_1.value == 1
        assert num_2.value == 2
        assert num_3.value == 3

    # skip if auth app is not installed
    @pytest.mark.skipif(
        not apps.is_installed("django.contrib.auth"),
        reason="Django auth app is not installed",
    )
    def test_generators_work_with_user_model(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        baker.make(User, username=itertools.cycle(["a", "b", "c"]), _quantity=3)
        assert User.objects.count() == 3
        u1, u2, u3 = User.objects.all()
        assert u1.username == "a"
        assert u2.username == "b"
        assert u3.username == "c"


@pytest.mark.django_db
class TestBakerPrepareSavingRelatedInstances:
    def test_default_behaviour_for_m2m_and_fk(self):
        dog = baker.prepare(models.Dog)

        assert dog.pk is None
        assert dog.owner.pk is None

        # reverse FK access in Django 4.1 raises ValueError instead of DoesNotExist
        #  https://docs.djangoproject.com/en/4.1/releases/4.1/#reverse-foreign-key-changes-for-unsaved-model-instances
        with pytest.raises(models.Dog.DoesNotExist):
            assert dog.owner.dog_set.get()

        with pytest.raises(ValueError):
            assert dog.friends_with

    def test_create_fk_instances(self):
        dog = baker.prepare(models.Dog, _save_related=True)

        assert dog.pk is None
        assert dog.owner.pk
        with pytest.raises(ValueError):
            assert dog.friends_with

    def test_create_fk_instances_with_quantity(self):
        dog1, dog2 = baker.prepare(models.Dog, _save_related=True, _quantity=2)

        assert dog1.pk is None
        assert dog1.owner.pk
        with pytest.raises(ValueError):
            assert dog1.friends_with

        assert dog2.pk is None
        assert dog2.owner.pk
        with pytest.raises(ValueError):
            assert dog2.friends_with

    def test_create_one_to_one(self):
        lonely_person = baker.prepare(models.LonelyPerson, _save_related=True)

        assert lonely_person.pk is None
        assert lonely_person.only_friend.pk

    def test_recipe_prepare_model_with_one_to_one_and_save_related(self):
        lonely_person = baker_recipes.lonely_person.prepare(_save_related=True)

        assert lonely_person.pk is None
        assert lonely_person.only_friend.pk


@pytest.mark.django_db
class TestBakerCreatesAssociatedModels(TestCase):
    def test_dependent_models_with_ForeignKey(self):
        dog = baker.make(models.Dog)
        assert isinstance(dog.owner, models.Person)

    def test_foreign_key_on_parent_should_create_one_object(self):
        person_count = models.Person.objects.count()
        baker.make(models.GuardDog)
        assert models.Person.objects.count() == person_count + 1

    def test_foreign_key_on_parent_is_not_created(self):
        """Foreign key on parent doesn't get created using owner."""
        owner = baker.make(models.Person)
        person_count = models.Person.objects.count()
        dog = baker.make(models.GuardDog, owner=owner)
        assert models.Person.objects.count() == person_count
        assert dog.owner == owner

    def test_foreign_key_on_parent_id_is_not_created(self):
        """Foreign key on parent doesn't get created using owner_id."""
        owner = baker.make(models.Person)
        person_count = models.Person.objects.count()
        dog = baker.make(models.GuardDog, owner_id=owner.id)
        assert models.Person.objects.count() == person_count
        assert models.GuardDog.objects.get(pk=dog.pk).owner == owner

    def test_auto_now_add_on_parent_should_work(self):
        person_count = models.Person.objects.count()
        dog = baker.make(models.GuardDog)
        assert models.Person.objects.count() == person_count + 1
        assert dog.created

    def test_attrs_on_related_model_through_parent(self):
        baker.make(models.GuardDog, owner__name="john")
        for person in models.Person.objects.all():
            assert person.name == "john"

    def test_access_related_name_of_m2m(self):
        try:
            baker.make(models.Person, classroom_set=[baker.make(models.Classroom)])
        except TypeError:
            raise AssertionError("type error raised")

    def test_save_object_instances_when_handling_one_to_many_relations(self):
        owner = baker.make(models.Person)
        dogs_set = baker.prepare(
            models.Dog,
            owner=owner,
            _quantity=2,
        )

        assert models.Dog.objects.count() == 0  # ensure there are no dogs in our db
        home = baker.make(
            models.Home,
            owner=owner,
            dogs=dogs_set,
        )
        assert home.dogs.count() == 2
        assert models.Dog.objects.count() == 2  # dogs in dogs_set were created

    def test_prepare_fk(self):
        dog = baker.prepare(models.Dog)
        assert isinstance(dog, models.Dog)
        assert isinstance(dog.owner, models.Person)

        assert models.Person.objects.all().count() == 0
        assert models.Dog.objects.all().count() == 0

    def test_create_one_to_one(self):
        lonely_person = baker.make(models.LonelyPerson)

        assert models.LonelyPerson.objects.all().count() == 1
        assert isinstance(lonely_person.only_friend, models.Person)
        assert models.Person.objects.all().count() == 1

    def test_create_multiple_one_to_one(self):
        baker.make(models.LonelyPerson, _quantity=5)
        assert models.LonelyPerson.objects.all().count() == 5
        assert models.Person.objects.all().count() == 5

    def test_bulk_create_multiple_one_to_one(self):
        query_count = 6
        with self.assertNumQueries(query_count):
            baker.make(models.LonelyPerson, _quantity=5, _bulk_create=True)

        assert models.LonelyPerson.objects.all().count() == 5
        assert models.Person.objects.all().count() == 5

    def test_chaining_bulk_create_reduces_query_count(self):
        query_count = 3
        with self.assertNumQueries(query_count):
            baker.make(models.Person, _quantity=5, _bulk_create=True)
            person_iter = models.Person.objects.all().iterator()
            baker.make(
                models.LonelyPerson,
                only_friend=person_iter,
                _quantity=5,
                _bulk_create=True,
            )
            # 2 bulk create and 1 select on Person

        assert models.LonelyPerson.objects.all().count() == 5
        assert models.Person.objects.all().count() == 5

    def test_bulk_create_multiple_fk(self):
        query_count = 6
        with self.assertNumQueries(query_count):
            baker.make(models.PaymentBill, _quantity=5, _bulk_create=True)

        assert models.PaymentBill.objects.all().count() == 5
        assert models.User.objects.all().count() == 5

    def test_create_many_to_many_if_flagged(self):
        store = baker.make(models.Store, make_m2m=True)
        assert store.employees.count() == 5
        assert store.customers.count() == 5

    def test_regression_many_to_many_field_is_accepted_as_kwargs(self):
        employees = baker.make(models.Person, _quantity=3)
        customers = baker.make(models.Person, _quantity=3)

        store = baker.make(models.Store, employees=employees, customers=customers)

        assert store.employees.count() == 3
        assert store.customers.count() == 3
        assert models.Person.objects.count() == 6

    def test_create_many_to_many_with_iter(self):
        students = baker.make(models.Person, _quantity=3)
        classrooms = baker.make(models.Classroom, _quantity=3, students=iter(students))

        assert classrooms[0].students.count() == 1
        assert classrooms[0].students.first() == students[0]
        assert classrooms[1].students.count() == 1
        assert classrooms[1].students.first() == students[1]
        assert classrooms[2].students.count() == 1
        assert classrooms[2].students.first() == students[2]

    def test_create_many_to_many_with_unsaved_iter(self):
        students = baker.prepare(models.Person, _quantity=3)
        classrooms = baker.make(models.Classroom, _quantity=3, students=iter(students))

        assert students[0].pk is not None
        assert students[1].pk is not None
        assert students[2].pk is not None

        assert classrooms[0].students.count() == 1
        assert classrooms[0].students.first() == students[0]
        assert classrooms[1].students.count() == 1
        assert classrooms[1].students.first() == students[1]
        assert classrooms[2].students.count() == 1
        assert classrooms[2].students.first() == students[2]

    def test_create_many_to_many_with_through_and_iter(self):
        students = baker.make(models.Person, _quantity=3)
        schools = baker.make(
            models.School,
            _quantity=3,
            students=iter(students),
        )

        assert schools[0].students.count() == 1
        assert schools[0].students.first() == students[0]
        assert schools[1].students.count() == 1
        assert schools[1].students.first() == students[1]
        assert schools[2].students.count() == 1
        assert schools[2].students.first() == students[2]

    def test_create_many_to_many_with_set_default_quantity(self):
        store = baker.make(models.Store, make_m2m=True)
        assert store.employees.count() == baker.MAX_MANY_QUANTITY
        assert store.customers.count() == baker.MAX_MANY_QUANTITY

    def test_create_many_to_many_with_through_option(self):
        # School student's attr is a m2m relationship with a model through
        school = baker.make(models.School, make_m2m=True)
        assert models.School.objects.count() == 1
        assert school.students.count() == baker.MAX_MANY_QUANTITY
        assert models.SchoolEnrollment.objects.count() == baker.MAX_MANY_QUANTITY
        assert models.Person.objects.count() == baker.MAX_MANY_QUANTITY

    def test_does_not_create_many_to_many_as_default(self):
        store = baker.make(models.Store)
        assert store.employees.count() == 0
        assert store.customers.count() == 0

    def test_does_not_create_nullable_many_to_many_for_relations(self):
        classroom = baker.make(models.Classroom, make_m2m=False)
        assert classroom.students.count() == 0

    def test_nullable_many_to_many_is_not_created_even_if_flagged(self):
        classroom = baker.make(models.Classroom, make_m2m=True)
        assert classroom.students.count() == 0

    def test_m2m_changed_signal_is_fired(self):
        # TODO: Use object attrs instead of mocks for Django 1.4 compat
        self.m2m_changed_fired = False

        def test_m2m_changed(*args, **kwargs):
            self.m2m_changed_fired = True

        m2m_changed.connect(test_m2m_changed, dispatch_uid="test_m2m_changed")
        baker.make(models.Store, make_m2m=True)
        assert self.m2m_changed_fired

    def test_simple_creating_person_with_parameters(self):
        kid = baker.make(models.Person, enjoy_jards_macale=True, age=10, name="Mike")
        assert kid.age == 10
        assert kid.enjoy_jards_macale is True
        assert kid.name == "Mike"

    def test_creating_person_from_factory_using_parameters(self):
        person_baker_ = baker.Baker(models.Person)
        person = person_baker_.make(
            enjoy_jards_macale=False, age=20, gender="M", name="John"
        )
        assert person.age == 20
        assert person.enjoy_jards_macale is False
        assert person.name == "John"
        assert person.gender == "M"

    def test_ForeignKey_model_field_population(self):
        dog = baker.make(models.Dog, breed="X1", owner__name="Bob")
        assert dog.breed == "X1"
        assert dog.owner.name == "Bob"

    def test_ForeignKey_model_field_population_should_work_with_prepare(self):
        dog = baker.prepare(models.Dog, breed="X1", owner__name="Bob")
        assert dog.breed == "X1"
        assert dog.owner.name == "Bob"

    def test_ForeignKey_model_field_population_for_not_required_fk(self):
        user = baker.make(models.User, profile__email="a@b.com")
        assert user.profile.email == "a@b.com"

    def test_does_not_creates_null_ForeignKey(self):
        user = baker.make(models.User)
        assert not user.profile

    def test_passing_m2m_value(self):
        store = baker.make(models.Store, customers=[baker.make(models.Person)])
        assert store.customers.count() == 1

    def test_ensure_recursive_ForeignKey_population(self):
        bill = baker.make(models.PaymentBill, user__profile__email="a@b.com")
        assert bill.user.profile.email == "a@b.com"

    def test_field_lookup_for_m2m_relationship(self):
        store = baker.make(models.Store, suppliers__gender="M")
        suppliers = store.suppliers.all()
        assert suppliers
        for supplier in suppliers:
            assert supplier.gender == "M"

    def test_field_lookup_for_one_to_one_relationship(self):
        lonely_person = baker.make(models.LonelyPerson, only_friend__name="Bob")
        assert lonely_person.only_friend.name == "Bob"

    def test_allow_create_fk_related_model(self):
        try:
            person = baker.make(
                models.Person, dog_set=[baker.make(models.Dog), baker.make(models.Dog)]
            )
        except TypeError:
            raise AssertionError("type error raised")

        assert person.dog_set.count() == 2

    def test_field_lookup_for_related_field(self):
        person = baker.make(
            models.Person,
            one_related__name="Foo",
            fk_related__name="Bar",
        )

        assert person.pk
        assert person.one_related.pk
        assert person.fk_related.count() == 1
        assert person.one_related.name == "Foo"
        assert person.fk_related.get().name == "Bar"

    def test_field_lookup_for_related_field_does_not_work_with_prepare(self):
        person = baker.prepare(
            models.Person,
            one_related__name="Foo",
            fk_related__name="Bar",
        )

        assert not person.pk
        assert models.RelatedNamesModel.objects.count() == 0

    def test_ensure_reverse_fk_for_many_to_one_is_working(self):
        """This is a regression test to make sure issue 291 is fixed."""
        fk1, fk2 = baker.prepare(
            models.Issue291Model3, fk_model_2=None, name="custom name", _quantity=2
        )
        obj = baker.make(
            models.Issue291Model2,
            m2m_model_1=[baker.make(models.Issue291Model1)],
            bazs=[fk1, fk2],
        )

        assert obj.bazs.count() == 2
        related_1, related_2 = obj.bazs.all()
        assert related_1.name == "custom name"
        assert related_2.name == "custom name"


@pytest.mark.django_db
class TestHandlingUnsupportedModels:
    def test_unsupported_model_raises_an_explanatory_exception(self):
        try:
            baker.make(models.UnsupportedModel)
            raise AssertionError("Should have raised a TypeError")
        except TypeError as e:
            assert "not supported" in repr(e)
            assert "field unsupported_field" in repr(e)


@pytest.mark.skipif(
    not BAKER_CONTENTTYPES, reason="Django contenttypes framework is not installed"
)
@pytest.mark.django_db
class TestHandlingModelsWithGenericRelationFields:
    def test_create_model_with_generic_relation(self):
        dummy = baker.make(models.DummyGenericRelationModel)
        assert isinstance(dummy, models.DummyGenericRelationModel)


@pytest.mark.skipif(
    not BAKER_CONTENTTYPES, reason="Django contenttypes framework is not installed"
)
@pytest.mark.django_db
class TestHandlingContentTypeField:
    def test_create_model_with_contenttype_field(self):
        from django.contrib.contenttypes.models import ContentType

        dummy = baker.make(models.DummyGenericForeignKeyModel)
        assert isinstance(dummy, models.DummyGenericForeignKeyModel)
        assert isinstance(dummy.content_type, ContentType)

    def test_create_model_with_contenttype_with_content_object(self):
        """Test creating model with contenttype field and populating that field by function."""
        from django.contrib.contenttypes.models import ContentType

        def get_dummy_key():
            return baker.make("Person")

        dummy = baker.make(
            models.DummyGenericForeignKeyModel, content_object=get_dummy_key
        )
        assert isinstance(dummy, models.DummyGenericForeignKeyModel)
        assert isinstance(dummy.content_type, ContentType)
        assert isinstance(dummy.content_object, models.Person)

    def test_create_model_with_contenttype_field_and_proxy_model(self):
        from django.contrib.contenttypes.models import ContentType

        class ProxyPerson(models.Person):
            class Meta:
                proxy = True
                app_label = "generic"

        dummy = baker.make(
            models.DummyGenericForeignKeyModel,
            content_object=baker.make(ProxyPerson, name="John Doe"),
        )
        dummy.refresh_from_db()
        assert isinstance(dummy, models.DummyGenericForeignKeyModel)
        assert isinstance(dummy.content_type, ContentType)
        assert isinstance(dummy.content_object, ProxyPerson)
        assert dummy.content_object.name == "John Doe"


@pytest.mark.skipif(
    not BAKER_CONTENTTYPES, reason="Django contenttypes framework is not installed"
)
class TestHandlingContentTypeFieldNoQueries:
    def test_create_model_with_contenttype_field(self):
        from django.contrib.contenttypes.models import ContentType

        # Clear ContentType's internal cache so that it *will* try to connect to
        # the database to fetch the corresponding ContentType model for
        # a randomly chosen model.
        ContentType.objects.clear_cache()

        with pytest.warns(
            UserWarning,
            match="Database access disabled, returning ContentType raw instance",
        ):
            dummy = baker.prepare(models.DummyGenericForeignKeyModel)
        assert isinstance(dummy, models.DummyGenericForeignKeyModel)
        assert isinstance(dummy.content_type, ContentType)


@pytest.mark.django_db
class TestSkipNullsTestCase:
    def test_skip_null(self):
        dummy = baker.make(models.DummyNullFieldsModel)
        assert dummy.null_foreign_key is None
        assert dummy.null_integer_field is None


@pytest.mark.django_db
class TestFillNullsTestCase:
    def test_create_nullable_many_to_many_if_flagged_and_fill_field_optional(self):
        classroom = baker.make(
            models.Classroom, make_m2m=True, _fill_optional=["students"]
        )
        assert classroom.students.count() == 5

    def test_create_nullable_many_to_many_if_flagged_and_fill_optional(self):
        classroom = baker.make(models.Classroom, make_m2m=True, _fill_optional=True)
        assert classroom.students.count() == 5

    def test_nullable_many_to_many_is_not_created_if_not_flagged_and_fill_optional(
        self,
    ):
        classroom = baker.make(models.Classroom, make_m2m=False, _fill_optional=True)
        assert classroom.students.count() == 0


@pytest.mark.django_db
class TestSkipBlanksTestCase:
    def test_skip_blank(self):
        dummy = baker.make(models.DummyBlankFieldsModel)
        assert dummy.blank_char_field == ""
        assert dummy.blank_text_field == ""

    def test_skip_blank_with_argument(self):
        dummy = baker.make(models.DummyBlankFieldsModel, _fill_optional=False)
        assert dummy.blank_char_field == ""
        assert dummy.blank_text_field == ""

    def test_skip_blank_when_preparing(self):
        dummy = baker.prepare(models.DummyBlankFieldsModel)
        assert dummy.blank_char_field == ""
        assert dummy.blank_text_field == ""

    def test_skip_blank_when_preparing_with_argument(self):
        dummy = baker.prepare(models.DummyBlankFieldsModel, _fill_optional=False)
        assert dummy.blank_char_field == ""
        assert dummy.blank_text_field == ""


@pytest.mark.django_db
class TestFillBlanksTestCase:
    def test_fill_field_optional(self):
        dummy = baker.make(
            models.DummyBlankFieldsModel, _fill_optional=["blank_char_field"]
        )
        assert len(dummy.blank_char_field) == 50

    def test_fill_field_optional_when_preparing(self):
        dummy = baker.prepare(
            models.DummyBlankFieldsModel, _fill_optional=["blank_char_field"]
        )
        assert len(dummy.blank_char_field) == 50

    def test_fill_wrong_field(self):
        with pytest.raises(AttributeError) as exc_info:
            baker.make(
                models.DummyBlankFieldsModel,
                _fill_optional=["blank_char_field", "wrong"],
            )

        msg = "_fill_optional field(s) ['wrong'] are not related to model DummyBlankFieldsModel"
        assert msg in str(exc_info.value)

    def test_fill_wrong_fields_with_parent(self):
        with pytest.raises(AttributeError):
            baker.make(models.SubclassOfAbstract, _fill_optional=["name", "wrong"])

    def test_fill_many_optional(self):
        dummy = baker.make(
            models.DummyBlankFieldsModel,
            _fill_optional=["blank_char_field", "blank_text_field"],
        )
        assert len(dummy.blank_text_field) == 300

    def test_fill_all_optional(self):
        dummy = baker.make(models.DummyBlankFieldsModel, _fill_optional=True)
        assert len(dummy.blank_char_field) == 50
        assert len(dummy.blank_text_field) == 300

    def test_fill_all_optional_when_preparing(self):
        dummy = baker.prepare(models.DummyBlankFieldsModel, _fill_optional=True)
        assert len(dummy.blank_char_field) == 50
        assert len(dummy.blank_text_field) == 300

    def test_fill_optional_with_integer(self):
        with pytest.raises(TypeError):
            baker.make(models.DummyBlankFieldsModel, _fill_optional=1)

    def test_fill_optional_with_default(self):
        dummy = baker.make(models.DummyDefaultFieldsModel, _fill_optional=True)
        assert dummy.default_callable_int_field == 12
        assert isinstance(dummy.default_callable_datetime_field, datetime.datetime)

    def test_fill_optional_with_default_unknown_class(self):
        dummy = baker.make(models.DummyDefaultFieldsModel, _fill_optional=True)
        assert dummy.default_unknown_class_field == 42


@pytest.mark.django_db
class TestFillAutoFieldsTestCase:
    def test_fill_autofields_with_provided_value(self):
        baker.make(models.DummyEmptyModel, id=237)
        saved_dummy = models.DummyEmptyModel.objects.get()
        assert saved_dummy.id == 237

    def test_keeps_prepare_autovalues(self):
        dummy = baker.prepare(models.DummyEmptyModel, id=543)
        assert dummy.id == 543
        dummy.save()
        saved_dummy = models.DummyEmptyModel.objects.get()
        assert saved_dummy.id == 543


@pytest.mark.django_db
class TestSkipDefaultsTestCase:
    def test_skip_fields_with_default(self):
        dummy = baker.make(models.DummyDefaultFieldsModel)
        assert dummy.default_char_field == "default"
        assert dummy.default_text_field == "default"
        assert dummy.default_int_field == 123
        assert dummy.default_float_field == 123.0
        assert dummy.default_date_field == "2012-01-01"
        assert dummy.default_date_time_field == tz_aware(datetime.datetime(2012, 1, 1))
        assert dummy.default_time_field == "00:00:00"
        assert dummy.default_decimal_field == Decimal("0")
        assert dummy.default_email_field == "foo@bar.org"
        assert dummy.default_slug_field == "a-slug"
        assert dummy.default_unknown_class_field == 42
        assert dummy.default_callable_int_field == 12
        assert isinstance(dummy.default_callable_datetime_field, datetime.datetime)


@pytest.mark.django_db
class TestBakerHandlesModelWithNext:
    def test_creates_instance_for_model_with_next(self):
        instance = baker.make(
            models.BaseModelForNext,
            fk=baker.make(models.ModelWithNext),
        )

        assert instance.id
        assert instance.fk.id
        assert instance.fk.attr
        assert instance.fk.next() == "foo"


@pytest.mark.django_db
class TestBakerHandlesModelWithList:
    def test_creates_instance_for_model_with_list(self):
        instance = baker.make(models.BaseModelForList, fk=["foo"])

        assert instance.id
        assert instance.fk == ["foo"]


@pytest.mark.django_db
class TestBakerGeneratesIPAddresses:
    def test_create_model_with_valid_ips(self):
        form_data = {
            "ipv4_field": random_gen.gen_ipv4(),
            "ipv6_field": random_gen.gen_ipv6(),
            "ipv46_field": random_gen.gen_ipv46(),
        }
        assert DummyGenericIPAddressFieldForm(form_data).is_valid()


class TestBakerAllowsSaveParameters(TestCase):
    databases = ["default", settings.EXTRA_DB]

    def test_allows_save_kwargs_on_baker_make(self):
        owner = baker.make(models.Person)
        dog = baker.make(models.ModelWithOverwrittenSave, _save_kwargs={"owner": owner})
        assert owner == dog.owner

        dog1, dog2 = baker.make(
            models.ModelWithOverwrittenSave, _save_kwargs={"owner": owner}, _quantity=2
        )
        assert dog1.owner == owner
        assert dog2.owner == owner

    def test_allow_user_to_specify_database_via_save_kwargs_for_retro_compatibility(
        self,
    ):
        profile = baker.make(models.Profile, _save_kwargs={"using": settings.EXTRA_DB})
        qs = models.Profile.objects.using(settings.EXTRA_DB).all()

        assert qs.count() == 1
        assert profile in qs


class TestBakerSupportsMultiDatabase(TestCase):
    databases = ["default", settings.EXTRA_DB]

    def test_allow_user_to_specify_database_via_using(self):
        profile = baker.make(models.Profile, _using=settings.EXTRA_DB)
        qs = models.Profile.objects.using(settings.EXTRA_DB).all()

        assert qs.count() == 1
        assert profile in qs

    def test_related_fk_database_specified_via_using_kwarg(self):
        dog = baker.make(models.Dog, _using=settings.EXTRA_DB)
        dog_qs = models.Dog.objects.using(settings.EXTRA_DB).all()
        assert dog_qs.count() == 1
        assert dog in dog_qs

        person_qs = models.Person.objects.using(settings.EXTRA_DB).all()
        assert person_qs.count() == 1
        assert dog.owner in person_qs

    def test_allow_user_to_specify_database_via_using_combined_with_bulk_create(
        self,
    ):
        baker.make(
            models.Profile, _using=settings.EXTRA_DB, _quantity=10, _bulk_create=True
        )
        qs = models.Profile.objects.using(settings.EXTRA_DB).all()

        assert qs.count() == 10

    def test_related_fk_database_specified_via_using_kwarg_combined_with_quantity(self):
        dogs = baker.make(models.Dog, _using=settings.EXTRA_DB, _quantity=5)
        dog_qs = models.Dog.objects.using(settings.EXTRA_DB).all()
        person_qs = models.Person.objects.using(settings.EXTRA_DB).all()

        assert person_qs.count() == 5
        assert dog_qs.count() == 5
        for dog in dogs:
            assert dog in dog_qs
            assert dog.owner in person_qs

    def test_related_fk_database_specified_via_using_kwarg_combined_with_bulk_create(
        self,
    ):
        # A custom router must be used when using bulk create and saving
        # related objects in a multi-database setting.
        class AllowRelationRouter:
            """Custom router that allows saving of relations."""

            def allow_relation(self, obj1, obj2, **hints):
                """Allow all relations."""
                return True

        with override_settings(DATABASE_ROUTERS=[AllowRelationRouter()]):
            baker.make(
                models.PaymentBill,
                _quantity=5,
                _bulk_create=True,
                _using=settings.EXTRA_DB,
            )

        assert models.PaymentBill.objects.all().using(settings.EXTRA_DB).count() == 5
        assert models.User.objects.all().using(settings.EXTRA_DB).count() == 5

        # Default router will not be able to save the related objects
        with pytest.raises(ValueError):
            baker.make(
                models.PaymentBill,
                _quantity=5,
                _bulk_create=True,
                _using=settings.EXTRA_DB,
            )

    def test_allow_recipe_to_specify_database_via_using(self):
        dog = baker.make_recipe("generic.homeless_dog", _using=settings.EXTRA_DB)
        qs = models.Dog.objects.using(settings.EXTRA_DB).all()
        assert qs.count() == 1
        assert dog in qs

    def test_recipe_related_fk_database_specified_via_using_kwarg(self):
        dog = baker.make_recipe("generic.dog", _using=settings.EXTRA_DB)
        dog_qs = models.Dog.objects.using(settings.EXTRA_DB).all()
        person_qs = models.Person.objects.using(settings.EXTRA_DB).all()
        dog.refresh_from_db()
        assert dog.owner
        assert dog_qs.count() == 1
        assert dog in dog_qs
        assert person_qs.count() == 1
        assert dog.owner in person_qs

    def test_recipe_related_fk_database_specified_via_using_kwarg_and_quantity(self):
        dogs = baker.make_recipe("generic.dog", _using=settings.EXTRA_DB, _quantity=5)
        dog_qs = models.Dog.objects.using(settings.EXTRA_DB).all()
        person_qs = models.Person.objects.using(settings.EXTRA_DB).all()
        assert dog_qs.count() == 5
        # since we're using recipes, all dogs belong to the same owner
        assert person_qs.count() == 1
        for dog in dogs:
            dog.refresh_from_db()
            assert dog in dog_qs
            assert dog.owner in person_qs

    def test_related_m2m_database_specified_via_using_kwarg(self):
        baker.make(models.Dog, _using=settings.EXTRA_DB, make_m2m=True)
        dog_qs = models.Dog.objects.using(settings.EXTRA_DB).all()
        assert dog_qs.count() == MAX_MANY_QUANTITY + 1
        assert not models.Dog.objects.exists()

    def test_related_m2m_database_specified_via_using_kwarg_and_quantity(self):
        qtd = 3
        baker.make(models.Dog, _using=settings.EXTRA_DB, make_m2m=True, _quantity=qtd)
        dog_qs = models.Dog.objects.using(settings.EXTRA_DB).all()
        assert dog_qs.count() == MAX_MANY_QUANTITY * qtd + qtd
        assert not models.Dog.objects.exists()

    def test_create_many_to_many_with_through_option_and_custom_db(self):
        # School student's attr is a m2m relationship with a model through
        school = baker.make(models.School, make_m2m=True, _using=settings.EXTRA_DB)
        assert models.School.objects.using(settings.EXTRA_DB).count() == 1
        assert (
            school.students.using(settings.EXTRA_DB).count() == baker.MAX_MANY_QUANTITY
        )
        assert (
            models.SchoolEnrollment.objects.using(settings.EXTRA_DB).count()
            == baker.MAX_MANY_QUANTITY
        )
        assert (
            models.Person.objects.using(settings.EXTRA_DB).count()
            == baker.MAX_MANY_QUANTITY
        )

    def test_recipe_m2m_with_custom_db(self):
        school = baker.make_recipe(
            "generic.paulo_freire_school", _using=settings.EXTRA_DB, make_m2m=True
        )
        school.refresh_from_db()
        assert school.pk
        assert school.name == "Escola Municipal Paulo Freire"
        assert models.School.objects.using(settings.EXTRA_DB).count() == 1
        assert (
            school.students.using(settings.EXTRA_DB).count() == baker.MAX_MANY_QUANTITY
        )
        assert (
            models.SchoolEnrollment.objects.using(settings.EXTRA_DB).count()
            == baker.MAX_MANY_QUANTITY
        )
        assert (
            models.Person.objects.using(settings.EXTRA_DB).count()
            == baker.MAX_MANY_QUANTITY
        )

        assert not models.School.objects.exists()
        assert not models.SchoolEnrollment.objects.exists()
        assert not models.Person.objects.exists()


@pytest.mark.django_db
class TestBakerAutomaticallyRefreshFromDB:
    def test_refresh_from_db_if_true(self):
        person = baker.make(
            models.Person, birthday="2017-02-01", _refresh_after_create=True
        )

        assert person.birthday == datetime.date(2017, 2, 1)

    def test_do_not_refresh_from_db_if_false(self):
        person = baker.make(
            models.Person, birthday="2017-02-01", _refresh_after_create=False
        )

        assert person.birthday == "2017-02-01"
        assert person.birthday != datetime.date(2017, 2, 1)

    def test_do_not_refresh_from_db_by_default(self):
        person = baker.make(models.Person, birthday="2017-02-01")

        assert person.birthday == "2017-02-01"
        assert person.birthday != datetime.date(2017, 2, 1)


@pytest.mark.django_db
class TestBakerMakeCanFetchInstanceFromDefaultManager:
    def test_annotation_within_manager_get_queryset_are_run_on_make(self):
        """A custom model Manager can be used within make().

        Passing ``_from_manager='objects'`` will force ``baker.make()``
        to return an instance that has been going through a given
        Manager, thus calling its ``get_queryset()`` method and associated
        code, like default annotations. As such the instance will have
        the same fields as one created in the application.

        """
        movie = baker.make(models.MovieWithAnnotation)
        with pytest.raises(AttributeError):
            assert movie.name

        movie = baker.make(
            models.MovieWithAnnotation,
            title="Old Boy",
            _from_manager="objects",
        )
        assert movie.title == movie.name


@pytest.mark.django_db
class TestCreateM2MWhenBulkCreate(TestCase):
    def test_create(self):
        person = baker.make(models.Person)

        with self.assertNumQueries(11):
            baker.make(
                models.Classroom, students=[person], _quantity=10, _bulk_create=True
            )
        c1, c2 = models.Classroom.objects.all()[:2]
        assert list(c1.students.all()) == list(c2.students.all()) == [person]

    def test_make_should_create_objects_using_reverse_name(self):
        classroom = baker.make(models.Classroom)

        with self.assertNumQueries(21):
            baker.make(
                models.Person,
                classroom_set=[classroom],
                _quantity=10,
                _bulk_create=True,
            )
        s1, s2 = models.Person.objects.all()[:2]
        assert (
            list(s1.classroom_set.all()) == list(s2.classroom_set.all()) == [classroom]
        )


class TestBakerSeeded:
    @pytest.fixture()
    def reset_seed(self):
        old_state = random_gen.baker_random.getstate()
        yield
        random_gen.baker_random.setstate(old_state)
        baker.Baker._global_seed = baker.Baker.SENTINEL

    @pytest.mark.django_db
    def test_seed(self, reset_seed):
        baker.seed(1)
        assert baker.Baker._global_seed == 1
        assert random_gen.gen_integer() == 55195912693

    @pytest.mark.django_db
    def test_unseeded(self):
        assert baker.Baker._global_seed is baker.Baker.SENTINEL


class TestAutoNowFields:
    @pytest.mark.django_db
    @pytest.mark.parametrize("use_tz", [False, True])
    def test_make_with_auto_now(self, use_tz, settings):
        settings.USE_TZ = use_tz
        tzinfo = datetime.timezone.utc if use_tz else None

        now = datetime.datetime(2023, 10, 20, 15, 30).replace(tzinfo=tzinfo)

        instance = baker.make(
            models.ModelWithAutoNowFields,
            created=now,
            updated=now,
            sent_date=now,
        )

        assert instance.created == now
        assert instance.updated == now
        assert instance.sent_date == now

        # Should not update after refreshing from the db
        instance.refresh_from_db()
        assert instance.created == now
        assert instance.updated == now
        assert instance.sent_date == now

    @pytest.mark.django_db
    def test_make_with_auto_now_and_fill_optional(self):
        instance = baker.make(
            models.ModelWithAutoNowFields,
            _fill_optional=True,
        )
        created, updated, sent_date = (
            instance.created,
            instance.updated,
            instance.sent_date,
        )

        # Should not update after refreshing from the db
        instance.refresh_from_db()
        assert instance.created == created
        assert instance.updated == updated
        assert instance.sent_date == sent_date
