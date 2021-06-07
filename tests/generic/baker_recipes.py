# ATTENTION: Recipes defined for testing purposes only
from datetime import timedelta
from decimal import Decimal

from django.utils.timezone import now

from model_bakery.recipe import Recipe, foreign_key, related, seq
from tests.generic.models import (
    TEST_TIME,
    Dog,
    DummyDefaultFieldsModel,
    DummyUniqueIntegerFieldModel,
    LonelyPerson,
    Person,
    School,
)

person = Recipe(
    Person,
    name="John Doe",
    nickname="joe",
    age=18,
    bio="Someone in the crowd",
    blog="http://joe.blogspot.com",
    days_since_last_login=4,
    birthday=now().date(),
    appointment=now(),
    birth_time=now(),
)

lonely_person = Recipe(LonelyPerson, only_friend=foreign_key(person, one_to_one=True))

serial_person = Recipe(
    Person,
    name=seq("joe"),
)

serial_numbers = Recipe(
    DummyDefaultFieldsModel,
    default_decimal_field=seq(Decimal("20.1")),
    default_int_field=seq(10),
    default_float_field=seq(1.23),
)

serial_numbers_by = Recipe(
    DummyDefaultFieldsModel,
    default_decimal_field=seq(Decimal("20.1"), increment_by=Decimal("2.4")),
    default_int_field=seq(10, increment_by=3),
    default_float_field=seq(1.23, increment_by=1.8),
)

serial_datetime = Recipe(
    DummyDefaultFieldsModel,
    default_date_field=seq(TEST_TIME.date(), timedelta(days=1)),
    default_date_time_field=seq(TEST_TIME, timedelta(hours=3)),
    default_time_field=seq(TEST_TIME.time(), timedelta(seconds=15), start="xpto"),
)

dog = Recipe(Dog, breed="Pug", owner=foreign_key(person))

homeless_dog = Recipe(
    Dog,
    breed="Pug",
)

other_dog = Recipe(Dog, breed="Basset", owner=foreign_key("person"))

dog_with_friends = dog.extend(
    friends_with=related(dog, dog),
)

dog_with_more_friends = dog.extend(
    friends_with=related(dog_with_friends),
)

extended_dog = dog.extend(
    breed="Super basset",
)

paulo_freire_school = Recipe(School, name="Escola Municipal Paulo Freire")


class SmallDogRecipe(Recipe):
    pass


small_dog = SmallDogRecipe(Dog)


pug = small_dog.extend(
    breed="Pug",
)

other_dog_unicode = Recipe(Dog, breed="Basset", owner=foreign_key("person"))

dummy_unique_field = Recipe(
    DummyUniqueIntegerFieldModel,
    value=seq(10),
)

dog_lady = Recipe(Person, dog_set=related("dog", other_dog))

nullable_related = Recipe(
    "generic.DummyBlankFieldsModel",
    dummynullfieldsmodel_set=related(Recipe("generic.DummyNullFieldsModel")),
)

cast_member = Recipe("generic.CastMember", person=foreign_key(person))

movie_with_cast = Recipe(
    "generic.Movie", cast_members=related(cast_member, cast_member)
)

overrided_save = Recipe("generic.ModelWithOverridedSave")

ip_fields = Recipe(
    "generic.DummyGenericIPAddressFieldModel",
    ipv4_field=seq("127.0.0.", increment_by=2),
    ipv6_field=seq("2001:12f8:0:28::", start=4, increment_by=2),
)
