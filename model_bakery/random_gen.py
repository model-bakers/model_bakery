"""Generators are callables that return a value used to populate a field.

If this callable has a `required` attribute (a list, mostly), for each
item in the list, if the item is a string, the field attribute with the
same name will be fetched from the field and used as argument for the
generator. If it is a callable (which will receive `field` as first
argument), it should return a list in the format (key, value) where key
is the argument name for generator and value is the value for that
argument.
"""

import string
import warnings
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from os.path import abspath, dirname, join
from random import choice, randint, random, uniform
from typing import Any, Callable, List, Optional, Tuple, Union
from uuid import UUID

from django.core.files.base import ContentFile
from django.db.models import Field, Model
from django.utils.timezone import now

MAX_LENGTH = 300
# Using sys.maxint here breaks a bunch of tests when running against a
# Postgres database.
MAX_INT = 100000000000


def get_content_file(content: bytes, name: str) -> ContentFile:
    return ContentFile(content, name=name)


def gen_file_field() -> ContentFile:
    name = "mock_file.txt"
    file_path = abspath(join(dirname(__file__), name))
    with open(file_path, "rb") as f:
        return get_content_file(f.read(), name=name)


def gen_image_field() -> ContentFile:
    name = "mock_img.jpeg"
    file_path = abspath(join(dirname(__file__), name))
    with open(file_path, "rb") as f:
        return get_content_file(f.read(), name=name)


def gen_from_list(a_list: Union[List[str], range]) -> Callable:
    """Make sure all values of the field are generated from a list.

    Examples:
        Here how to use it.

        >>> from baker import Baker
        >>> class ExperienceBaker(Baker):
        >>>     attr_mapping = {'some_field': gen_from_list(['A', 'B', 'C'])}

    """
    return lambda: choice(list(a_list))


# -- DEFAULT GENERATORS --


def gen_from_choices(choices: List) -> Callable:
    choice_list = []
    for value, label in choices:
        if isinstance(label, (list, tuple)):
            for val, lbl in label:
                choice_list.append(val)
        else:
            choice_list.append(value)
    return gen_from_list(choice_list)


def gen_integer(min_int: int = -MAX_INT, max_int: int = MAX_INT) -> int:
    return randint(min_int, max_int)


def gen_float() -> float:
    return random() * gen_integer()


def gen_decimal(max_digits: int, decimal_places: int) -> Decimal:
    def num_as_str(x: int) -> str:
        return "".join([str(randint(0, 9)) for _ in range(x)])

    if decimal_places:
        return Decimal(
            f"{num_as_str(max_digits - decimal_places - 1)}.{num_as_str(decimal_places)}"
        )

    return Decimal(num_as_str(max_digits))


gen_decimal.required = ["max_digits", "decimal_places"]  # type: ignore[attr-defined]


def gen_date() -> date:
    return now().date()


def gen_datetime() -> datetime:
    return now()


def gen_time() -> time:
    return now().time()


def gen_string(max_length: int) -> str:
    return str("".join(choice(string.ascii_letters) for _ in range(max_length)))


def _gen_string_get_max_length(field: Field) -> Tuple[str, int]:
    max_length = getattr(field, "max_length", None)
    if max_length is None:
        max_length = MAX_LENGTH
    return "max_length", max_length


gen_string.required = [_gen_string_get_max_length]  # type: ignore[attr-defined]


def gen_slug(max_length: int) -> str:
    valid_chars = string.ascii_letters + string.digits + "_-"
    return str("".join(choice(valid_chars) for _ in range(max_length)))


gen_slug.required = ["max_length"]  # type: ignore[attr-defined]


def gen_text() -> str:
    return gen_string(MAX_LENGTH)


def gen_boolean() -> bool:
    return choice((True, False))


def gen_null_boolean():
    return choice((True, False, None))


def gen_url() -> str:
    return f"http://www.{gen_string(30)}.com/"


def gen_email() -> str:
    return f"{gen_string(10)}@example.com"


def gen_ipv6() -> str:
    return ":".join(format(randint(1, 65535), "x") for _ in range(8))


def gen_ipv4() -> str:
    return ".".join(str(randint(1, 255)) for _ in range(4))


def gen_ipv46() -> str:
    ip_gen = choice([gen_ipv4, gen_ipv6])
    return ip_gen()


def gen_ip(protocol: str, default_validators: List[Callable]) -> str:
    from django.core.exceptions import ValidationError

    protocol = (protocol or "").lower()

    if not protocol:
        field_validator = default_validators[0]
        dummy_ipv4 = "1.1.1.1"
        dummy_ipv6 = "FE80::0202:B3FF:FE1E:8329"
        try:
            field_validator(dummy_ipv4)
            field_validator(dummy_ipv6)
            generator = gen_ipv46
        except ValidationError:
            try:
                field_validator(dummy_ipv4)
                generator = gen_ipv4
            except ValidationError:
                generator = gen_ipv6
    elif protocol == "ipv4":
        generator = gen_ipv4
    elif protocol == "ipv6":
        generator = gen_ipv6
    else:
        generator = gen_ipv46

    return generator()


gen_ip.required = ["protocol", "default_validators"]  # type: ignore[attr-defined]


def gen_byte_string(max_length: int = 16) -> bytes:
    generator = (randint(0, 255) for x in range(max_length))
    return bytes(generator)


def gen_interval(interval_key: str = "milliseconds", offset: int = 0) -> timedelta:
    interval = gen_integer() + offset
    kwargs = {interval_key: interval}
    return timedelta(**kwargs)


def gen_content_type():
    from django.apps import apps
    from django.contrib.contenttypes.models import ContentType

    try:
        return ContentType.objects.get_for_model(choice(apps.get_models()))
    except (AssertionError, RuntimeError):
        # AssertionError is raised by Django's test framework when db access is not available:
        # https://github.com/django/django/blob/stable/4.0.x/django/test/testcases.py#L150
        # RuntimeError is raised by pytest-django when db access is not available:
        # https://github.com/pytest-dev/pytest-django/blob/v4.5.2/pytest_django/plugin.py#L709
        warnings.warn("Database access disabled, returning ContentType raw instance")
        return ContentType()


def gen_uuid() -> UUID:
    import uuid

    return uuid.uuid4()


def gen_array():
    return []


def gen_json():
    return {}


def gen_hstore():
    return {}


def _fk_model(field: Field) -> Tuple[str, Optional[Model]]:
    try:
        return ("model", field.related_model)
    except AttributeError:
        return ("model", field.related.parent_model)


def _prepare_related(model: str, **attrs: Any) -> Union[Model, List[Model]]:
    from .baker import prepare

    return prepare(model, **attrs)


def gen_related(model, **attrs):
    from .baker import make

    return make(model, **attrs)


gen_related.required = [_fk_model, "_using"]  # type: ignore[attr-defined]
gen_related.prepare = _prepare_related  # type: ignore[attr-defined]


def gen_m2m(model, **attrs):
    from .baker import MAX_MANY_QUANTITY, make

    return make(model, _quantity=MAX_MANY_QUANTITY, **attrs)


gen_m2m.required = [_fk_model, "_using"]  # type: ignore[attr-defined]


# GIS generators


def gen_coord() -> float:
    return uniform(0, 1)


def gen_coords() -> str:
    return f"{gen_coord()} {gen_coord()}"


def gen_point() -> str:
    return f"POINT ({gen_coords()})"


def _gen_line_string_without_prefix() -> str:
    return f"({gen_coords()}, {gen_coords()})"


def gen_line_string() -> str:
    return f"LINESTRING {_gen_line_string_without_prefix()}"


def _gen_polygon_without_prefix() -> str:
    start = gen_coords()
    return f"(({start}, {gen_coords()}, {gen_coords()}, {start}))"


def gen_polygon() -> str:
    return f"POLYGON {_gen_polygon_without_prefix()}"


def gen_multi_point() -> str:
    return f"MULTIPOINT (({gen_coords()}))"


def gen_multi_line_string() -> str:
    return f"MULTILINESTRING ({_gen_line_string_without_prefix()})"


def gen_multi_polygon() -> str:
    return f"MULTIPOLYGON ({_gen_polygon_without_prefix()})"


def gen_geometry():
    return gen_point()


def gen_geometry_collection() -> str:
    return f"GEOMETRYCOLLECTION ({gen_point()})"


def gen_pg_numbers_range(number_cast: Callable[[int], Any]) -> Callable:
    def gen_range():
        try:
            from psycopg.types.range import Range
        except ImportError:
            from psycopg2._range import NumericRange as Range

        base_num = gen_integer(1, 100000)
        return Range(number_cast(-1 * base_num), number_cast(base_num))

    return gen_range


def gen_date_range():
    try:
        from psycopg.types.range import DateRange
    except ImportError:
        from psycopg2.extras import DateRange

    base_date = gen_date()
    interval = gen_interval(offset=24 * 60 * 60 * 1000)  # force at least 1 day interval
    args = sorted([base_date - interval, base_date + interval])
    return DateRange(*args)


def gen_datetime_range():
    try:
        from psycopg.types.range import TimestamptzRange
    except ImportError:
        from psycopg2.extras import DateTimeTZRange as TimestamptzRange

    base_datetime = gen_datetime()
    interval = gen_interval()
    args = sorted([base_datetime - interval, base_datetime + interval])
    return TimestamptzRange(*args)
