from decimal import Decimal
from typing import Any, Callable, Dict, Optional, Type, Union

from django.db.backends.base.operations import BaseDatabaseOperations
from django.db.models import (
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
    ManyToManyField,
    OneToOneField,
    PositiveIntegerField,
    PositiveSmallIntegerField,
    SlugField,
    SmallIntegerField,
    TextField,
    TimeField,
    URLField,
    UUIDField,
)

from . import random_gen
from .utils import import_from_str

try:
    # Proper support starts with Django 3.0
    #  (as it uses `django/db/backends/base/operations.py` for matching ranges)
    from django.db.models import AutoField, BigAutoField, SmallAutoField
except ImportError:
    AutoField = None
    BigAutoField = None
    SmallAutoField = None

try:
    # added in Django 3.1
    from django.db.models import PositiveBigIntegerField
except ImportError:
    PositiveBigIntegerField = None

try:
    # Replaced `django.contrib.postgres.fields.JSONField` in Django 3.1
    from django.db.models import JSONField
except ImportError:
    JSONField = None

try:
    # PostgreSQL-specific field (only available when psycopg is installed)
    from django.contrib.postgres.fields import ArrayField
except ImportError:
    ArrayField = None

try:
    # Deprecated since Django 3.1, removed in Django 4.0
    # PostgreSQL-specific field (only available when psycopg is installed)
    from django.contrib.postgres.fields import JSONField as PostgresJSONField
except ImportError:
    PostgresJSONField = None

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
    # Deprecated since Django 3.1, removed in Django 4.0
    from django.db.models import NullBooleanField
except ImportError:
    NullBooleanField = None


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
    IntegerField: _make_integer_gen_by_range(IntegerField),
    BigIntegerField: _make_integer_gen_by_range(BigIntegerField),
    SmallIntegerField: _make_integer_gen_by_range(SmallIntegerField),
    PositiveIntegerField: _make_integer_gen_by_range(PositiveIntegerField),
    PositiveSmallIntegerField: _make_integer_gen_by_range(PositiveSmallIntegerField),
    FloatField: random_gen.gen_float,
    DecimalField: random_gen.gen_decimal,
    BinaryField: random_gen.gen_byte_string,
    CharField: random_gen.gen_string,
    TextField: random_gen.gen_text,
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
}  # type: Dict[Type, Callable]

if ArrayField:
    default_mapping[ArrayField] = random_gen.gen_array
if JSONField:
    default_mapping[JSONField] = random_gen.gen_json
if PostgresJSONField:
    default_mapping[PostgresJSONField] = random_gen.gen_json
if HStoreField:
    default_mapping[HStoreField] = random_gen.gen_hstore
if CICharField:
    default_mapping[CICharField] = random_gen.gen_string
if CIEmailField:
    default_mapping[CIEmailField] = random_gen.gen_email
if CITextField:
    default_mapping[CITextField] = random_gen.gen_text
if AutoField:
    default_mapping[AutoField] = _make_integer_gen_by_range(AutoField)
if BigAutoField:
    default_mapping[BigAutoField] = _make_integer_gen_by_range(BigAutoField)
if SmallAutoField:
    default_mapping[SmallAutoField] = _make_integer_gen_by_range(SmallAutoField)
if PositiveBigIntegerField:
    default_mapping[PositiveBigIntegerField] = _make_integer_gen_by_range(
        PositiveBigIntegerField
    )
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
if NullBooleanField:
    default_mapping[NullBooleanField] = random_gen.gen_boolean


# Add GIS fields


def get_type_mapping() -> Dict[Type, Callable]:
    from django.contrib.contenttypes.models import ContentType

    from .gis import default_gis_mapping

    mapping = default_mapping.copy()
    mapping[ContentType] = random_gen.gen_content_type
    mapping.update(default_gis_mapping)

    return mapping.copy()


user_mapping = {}


def add(field: str, func: Optional[Union[Callable, str]]) -> None:
    user_mapping[import_from_str(field)] = import_from_str(func)


def get(field: Any) -> Optional[Callable]:
    return user_mapping.get(field)
