from collections.abc import Callable
from decimal import Decimal
from typing import Any

from django.db.backends.base.operations import BaseDatabaseOperations
from django.db.models import (
    AutoField,
    BigAutoField,
    BigIntegerField,
    BinaryField,
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    DecimalField,
    DurationField,
    EmailField,
    FileField,
    FloatField,
    ForeignKey,
    GenericIPAddressField,
    ImageField,
    IntegerField,
    IPAddressField,
    JSONField,
    ManyToManyField,
    OneToOneField,
    PositiveBigIntegerField,
    PositiveIntegerField,
    PositiveSmallIntegerField,
    SlugField,
    SmallAutoField,
    SmallIntegerField,
    TextField,
    TimeField,
    URLField,
    UUIDField,
)

from . import random_gen
from .utils import import_from_str

try:
    # PostgreSQL-specific field (only available when psycopg is installed)
    from django.contrib.postgres.fields import ArrayField
except ImportError:
    ArrayField = None

try:
    # PostgreSQL-specific field (only available when psycopg is installed)
    from django.contrib.postgres.fields import HStoreField
except ImportError:
    HStoreField = None

try:
    # PostgreSQL-specific fields (only available when psycopg is installed)
    from django.contrib.postgres.fields.citext import (
        CICharField,
        CIEmailField,
        CITextField,
    )
except ImportError:
    CICharField = None
    CIEmailField = None
    CITextField = None


try:
    # PostgreSQL-specific fields (only available when psycopg is installed)
    from django.contrib.postgres.fields.ranges import (
        BigIntegerRangeField,
        DateRangeField,
        DateTimeRangeField,
        DecimalRangeField,
        IntegerRangeField,
    )
except ImportError:
    BigIntegerRangeField = None
    DateRangeField = None
    DateTimeRangeField = None
    DecimalRangeField = None
    IntegerRangeField = None


def _make_integer_gen_by_range(field_type: Any) -> Callable:
    min_int, max_int = BaseDatabaseOperations.integer_field_ranges[field_type.__name__]

    def gen_integer():
        return random_gen.gen_integer(min_int=min_int, max_int=max_int)

    return gen_integer


default_mapping = {
    ForeignKey: random_gen.gen_related,
    OneToOneField: random_gen.gen_related,
    ManyToManyField: random_gen.gen_m2m,
    BooleanField: random_gen.gen_boolean,
    AutoField: _make_integer_gen_by_range(AutoField),
    BigAutoField: _make_integer_gen_by_range(BigAutoField),
    IntegerField: _make_integer_gen_by_range(IntegerField),
    SmallAutoField: _make_integer_gen_by_range(SmallAutoField),
    BigIntegerField: _make_integer_gen_by_range(BigIntegerField),
    SmallIntegerField: _make_integer_gen_by_range(SmallIntegerField),
    PositiveBigIntegerField: _make_integer_gen_by_range(PositiveBigIntegerField),
    PositiveIntegerField: _make_integer_gen_by_range(PositiveIntegerField),
    PositiveSmallIntegerField: _make_integer_gen_by_range(PositiveSmallIntegerField),
    FloatField: random_gen.gen_float,
    DecimalField: random_gen.gen_decimal,
    BinaryField: random_gen.gen_byte_string,
    CharField: random_gen.gen_string,
    TextField: random_gen.gen_string,
    SlugField: random_gen.gen_slug,
    UUIDField: random_gen.gen_uuid,
    DateField: random_gen.gen_date,
    DateTimeField: random_gen.gen_datetime,
    TimeField: random_gen.gen_time,
    URLField: random_gen.gen_url,
    EmailField: random_gen.gen_email,
    IPAddressField: random_gen.gen_ipv4,
    GenericIPAddressField: random_gen.gen_ip,
    FileField: random_gen.gen_file_field,
    ImageField: random_gen.gen_image_field,
    DurationField: random_gen.gen_interval,
    JSONField: random_gen.gen_json,
}  # type: dict[type, Callable]

if ArrayField:
    default_mapping[ArrayField] = random_gen.gen_array
if HStoreField:
    default_mapping[HStoreField] = random_gen.gen_hstore
if CICharField:
    default_mapping[CICharField] = random_gen.gen_string
if CIEmailField:
    default_mapping[CIEmailField] = random_gen.gen_email
if CITextField:
    default_mapping[CITextField] = random_gen.gen_string
if DecimalRangeField:
    default_mapping[DecimalRangeField] = random_gen.gen_pg_numbers_range(Decimal)
if IntegerRangeField:
    default_mapping[IntegerRangeField] = random_gen.gen_pg_numbers_range(int)
if BigIntegerRangeField:
    default_mapping[BigIntegerRangeField] = random_gen.gen_pg_numbers_range(int)
if DateRangeField:
    default_mapping[DateRangeField] = random_gen.gen_date_range
if DateTimeRangeField:
    default_mapping[DateTimeRangeField] = random_gen.gen_datetime_range


# Add GIS fields


def get_type_mapping() -> dict[type, Callable]:
    from .content_types import default_contenttypes_mapping
    from .gis import default_gis_mapping

    mapping = default_mapping.copy()
    mapping.update(default_contenttypes_mapping)
    mapping.update(default_gis_mapping)
    return mapping.copy()


user_mapping = {}


def add(field: str, func: Callable | str | None) -> None:
    user_mapping[import_from_str(field)] = import_from_str(func)


def get(field: Any) -> Callable | None:
    return user_mapping.get(field)
