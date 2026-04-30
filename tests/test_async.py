"""Tests for `amake` / `aprepare` — the async variants of `make` / `prepare`.

We use `pytest.mark.django_db(transaction=True)` rather than the default
because under the stock Django backend `instance.asave()` is internally a
`sync_to_async(thread_sensitive=True)` wrapper — saves run on asgiref's
shared sync thread, which has its own DB connection. The default
atomic-wrap test transaction lives on pytest's test thread and would not
see (or roll back) those writes, leaking rows into later tests. With
`transaction=True` pytest-django truncates tables between tests, which
covers any connection.
"""

from datetime import datetime

import pytest

from model_bakery import baker
from model_bakery.exceptions import InvalidQuantityException
from tests.generic.models import (
    Classroom,
    Dog,
    Home,
    LonelyPerson,
    PaymentBill,
    Person,
    Profile,
    User,
)


@pytest.mark.django_db(transaction=True)
class TestAmakeBasics:
    async def test_amake_persists_simple_model(self):
        profile = await baker.amake(Profile)
        assert profile.pk is not None
        assert profile.email

    async def test_amake_persists_model_by_string(self):
        profile = await baker.amake("generic.Profile")
        assert profile.pk is not None

    async def test_amake_with_field_overrides(self):
        profile = await baker.amake(Profile, email="me@example.com")
        assert profile.email == "me@example.com"
        assert profile.pk is not None

    async def test_amake_creates_forward_fk(self):
        user = await baker.amake(User)
        assert user.pk is not None
        # `profile` is nullable so without explicit override it may be None.
        # When it is set, the related row must also have been persisted.
        if user.profile is not None:
            assert user.profile.pk is not None

    async def test_amake_with_fk_instance_override(self):
        profile = await baker.amake(Profile)
        user = await baker.amake(User, profile=profile)
        assert user.profile_id == profile.pk

    async def test_amake_fill_optional_creates_fk(self):
        user = await baker.amake(User, _fill_optional=["profile"])
        assert user.profile is not None
        assert user.profile.pk is not None

    async def test_amake_fill_optional_true_creates_fk(self):
        user = await baker.amake(User, _fill_optional=True)
        assert user.profile is not None
        assert user.profile.pk is not None


@pytest.mark.django_db(transaction=True)
class TestAmakeRelations:
    async def test_amake_double_underscore_forward_fk_traversal(self):
        bill = await baker.amake(
            PaymentBill, _fill_optional=["user"], user__username="alice"
        )
        assert bill.user.username == "alice"
        assert bill.user.pk is not None
        assert bill.pk is not None

    async def test_amake_one_to_one_forward(self):
        lonely = await baker.amake(LonelyPerson)
        assert lonely.pk is not None
        assert lonely.only_friend_id is not None
        assert lonely.only_friend.pk == lonely.only_friend_id

    async def test_amake_reverse_relation_creates_child(self):
        # `Profile` has a reverse FK from `User.profile` with default
        # accessor `user_set`. Baker treats `user_set` as a reverse-rel
        # name and creates a User attached to this Profile.
        profile = await baker.amake(Profile, user_set__username="bob")
        users = [u async for u in User.objects.filter(profile=profile)]
        assert len(users) == 1
        assert users[0].username == "bob"


@pytest.mark.django_db(transaction=True)
class TestAmakeQuantity:
    async def test_amake_with_quantity_returns_list(self):
        profiles = await baker.amake(Profile, _quantity=3)
        assert isinstance(profiles, list)
        assert len(profiles) == 3
        assert all(p.pk is not None for p in profiles)
        assert len({p.pk for p in profiles}) == 3

    async def test_amake_invalid_quantity_raises(self):
        with pytest.raises(InvalidQuantityException):
            await baker.amake(Profile, _quantity=0)


@pytest.mark.django_db(transaction=True)
class TestAprepare:
    async def test_aprepare_does_not_persist(self):
        profile = await baker.aprepare(Profile)
        assert profile.pk is None
        assert profile.email

    async def test_aprepare_save_related_unsupported(self):
        with pytest.raises(NotImplementedError, match="_save_related"):
            await baker.aprepare(User, _save_related=True)

    async def test_aprepare_quantity(self):
        profiles = await baker.aprepare(Profile, _quantity=2)
        assert len(profiles) == 2
        assert all(p.pk is None for p in profiles)


@pytest.mark.django_db(transaction=True)
class TestAmakeM2M:
    async def test_m2m_explicit_attr(self):
        dog1 = await baker.amake(Dog)
        dog2 = await baker.amake(Dog)
        home = await baker.amake(Home, dogs=[dog1, dog2])
        assert home.pk is not None
        related = [d async for d in home.dogs.all()]
        assert {d.pk for d in related} == {dog1.pk, dog2.pk}

    async def test_make_m2m_auto_generates_required_field(self):
        # `Home.dogs` is non-nullable M2M to Dog — `make_m2m=True` fills it.
        home = await baker.amake(Home, make_m2m=True)
        assert home.pk is not None
        assert await home.dogs.acount() > 0

    async def test_make_m2m_default_skips_nullable(self):
        # Nullable M2M (Classroom.students) is not auto-filled even with
        # `make_m2m=True` — matches sync behaviour. Override with
        # `_fill_optional` if you want it.
        classroom = await baker.amake(Classroom, make_m2m=True)
        assert await classroom.students.acount() == 0


@pytest.mark.django_db(transaction=True)
class TestAmakeKwargs:
    async def test_refresh_after_create(self):
        # Smoke-test: creating with refresh re-reads from DB.
        profile = await baker.amake(
            Profile, email="x@y.z", _refresh_after_create=True
        )
        assert profile.pk is not None
        assert profile.email == "x@y.z"

    async def test_save_kwargs_forwarded(self):
        # `using` is the only widely-applicable save kwarg without extra setup.
        profile = await baker.amake(Profile, _save_kwargs={"using": "default"})
        assert profile.pk is not None

    async def test_create_files_kwarg_accepted(self):
        # Smoke-test only: with `_create_files=False` the FileField is
        # skipped, but the kwarg is no longer rejected by the async path.
        # Actual file generation is the same code path as sync — covered
        # by `tests/test_filling_fields.py::TestsFillingFileField`.
        profile = await baker.amake(Profile, _create_files=False)
        assert profile.pk is not None

    async def test_auto_now_override(self):
        # Dog has `created = DateTimeField(auto_now_add=True)`. The conftest
        # leaves USE_TZ at its env default, which is False in this suite —
        # use a naive datetime to match the SQLite backend's expectations.
        dt = datetime(2020, 1, 1)
        dog = await baker.amake(Dog, created=dt)
        assert dog.pk is not None
        assert dog.created == dt
        # ...and the override survived a re-fetch.
        await dog.arefresh_from_db()
        assert dog.created == dt


@pytest.mark.django_db(transaction=True)
class TestAmakeBulkCreate:
    async def test_bulk_create_with_quantity(self):
        profiles = await baker.amake(Profile, _quantity=5, _bulk_create=True)
        assert isinstance(profiles, list)
        assert len(profiles) == 5
        assert all(p.pk is not None for p in profiles)
        assert await Profile.objects.acount() == 5

    async def test_bulk_create_persists_fk(self):
        # Bulk-creating User auto-creates a nullable Profile per row via the
        # `_save_related_objs` helper.
        users = await baker.amake(
            User, _quantity=3, _bulk_create=True, _fill_optional=["profile"]
        )
        assert len(users) == 3
        assert await Profile.objects.acount() == 3
        assert all(u.profile_id is not None for u in users)

    async def test_bulk_create_with_m2m_attrs(self):
        dog1 = await baker.amake(Dog)
        dog2 = await baker.amake(Dog)
        homes = await baker.amake(
            Home, _quantity=2, _bulk_create=True, dogs=[dog1, dog2]
        )
        assert len(homes) == 2
        for home in homes:
            related = {d.pk async for d in home.dogs.all()}
            assert related == {dog1.pk, dog2.pk}

    async def test_bulk_create_single_returns_instance(self):
        # Without `_quantity`, sync `make(..., _bulk_create=True)` returns
        # the single created instance, not a list. Async should match.
        profile = await baker.amake(Profile, _bulk_create=True)
        assert not isinstance(profile, list)
        assert profile.pk is not None


@pytest.mark.django_db(transaction=True)
class TestAmakeWithCustomGenerator:
    async def test_custom_generator_works(self):
        # `gen_same_text` is registered for CustomFieldViaSettings in conftest.
        from tests.generic.models import CustomFieldViaSettingsModel

        instance = await baker.amake(CustomFieldViaSettingsModel)
        assert instance.custom_value == "always the same text"
        assert instance.pk is not None


class TestAprepareNoDb:
    # No `django_db` mark: `aprepare` with default args does no I/O, so this
    # guards against accidentally introducing DB calls.
    async def test_aprepare_no_db_access(self):
        person = await baker.aprepare(Person)
        assert person.pk is None
        assert person.name
