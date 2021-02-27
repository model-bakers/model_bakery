import datetime
from decimal import Decimal
from inspect import getmodule

import pytest
from django.utils.timezone import utc

from model_bakery.utils import get_calling_module, import_from_str, seq
from tests.generic.models import User


def test_import_from_str():
    with pytest.raises(AttributeError):
        import_from_str("tests.generic.UndefinedObject")

    with pytest.raises(ImportError):
        import_from_str("tests.generic.undefined_path.User")

    assert import_from_str("tests.generic.models.User") == User
    assert import_from_str(User) == User
    assert import_from_str("generic.User") == User


def test_get_calling_module():
    # Reference to this very module
    this_module = getmodule(test_get_calling_module)

    # Once removed is the `pytest` module calling this function
    pytest_module = get_calling_module(1)
    assert pytest_module != this_module
    assert "pytest" in pytest_module.__name__

    # Test functions
    def dummy_secondary_method():
        return get_calling_module(2), get_calling_module(3)

    def dummy_method():
        return (*dummy_secondary_method(), get_calling_module(1), get_calling_module(2))

    # Unpack results from the function chain
    sec_mod, sec_pytest_mod, dummy_mod, pytest_mod = dummy_method()

    assert sec_mod == this_module
    assert "pytest" in sec_pytest_mod.__name__
    assert dummy_mod == this_module
    assert "pytest" in pytest_mod.__name__

    # Raise an `IndexError` when attempting to access too many frames removed
    with pytest.raises(IndexError):
        assert get_calling_module(100)


class TestSeq:
    def test_string(self):
        sequence = seq("muffin")
        assert next(sequence) == "muffin1"
        assert next(sequence) == "muffin2"
        assert next(sequence) == "muffin3"

    def test_string_start(self):
        sequence = seq("muffin", start=9)
        assert next(sequence) == "muffin9"
        assert next(sequence) == "muffin10"
        assert next(sequence) == "muffin11"

    def test_string_suffix(self):
        sequence = seq("cookie", suffix="@example.com")
        assert next(sequence) == "cookie1@example.com"
        assert next(sequence) == "cookie2@example.com"
        assert next(sequence) == "cookie3@example.com"

    def test_string_suffix_and_start(self):
        sequence = seq("cookie", start=111, suffix="@example.com")
        assert next(sequence) == "cookie111@example.com"
        assert next(sequence) == "cookie112@example.com"
        assert next(sequence) == "cookie113@example.com"

    def test_string_invalid_suffix(self):
        sequence = seq("cookie", suffix=42)

        with pytest.raises(TypeError) as exc:
            next(sequence)
            assert str(exc.value) == "Sequences suffix can only be a string"

    def test_int(self):
        sequence = seq(1)
        assert next(sequence) == 2
        assert next(sequence) == 3
        assert next(sequence) == 4

    def test_int_increment_by(self):
        sequence = seq(1, increment_by=3)
        assert next(sequence) == 4
        assert next(sequence) == 7
        assert next(sequence) == 10

    def test_decimal(self):
        sequence = seq(Decimal("36.6"))
        assert next(sequence) == Decimal("37.6")
        assert next(sequence) == Decimal("38.6")
        assert next(sequence) == Decimal("39.6")

    def test_decimal_increment_by(self):
        sequence = seq(Decimal("36.6"), increment_by=Decimal("2.4"))
        assert next(sequence) == Decimal("39.0")
        assert next(sequence) == Decimal("41.4")
        assert next(sequence) == Decimal("43.8")

    def test_float(self):
        sequence = seq(1.23)
        assert next(sequence) == 2.23
        assert next(sequence) == 3.23
        assert next(sequence) == 4.23

    def test_float_increment_by(self):
        sequence = seq(1.23, increment_by=1.8)
        assert next(sequence) == pytest.approx(3.03)
        assert next(sequence) == pytest.approx(4.83)
        assert next(sequence) == pytest.approx(6.63)

    def test_numbers_with_suffix(self):
        sequence = seq(1, suffix="iamnotanumber")
        with pytest.raises(TypeError) as exc:
            next(sequence)
            assert (
                str(exc.value)
                == "Sequences with suffix can only be used with text values"
            )

    def test_date(self):
        sequence = seq(
            datetime.date(2021, 2, 11), increment_by=datetime.timedelta(days=6)
        )
        assert next(sequence) == datetime.date(2021, 2, 17)
        assert next(sequence) == datetime.date(2021, 2, 23)
        assert next(sequence) == datetime.date(2021, 3, 1)

    def test_time(self):
        sequence = seq(
            datetime.time(15, 39, 58, 457698),
            increment_by=datetime.timedelta(minutes=59),
        )
        assert next(sequence) == datetime.time(16, 38, 58, 457698)
        assert next(sequence) == datetime.time(17, 37, 58, 457698)
        assert next(sequence) == datetime.time(18, 36, 58, 457698)

    @pytest.mark.parametrize("use_tz", [False, True])
    def test_datetime(self, settings, use_tz):
        settings.USE_TZ = use_tz
        tzinfo = utc if use_tz else None

        sequence = seq(
            datetime.datetime(2021, 2, 11, 15, 39, 58, 457698),
            increment_by=datetime.timedelta(hours=3),
        )
        assert next(sequence) == datetime.datetime(
            2021, 2, 11, 18, 39, 58, 457698
        ).replace(tzinfo=tzinfo)
        assert next(sequence) == datetime.datetime(
            2021, 2, 11, 21, 39, 58, 457698
        ).replace(tzinfo=tzinfo)
        assert next(sequence) == datetime.datetime(
            2021, 2, 12, 00, 39, 58, 457698
        ).replace(tzinfo=tzinfo)
