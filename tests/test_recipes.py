import itertools
from datetime import timedelta
from decimal import Decimal
from random import choice  # noqa
from unittest.mock import patch

from django.db import connection
from django.utils.timezone import now

import pytest

from model_bakery import baker
from model_bakery.exceptions import InvalidQuantityException, RecipeIteratorEmpty
from model_bakery.recipe import Recipe, RecipeForeignKey, foreign_key, seq
from model_bakery.timezone import tz_aware
from tests.generic.baker_recipes import SmallDogRecipe, pug
from tests.generic.models import (
    TEST_TIME,
    Dog,
    DummyBlankFieldsModel,
    DummyNumbersModel,
    LonelyPerson,
    ModelWithAutoNowFields,
    Person,
    Profile,
    User,
)

recipe_attrs = {
    "name": "John Doe",
    "nickname": "joe",
    "age": 18,
    "bio": "Someone in the crowd",
    "birthday": now().date(),
    "appointment": now(),
    "blog": "https://joe.example.com",
    "days_since_last_login": 4,
    "birth_time": now(),
    "data": {"one": 1},
}
person_recipe = Recipe(Person, **recipe_attrs)
user_recipe = Recipe(User)
lonely_person_recipe = Recipe(LonelyPerson)


def test_import_seq_from_recipe():
    """Import seq method directly from recipe module."""
    try:
        from model_bakery.recipe import seq  # NoQA
    except ImportError:
        pytest.fail(f"{ImportError.__name__} raised")


def test_import_recipes():
    """Test imports works both for full import paths and for `app_name.recipe_name` strings."""
    assert baker.prepare_recipe("generic.dog"), baker.prepare_recipe(
        "tests.generic.dog"
    )


class TestDefiningRecipes:
    @pytest.mark.django_db
    def test_flat_model_make_recipe_with_the_correct_attributes(self):
        """Test a 'flat model' - without associations, like FK, M2M and O2O."""
        person = person_recipe.make()
        assert person.name == recipe_attrs["name"]
        assert person.nickname == recipe_attrs["nickname"]
        assert person.age == recipe_attrs["age"]
        assert person.bio == recipe_attrs["bio"]
        assert person.birthday == recipe_attrs["birthday"]
        assert person.appointment == recipe_attrs["appointment"]
        assert person.blog == recipe_attrs["blog"]
        assert person.days_since_last_login == recipe_attrs["days_since_last_login"]
        assert person.data is not recipe_attrs["data"]
        assert person.data == recipe_attrs["data"]
        assert person.id is not None

    def test_flat_model_prepare_recipe_with_the_correct_attributes(self):
        person = person_recipe.prepare()
        assert person.name == recipe_attrs["name"]
        assert person.nickname == recipe_attrs["nickname"]
        assert person.age == recipe_attrs["age"]
        assert person.bio == recipe_attrs["bio"]
        assert person.birthday == recipe_attrs["birthday"]
        assert person.appointment == recipe_attrs["appointment"]
        assert person.blog == recipe_attrs["blog"]
        assert person.days_since_last_login == recipe_attrs["days_since_last_login"]
        assert person.data is not recipe_attrs["data"]
        assert person.data == recipe_attrs["data"]
        assert person.id is None

    @pytest.mark.django_db
    def test_accepts_callable(self):
        r = Recipe(DummyBlankFieldsModel, blank_char_field=lambda: "callable!!")
        value = r.make().blank_char_field
        assert value == "callable!!"

    @pytest.mark.django_db
    def test_always_calls_when_creating(self):
        with patch("tests.test_recipes.choice") as choice_mock:
            choice_mock.return_value = "foo"
            lst = ["foo", "bar", "spam", "eggs"]
            r = Recipe(DummyBlankFieldsModel, blank_char_field=lambda: choice_mock(lst))
            assert r.make().blank_char_field
            assert r.make().blank_char_field
            assert choice_mock.call_count == 2

    @pytest.mark.django_db
    def test_always_calls_with_quantity(self):
        with patch("tests.test_recipes.choice") as choice_mock:
            choice_mock.return_value = "foo"
            lst = ["foo", "bar", "spam", "eggs"]
            r = Recipe(DummyBlankFieldsModel, blank_char_field=lambda: choice_mock(lst))
            r.make(_quantity=3)
            assert choice_mock.call_count == 3

    @pytest.mark.django_db
    def test_make_recipes_with_args(self):
        """Overriding some fields values at recipe execution."""
        person = person_recipe.make(name="Guido", age=56)
        assert person.name != recipe_attrs["name"]
        assert person.name == "Guido"

        assert person.age != recipe_attrs["age"]
        assert person.age == 56

        assert person.nickname == recipe_attrs["nickname"]
        assert person.bio == recipe_attrs["bio"]
        assert person.birthday == recipe_attrs["birthday"]
        assert person.appointment == recipe_attrs["appointment"]
        assert person.blog == recipe_attrs["blog"]
        assert person.days_since_last_login == recipe_attrs["days_since_last_login"]
        assert person.id is not None

    def test_prepare_recipes_with_args(self):
        """Overriding some fields values at recipe execution."""
        person = person_recipe.prepare(name="Guido", age=56)
        assert person.name != recipe_attrs["name"]
        assert person.name == "Guido"

        assert person.age != recipe_attrs["age"]
        assert person.age == 56

        assert person.nickname == recipe_attrs["nickname"]
        assert person.bio == recipe_attrs["bio"]
        assert person.birthday == recipe_attrs["birthday"]
        assert person.appointment == recipe_attrs["appointment"]
        assert person.blog == recipe_attrs["blog"]
        assert person.days_since_last_login == recipe_attrs["days_since_last_login"]
        assert person.id is None

    @pytest.mark.django_db
    def test_make_recipe_without_all_model_needed_data(self):
        person_recipe = Recipe(Person, name="John Doe")
        person = person_recipe.make()
        assert person.name == "John Doe"
        assert person.nickname
        assert person.age
        assert person.bio
        assert person.birthday
        assert person.appointment
        assert person.blog
        assert person.days_since_last_login
        assert person.id

    def test_prepare_recipe_without_all_model_needed_data(self):
        person_recipe = Recipe(Person, name="John Doe")
        person = person_recipe.prepare()
        assert person.name == "John Doe"
        assert person.nickname
        assert person.age
        assert person.bio
        assert person.birthday
        assert person.appointment
        assert person.blog
        assert person.days_since_last_login
        assert not person.id

    @pytest.mark.django_db
    def test_defining_recipes_str(self):
        p = Recipe("generic.Person", name=seq("foo"))
        try:
            p.make(_quantity=5)
        except AttributeError as e:
            pytest.fail(f"{e}")

    @pytest.mark.django_db
    def test_recipe_dict_attribute_isolation(self):
        person1 = person_recipe.make()
        person2 = person_recipe.make()
        person2.data["two"] = 2
        person3 = person_recipe.make()

        # Mutation on instances must have no side effect on their recipe definition,
        # or on other instances of the same recipe.
        assert person1.data == {"one": 1}
        assert person2.data == {"one": 1, "two": 2}
        assert person3.data == {"one": 1}

    @pytest.mark.skipif(
        connection.vendor != "postgresql", reason="PostgreSQL specific tests"
    )
    @pytest.mark.django_db
    def test_recipe_list_attribute_isolation(self):
        pg_person_recipe = person_recipe.extend(acquaintances=[1, 2, 3])
        person1 = pg_person_recipe.make()
        person2 = pg_person_recipe.make()
        person2.acquaintances.append(4)
        person3 = pg_person_recipe.make()

        # Mutation on instances must have no side effect on their recipe definition,
        # or on other instances of the same recipe.
        assert person1.acquaintances == [1, 2, 3]
        assert person2.acquaintances == [1, 2, 3, 4]
        assert person3.acquaintances == [1, 2, 3]


class TestExecutingRecipes:
    """Tests for calling recipes defined in baker_recipes.py."""

    @pytest.mark.django_db
    def test_model_with_foreign_key(self):
        dog = baker.make_recipe("tests.generic.dog")
        assert dog.breed == "Pug"
        assert isinstance(dog.owner, Person)
        assert dog.owner.id

        dog = baker.prepare_recipe("tests.generic.dog")
        assert dog.breed == "Pug"
        assert isinstance(dog.owner, Person)
        assert dog.owner.id is None

        dog = baker.prepare_recipe("tests.generic.dog", _save_related=True)
        assert dog.breed == "Pug"
        assert isinstance(dog.owner, Person)
        assert dog.owner.id

        dogs = baker.make_recipe("tests.generic.dog", _quantity=2)
        owner = dogs[0].owner
        for dog in dogs:
            assert dog.breed == "Pug"
            assert dog.owner == owner

    @pytest.mark.django_db
    def test_model_with_foreign_key_as_str(self):
        dog = baker.make_recipe("tests.generic.other_dog")
        assert dog.breed == "Basset"
        assert isinstance(dog.owner, Person)
        assert dog.owner.id

        dog = baker.prepare_recipe("tests.generic.other_dog")
        assert dog.breed == "Basset"
        assert isinstance(dog.owner, Person)
        assert dog.owner.id is None

    @pytest.mark.django_db
    def test_model_with_foreign_key_as_unicode(self):
        dog = baker.make_recipe("tests.generic.other_dog_unicode")
        assert dog.breed == "Basset"
        assert isinstance(dog.owner, Person)
        assert dog.owner.id

        dog = baker.prepare_recipe("tests.generic.other_dog_unicode")
        assert dog.breed == "Basset"
        assert isinstance(dog.owner, Person)
        assert dog.owner.id is None

    @pytest.mark.django_db
    def test_make_recipe(self):
        person = baker.make_recipe("tests.generic.person")
        assert isinstance(person, Person)
        assert person.id

    @pytest.mark.django_db
    def test_make_recipe_with_quantity_parameter(self):
        people = baker.make_recipe("tests.generic.person", _quantity=3)
        assert len(people) == 3
        for person in people:
            assert isinstance(person, Person)
            assert person.id

    @pytest.mark.django_db
    def test_make_extended_recipe(self):
        extended_dog = baker.make_recipe("tests.generic.extended_dog")
        assert extended_dog.breed == "Super basset"
        # No side effects happened due to a recipe extension
        base_dog = baker.make_recipe("tests.generic.dog")
        assert base_dog.breed == "Pug"

    @pytest.mark.django_db
    def test_extended_recipe_type(self):
        assert isinstance(pug, SmallDogRecipe)

    @pytest.mark.django_db
    def test_save_related_instances_on_prepare_recipe(self):
        dog = baker.prepare_recipe("tests.generic.homeless_dog")
        assert not dog.id
        assert not dog.owner_id

        dog = baker.prepare_recipe("tests.generic.homeless_dog", _save_related=True)
        assert not dog.id
        assert dog.owner.id

    @pytest.mark.django_db
    def test_make_recipe_with_quantity_parameter_respecting_model_args(self):
        people = baker.make_recipe(
            "tests.generic.person", _quantity=3, name="Dennis Ritchie", age=70
        )
        assert len(people) == 3
        for person in people:
            assert person.name == "Dennis Ritchie"
            assert person.age == 70

    def test_make_recipe_raises_correct_exception_if_invalid_quantity(self):
        with pytest.raises(InvalidQuantityException):
            baker.make_recipe("tests.generic.person", _quantity="hi")
        with pytest.raises(InvalidQuantityException):
            baker.make_recipe("tests.generic.person", _quantity=-1)

    def test_prepare_recipe_with_foreign_key(self):
        person_recipe = Recipe(Person, name="John Doe")
        dog_recipe = Recipe(
            Dog,
            owner=foreign_key(person_recipe),
        )
        dog = dog_recipe.prepare()

        assert dog.id is None
        assert dog.owner.id is None

    def test_prepare_recipe_with_quantity_parameter(self):
        people = baker.prepare_recipe("tests.generic.person", _quantity=3)
        assert len(people) == 3
        for person in people:
            assert isinstance(person, Person)
            assert person.id is None

    def test_prepare_recipe_with_quantity_parameter_respecting_model_args(self):
        people = baker.prepare_recipe(
            "tests.generic.person", _quantity=3, name="Dennis Ritchie", age=70
        )
        assert len(people) == 3
        for person in people:
            assert person.name == "Dennis Ritchie"
            assert person.age == 70

    def test_prepare_recipe_raises_correct_exception_if_invalid_quantity(self):
        with pytest.raises(InvalidQuantityException):
            baker.prepare_recipe("tests.generic.person", _quantity="hi")
        with pytest.raises(InvalidQuantityException):
            baker.prepare_recipe("tests.generic.person", _quantity=-1)

    def test_prepare_recipe(self):
        person = baker.prepare_recipe("tests.generic.person")
        assert isinstance(person, Person)
        assert not person.id

    @pytest.mark.django_db
    def test_make_recipe_with_args(self):
        person = baker.make_recipe(
            "tests.generic.person", name="Dennis Ritchie", age=70
        )
        assert person.name == "Dennis Ritchie"
        assert person.age == 70

    def test_prepare_recipe_with_args(self):
        person = baker.prepare_recipe(
            "tests.generic.person", name="Dennis Ritchie", age=70
        )
        assert person.name == "Dennis Ritchie"
        assert person.age == 70

    def test_import_recipe_inside_deeper_modules(self):
        recipe_name = "tests.generic.tests.sub_package.person"
        person = baker.prepare_recipe(recipe_name)
        assert person.name == "John Deeper"

    @pytest.mark.django_db
    def test_pass_save_kwargs(self):
        owner = baker.make(Person)

        dog = baker.make_recipe(
            "tests.generic.overwritten_save", _save_kwargs={"owner": owner}
        )
        assert owner == dog.owner

    @pytest.mark.django_db
    def test_pass_save_kwargs_in_recipe_definition(self):
        dog = baker.make_recipe("tests.generic.with_save_kwargs")
        assert dog.breed == "updated_breed"

    @pytest.mark.django_db
    def test_ip_fields_with_start(self):
        first, second = baker.make_recipe("tests.generic.ip_fields", _quantity=2)

        assert first.ipv4_field == "127.0.0.2"
        assert first.ipv6_field == "2001:12f8:0:28::4"
        assert second.ipv4_field == "127.0.0.4"
        assert second.ipv6_field == "2001:12f8:0:28::6"


class TestForeignKey:
    def test_foreign_key_method_returns_a_recipe_foreign_key_object(self):
        number_recipe = Recipe(DummyNumbersModel, float_field=1.6)
        obj = foreign_key(number_recipe)
        assert isinstance(obj, RecipeForeignKey)

    def test_not_accept_other_type(self):
        with pytest.raises(TypeError) as c:
            foreign_key(2)
        exception = c.value
        assert str(exception) == "Not a recipe"

    @pytest.mark.django_db
    def test_load_from_other_module_recipe(self):
        dog = Recipe(Dog, owner=foreign_key("tests.generic.person")).make()
        assert dog.owner.name == "John Doe"

    def test_fail_load_invalid_recipe(self):
        with pytest.raises(AttributeError):
            foreign_key("tests.generic.nonexisting_recipe")

    def test_class_directly_with_string(self):
        with pytest.raises(TypeError):
            RecipeForeignKey("foo")

    @pytest.mark.django_db
    def test_do_not_create_related_model(self):
        """It should not create another object when passing the object as argument."""
        person = baker.make_recipe("tests.generic.person")
        assert Person.objects.count() == 1
        baker.make_recipe("tests.generic.dog", owner=person)
        assert Person.objects.count() == 1
        baker.prepare_recipe("tests.generic.dog", owner=person)
        assert Person.objects.count() == 1

    @pytest.mark.django_db
    def test_do_query_lookup_for_recipes_make_method(self):
        """It should not create another object when using query lookup syntax."""
        dog = baker.make_recipe("tests.generic.dog", owner__name="James")
        assert Person.objects.count() == 1
        assert dog.owner.name == "James"

    def test_do_query_lookup_for_recipes_prepare_method(self):
        """It should not create another object when using query lookup syntax."""
        dog = baker.prepare_recipe("tests.generic.dog", owner__name="James")
        assert dog.owner.name == "James"

    @pytest.mark.django_db
    def test_do_query_lookup_empty_recipes(self):
        """It should not create another object when using query lookup syntax."""
        dog_recipe = Recipe(Dog)
        dog = dog_recipe.make(owner__name="James")
        assert Person.objects.count() == 1
        assert dog.owner.name == "James"

        dog = dog_recipe.prepare(owner__name="Zezin")
        assert Person.objects.count() == 1
        assert dog.owner.name == "Zezin"

    @pytest.mark.django_db
    def test_related_models_recipes(self):
        lady = baker.make_recipe("tests.generic.dog_lady")
        assert lady.dog_set.count() == 2
        assert lady.dog_set.all()[0].breed == "Pug"
        assert lady.dog_set.all()[1].breed == "Basset"

    @pytest.mark.django_db
    def test_related_fk_does_not_create_duplicate_parent(self):
        """Regression test for issue #397.

        When using related() with FK, the parent should be reused,
        not duplicated by the child recipe's foreign_key().
        """
        from tests.generic.models import Person

        lady = baker.make_recipe("tests.generic.dog_lady")
        assert Person.objects.count() == 1
        assert lady.dog_set.count() == 2
        for dog in lady.dog_set.all():
            assert dog.owner == lady

    @pytest.mark.django_db
    def test_related_models_recipes_make_mutiple(self):
        ladies = baker.make_recipe("tests.generic.dog_lady", _quantity=2)
        assert ladies[0].dog_set.count() == 2
        assert ladies[1].dog_set.count() == 2

    @pytest.mark.django_db
    def test_nullable_related(self):
        nullable = baker.make_recipe("tests.generic.nullable_related")
        assert nullable.dummynullfieldsmodel_set.count() == 1

    @pytest.mark.django_db
    def test_chained_related(self):
        movie = baker.make_recipe("tests.generic.movie_with_cast")
        assert movie.cast_members.count() == 2

    @pytest.mark.django_db
    def test_one_to_one_relationship(self):
        lonely_people = baker.make_recipe("tests.generic.lonely_person", _quantity=2)
        friend_ids = {x.only_friend.id for x in lonely_people}
        assert len(friend_ids) == 2


class TestM2MField:
    @pytest.mark.django_db
    def test_create_many_to_many(self):
        dog = baker.make_recipe("tests.generic.dog_with_friends")
        assert len(dog.friends_with.all()) == 2
        for friend in dog.friends_with.all():
            assert friend.breed == "Pug"
            assert friend.owner.name == "John Doe"

    @pytest.mark.django_db
    def test_create_nested(self):
        dog = baker.make_recipe("tests.generic.dog_with_more_friends")
        assert len(dog.friends_with.all()) == 1
        friend = dog.friends_with.all()[0]
        assert len(friend.friends_with.all()) == 2


class TestSequences:
    @pytest.mark.django_db
    def test_increment_for_strings(self):
        person = baker.make_recipe("tests.generic.serial_person")
        assert person.name == "joe1"
        person = baker.prepare_recipe("tests.generic.serial_person")
        assert person.name == "joe2"
        person = baker.make_recipe("tests.generic.serial_person")
        assert person.name == "joe3"

    @pytest.mark.django_db
    def test_increment_for_strings_with_suffix(self):
        fred_person = person_recipe.extend(email=seq("fred", suffix="@example.com"))
        person = fred_person.make()
        assert person.email == "fred1@example.com"
        person = fred_person.make()
        assert person.email == "fred2@example.com"
        person = fred_person.make()
        assert person.email == "fred3@example.com"

    @pytest.mark.django_db
    def test_increment_for_fks(self):
        profiles = baker.make(Profile, _quantity=3)
        start_id = profiles[0].id
        seq_user = user_recipe.extend(username="name", profile_id=seq(start_id))
        user = seq_user.make()
        assert user.profile_id == start_id + 1
        user = seq_user.make()
        assert user.profile_id == start_id + 2

    @pytest.mark.django_db
    def test_increment_for_one_to_one(self):
        people = baker.make(Person, _quantity=3)
        start_id = people[0].id
        seq_lonely_person = lonely_person_recipe.extend(only_friend_id=seq(start_id))
        person = seq_lonely_person.make()
        assert person.only_friend_id == start_id + 1
        user = seq_lonely_person.make()
        assert user.only_friend_id == start_id + 2

    @pytest.mark.django_db
    def test_increment_for_strings_with_bad_suffix(self):
        bob_person = person_recipe.extend(email=seq("bob", suffix=42))
        with pytest.raises(TypeError) as exc:
            bob_person.make()
            assert str(exc.value) == "Sequences suffix can only be a string"

    @pytest.mark.django_db
    def test_increment_for_strings_with_suffix_and_start(self):
        fred_person = person_recipe.extend(
            email=seq("fred", start=5, suffix="@example.com")
        )
        person = fred_person.make()
        assert person.email == "fred5@example.com"
        person = fred_person.make()
        assert person.email == "fred6@example.com"
        person = fred_person.make()
        assert person.email == "fred7@example.com"

    @pytest.mark.django_db
    def test_increment_for_numbers(self):
        dummy = baker.make_recipe("tests.generic.serial_numbers")
        assert dummy.default_int_field == 11
        assert dummy.default_decimal_field == Decimal("21.1")
        assert dummy.default_float_field == 2.23
        dummy = baker.make_recipe("tests.generic.serial_numbers")
        assert dummy.default_int_field == 12
        assert dummy.default_decimal_field == Decimal("22.1")
        assert dummy.default_float_field == 3.23
        dummy = baker.prepare_recipe("tests.generic.serial_numbers")
        assert dummy.default_int_field == 13
        assert dummy.default_decimal_field == Decimal("23.1")
        assert dummy.default_float_field == 4.23

    @pytest.mark.django_db
    def test_increment_for_numbers_2(self):
        """Repeated test to ensure Sequences atomicity."""
        dummy = baker.make_recipe("tests.generic.serial_numbers")
        assert dummy.default_int_field == 11
        assert dummy.default_decimal_field == Decimal("21.1")
        assert dummy.default_float_field == 2.23
        dummy = baker.make_recipe("tests.generic.serial_numbers")
        assert dummy.default_int_field == 12
        assert dummy.default_decimal_field == Decimal("22.1")
        assert dummy.default_float_field == 3.23
        dummy = baker.prepare_recipe("tests.generic.serial_numbers")
        assert dummy.default_int_field == 13
        assert dummy.default_decimal_field == Decimal("23.1")
        assert dummy.default_float_field == 4.23

    @pytest.mark.django_db
    def test_increment_for_numbers_with_suffix(self):
        with pytest.raises(TypeError) as exc:
            baker.make_recipe(
                "tests.generic.serial_numbers",
                default_int_field=seq(1, suffix="will not work"),
            )
            assert (
                str(exc.value)
                == "Sequences with suffix can only be used with text values"
            )

    @pytest.mark.django_db
    def test_creates_unique_field_recipe_using_for_iterator(self):
        for i in range(1, 4):
            dummy = baker.make_recipe("tests.generic.dummy_unique_field")
            assert dummy.value == 10 + i

    @pytest.mark.django_db
    def test_creates_unique_field_recipe_using_quantity_argument(self):
        dummies = baker.make_recipe("tests.generic.dummy_unique_field", _quantity=3)
        assert dummies[0].value == 11
        assert dummies[1].value == 12
        assert dummies[2].value == 13

    @pytest.mark.django_db
    def test_increment_by_3(self):
        dummy = baker.make_recipe("tests.generic.serial_numbers_by")
        assert dummy.default_int_field == 13
        assert dummy.default_decimal_field == Decimal("22.5")
        assert dummy.default_float_field == pytest.approx(3.030000)
        dummy = baker.make_recipe("tests.generic.serial_numbers_by")
        assert dummy.default_int_field == 16
        assert dummy.default_decimal_field == Decimal("24.9")
        assert dummy.default_float_field == pytest.approx(4.83)
        dummy = baker.prepare_recipe("tests.generic.serial_numbers_by")
        assert dummy.default_int_field == 19
        assert dummy.default_decimal_field == Decimal("27.3")
        assert dummy.default_float_field == pytest.approx(6.63)

    @pytest.mark.django_db
    def test_increment_by_timedelta(self):
        dummy = baker.make_recipe("tests.generic.serial_datetime")
        assert dummy.default_date_field == (TEST_TIME.date() + timedelta(days=1))
        assert dummy.default_date_time_field == tz_aware(TEST_TIME + timedelta(hours=3))
        assert dummy.default_time_field == (TEST_TIME + timedelta(seconds=15)).time()
        dummy = baker.make_recipe("tests.generic.serial_datetime")
        assert dummy.default_date_field == (TEST_TIME.date() + timedelta(days=2))
        assert dummy.default_date_time_field == tz_aware(TEST_TIME + timedelta(hours=6))
        assert dummy.default_time_field == (TEST_TIME + timedelta(seconds=30)).time()

    @pytest.mark.django_db
    def test_increment_by_timedelta_seq_combined_with_quantity(self):
        quantity = 5
        entries = baker.make_recipe("tests.generic.serial_datetime", _quantity=quantity)
        for i, e in enumerate(entries):
            index = i + 1
            assert e.default_date_field == (
                TEST_TIME.date() + timedelta(days=1 * index)
            )
            assert e.default_date_time_field == tz_aware(
                TEST_TIME + timedelta(hours=3 * index)
            )
            assert (
                e.default_time_field
                == (TEST_TIME + timedelta(seconds=15 * index)).time()
            )

    @pytest.mark.django_db
    def test_creates_unique_timedelta_recipe_using_quantity_argument(self):
        dummies = baker.make_recipe("tests.generic.serial_datetime", _quantity=3)
        assert dummies[0].default_date_field == TEST_TIME.date() + timedelta(days=1)
        assert dummies[1].default_date_field == TEST_TIME.date() + timedelta(days=2)
        assert dummies[2].default_date_field == TEST_TIME.date() + timedelta(days=3)

    @pytest.mark.django_db
    def test_increment_after_override_definition_field(self):
        person = baker.make_recipe("tests.generic.serial_person", name="tom")
        assert person.name == "tom"
        person = baker.make_recipe("tests.generic.serial_person")
        assert person.name == "joe4"
        person = baker.prepare_recipe("tests.generic.serial_person")
        assert person.name == "joe5"


class TestIterators:
    @pytest.mark.django_db
    def test_accepts_generators(self):
        r = Recipe(DummyBlankFieldsModel, blank_char_field=itertools.cycle(["a", "b"]))
        assert r.make().blank_char_field == "a"
        assert r.make().blank_char_field == "b"
        assert r.make().blank_char_field == "a"

    @pytest.mark.django_db
    def test_accepts_iterators(self):
        r = Recipe(DummyBlankFieldsModel, blank_char_field=iter(["a", "b", "c"]))
        assert r.make().blank_char_field == "a"
        assert r.make().blank_char_field == "b"
        assert r.make().blank_char_field == "c"

    @pytest.mark.django_db
    def test_empty_iterator_exception(self):
        r = Recipe(DummyBlankFieldsModel, blank_char_field=iter(["a", "b"]))
        assert r.make().blank_char_field == "a"
        assert r.make().blank_char_field == "b"
        with pytest.raises(RecipeIteratorEmpty):
            r.make()

    @pytest.mark.django_db
    def test_only_iterators_not_iteratables_are_iterated(self):
        """Ensure we only iterate explicit iterators.

        Consider "iterable" vs "iterator":

        Something like a string is "iterable", but not an "iterator". We don't
        want to iterate "iterables", only explicit "iterators".

        """
        r = Recipe(
            DummyBlankFieldsModel, blank_text_field="not an iterator, so don't iterate!"
        )
        assert r.make().blank_text_field == "not an iterator, so don't iterate!"


class TestAutoNowFields:
    @pytest.mark.django_db
    def test_make_with_auto_now_using_datetime_generator(self):
        delta = timedelta(minutes=1)

        def gen():
            idx = 0
            while True:
                idx += 1
                yield tz_aware(TEST_TIME) + idx * delta

        r = Recipe(
            ModelWithAutoNowFields,
            created=gen(),
        )

        assert r.make().created == tz_aware(TEST_TIME + 1 * delta)
        assert r.make().created == tz_aware(TEST_TIME + 2 * delta)

    @pytest.mark.django_db
    def test_make_with_auto_now_using_datetime_seq(self):
        delta = timedelta(minutes=1)
        r = Recipe(
            ModelWithAutoNowFields,
            created=seq(
                tz_aware(TEST_TIME),
                increment_by=delta,
            ),
        )

        assert r.make().created == tz_aware(TEST_TIME + 1 * delta)
        assert r.make().created == tz_aware(TEST_TIME + 2 * delta)
