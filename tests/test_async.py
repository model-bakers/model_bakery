"""Tests for `amake` / `aprepare` — the async variants of `make` / `prepare`.

These exercise the async code paths in `baker.py`. The motivating use case
(single-connection rollback under `django-async-backend`) isn't exercised
here because that backend is a separate dependency. What this file *does*
verify is that the async path exists, recurses correctly through forward
FKs, honours the same kwargs as sync `make`, and rejects unsupported
features with a clear error.

We use `pytest.mark.django_db(transaction=True)` rather than the default
because under the stock Django backend `instance.asave()` is internally a
`sync_to_async(thread_sensitive=True)` wrapper — saves run on asgiref's
shared sync thread, which has its own DB connection. The default
atomic-wrap test transaction lives on pytest's test thread and would not
see (or roll back) those writes, leaking rows into later tests. With
`transaction=True` pytest-django truncates tables between tests, which
covers any connection.
"""

import pytest

from model_bakery import baker
from model_bakery.exceptions import InvalidQuantityException
from tests.generic.models import (
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
class TestAmakeUnsupportedFeatures:
    async def test_make_m2m_not_supported(self):
        with pytest.raises(NotImplementedError, match="make_m2m"):
            await baker.amake(Home, make_m2m=True)

    async def test_save_kwargs_not_supported(self):
        with pytest.raises(NotImplementedError, match="_save_kwargs"):
            await baker.amake(Profile, _save_kwargs={"using": "default"})

    async def test_refresh_after_create_not_supported(self):
        with pytest.raises(NotImplementedError, match="_refresh_after_create"):
            await baker.amake(Profile, _refresh_after_create=True)

    async def test_create_files_not_supported(self):
        with pytest.raises(NotImplementedError, match="_create_files"):
            await baker.amake(Profile, _create_files=True)

    async def test_bulk_create_not_supported(self):
        with pytest.raises(NotImplementedError, match="_bulk_create"):
            await baker.amake(Profile, _bulk_create=True)

    async def test_m2m_field_attr_raises(self):
        # `Home.dogs` is M2M; passing it should fail clearly even though the
        # generic kwarg sniffing wouldn't catch it.
        dog = await baker.amake(Dog)
        with pytest.raises(NotImplementedError, match="ManyToManyField"):
            await baker.amake(Home, dogs=[dog])

    async def test_auto_now_override_raises(self):
        # Dog has `created = DateTimeField(auto_now_add=True)`.
        from datetime import datetime, timezone

        dt = datetime(2020, 1, 1, tzinfo=timezone.utc)
        with pytest.raises(NotImplementedError, match="auto_now"):
            await baker.amake(Dog, created=dt)


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
