import uuid
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from os.path import abspath
from tempfile import gettempdir

import pytest
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.validators import (
    validate_ipv4_address,
    validate_ipv6_address,
    validate_ipv46_address,
)
from django.db import connection
from django.db.models import FileField, ImageField, fields

from model_bakery import baker
from model_bakery.gis import BAKER_GIS
from model_bakery.random_gen import gen_related
from tests.generic import generators, models

try:
    from django.db.models import JSONField
except ImportError:
    JSONField = None

try:
    from django.contrib.postgres.fields import (
        ArrayField,
        CICharField,
        CIEmailField,
        CITextField,
        HStoreField,
    )
    from django.contrib.postgres.fields import JSONField as PostgresJSONField
    from django.contrib.postgres.fields.ranges import (
        BigIntegerRangeField,
        DateRangeField,
        DateTimeRangeField,
        IntegerRangeField,
    )
except ImportError:
    ArrayField = None
    PostgresJSONField = None
    HStoreField = None
    CICharField = None
    CIEmailField = None
    CITextField = None
    IntegerRangeField = None
    BigIntegerRangeField = None
    DateRangeField = None
    DateTimeRangeField = None

try:
    from django.contrib.postgres.fields.ranges import FloatRangeField
except ImportError:
    FloatRangeField = None
try:
    from django.contrib.postgres.fields.ranges import DecimalRangeField
except ImportError:
    DecimalRangeField = None


@pytest.fixture
def person(db):
    return baker.make("generic.Person")


@pytest.fixture()
def custom_cfg():
    yield None
    if hasattr(settings, "BAKER_CUSTOM_FIELDS_GEN"):
        delattr(settings, "BAKER_CUSTOM_FIELDS_GEN")
    baker.generators.add("tests.generic.fields.CustomFieldWithGenerator", None)
    baker.generators.add("django.db.models.fields.CharField", None)


class TestFillingFromChoice:
    def test_if_gender_is_populated_from_choices(self, person):
        from tests.generic.models import GENDER_CHOICES

        assert person.gender in map(lambda x: x[0], GENDER_CHOICES)

    def test_if_occupation_populated_from_choices(self, person):
        from tests.generic.models import OCCUPATION_CHOICES

        occupations = [item[0] for lst in OCCUPATION_CHOICES for item in lst[1]]
        assert person.occupation in occupations


class TestStringFieldsFilling:
    def test_fill_CharField_with_a_random_str(self, person):
        person_name_field = models.Person._meta.get_field("name")
        assert isinstance(person_name_field, fields.CharField)

        assert isinstance(person.name, str)
        assert len(person.name) == person_name_field.max_length

    def test_fill_SlugField_with_a_random_str(self, person):
        person_nickname_field = models.Person._meta.get_field("nickname")
        assert isinstance(person_nickname_field, fields.SlugField)

        assert isinstance(person.nickname, str)
        assert len(person.nickname) == person_nickname_field.max_length

    def test_fill_TextField_with_a_random_str(self, person):
        person_bio_field = models.Person._meta.get_field("bio")
        assert isinstance(person_bio_field, fields.TextField)

        assert isinstance(person.bio, str)


class TestBinaryFieldsFilling:
    def test_fill_BinaryField_with_random_binary(self, person):
        name_hash_field = models.Person._meta.get_field("name_hash")
        assert isinstance(name_hash_field, fields.BinaryField)
        name_hash = person.name_hash
        assert isinstance(name_hash, bytes)
        assert len(name_hash) == name_hash_field.max_length


class TestsDurationFieldsFilling:
    def test_fill_DurationField_with_random_interval_in_miliseconds(self, person):
        duration_of_sleep_field = models.Person._meta.get_field("duration_of_sleep")
        assert isinstance(duration_of_sleep_field, fields.DurationField)
        duration_of_sleep = person.duration_of_sleep
        assert isinstance(duration_of_sleep, timedelta)


class TestBooleanFieldsFilling:
    def test_fill_BooleanField_with_boolean(self, person):
        enjoy_jards_macale_field = models.Person._meta.get_field("enjoy_jards_macale")
        assert isinstance(enjoy_jards_macale_field, fields.BooleanField)

        assert isinstance(person.enjoy_jards_macale, bool)
        assert person.enjoy_jards_macale is True

    def test_fill_BooleanField_with_false_if_default_is_false(self, person):
        like_metal_music_field = models.Person._meta.get_field("like_metal_music")
        assert isinstance(like_metal_music_field, fields.BooleanField)

        assert isinstance(person.like_metal_music, bool)
        assert person.like_metal_music is False


class TestDateFieldsFilling:
    def test_fill_DateField_with_a_date(self, person):
        birthday_field = models.Person._meta.get_field("birthday")
        assert isinstance(birthday_field, fields.DateField)
        assert isinstance(person.birthday, date)


class TestDateTimeFieldsFilling:
    def test_fill_DateTimeField_with_a_datetime(self, person):
        appointment_field = models.Person._meta.get_field("appointment")
        assert isinstance(appointment_field, fields.DateTimeField)
        assert isinstance(person.appointment, datetime)


class TestTimeFieldsFilling:
    def test_fill_TimeField_with_a_time(self, person):
        birth_time_field = models.Person._meta.get_field("birth_time")
        assert isinstance(birth_time_field, fields.TimeField)
        assert isinstance(person.birth_time, time)


class TestUUIDFieldsFilling:
    def test_fill_UUIDField_with_uuid_object(self, person):
        uuid_field = models.Person._meta.get_field("uuid")
        assert isinstance(uuid_field, fields.UUIDField)
        assert isinstance(person.uuid, uuid.UUID)


@pytest.mark.skipif(JSONField is None, reason="JSONField could not be imported")
class TestJSONFieldsFilling:
    def test_fill_JSONField_with_uuid_object(self, person):
        json_field = models.Person._meta.get_field("data")
        assert isinstance(json_field, JSONField)
        assert isinstance(person.data, dict)


@pytest.mark.django_db
class TestFillingIntFields:
    def test_fill_IntegerField_with_a_random_number(self):
        dummy_int_model = baker.make(models.DummyIntModel)
        int_field = models.DummyIntModel._meta.get_field("int_field")
        assert isinstance(int_field, fields.IntegerField)
        assert isinstance(dummy_int_model.int_field, int)

    def test_fill_BigIntegerField_with_a_random_number(self):
        dummy_int_model = baker.make(models.DummyIntModel)
        big_int_field = models.DummyIntModel._meta.get_field("big_int_field")
        assert isinstance(big_int_field, fields.BigIntegerField)
        assert isinstance(dummy_int_model.big_int_field, int)

    def test_fill_SmallIntegerField_with_a_random_number(self):
        dummy_int_model = baker.make(models.DummyIntModel)
        small_int_field = models.DummyIntModel._meta.get_field("small_int_field")
        assert isinstance(small_int_field, fields.SmallIntegerField)
        assert isinstance(dummy_int_model.small_int_field, int)


@pytest.mark.django_db
class TestFillingPositiveIntFields:
    def test_fill_PositiveSmallIntegerField_with_a_random_number(self):
        dummy_positive_int_model = baker.make(models.DummyPositiveIntModel)
        field = models.DummyPositiveIntModel._meta.get_field("positive_small_int_field")
        positive_small_int_field = field
        assert isinstance(positive_small_int_field, fields.PositiveSmallIntegerField)
        assert isinstance(dummy_positive_int_model.positive_small_int_field, int)
        assert dummy_positive_int_model.positive_small_int_field > 0

    def test_fill_PositiveIntegerField_with_a_random_number(self):
        dummy_positive_int_model = baker.make(models.DummyPositiveIntModel)
        positive_int_field = models.DummyPositiveIntModel._meta.get_field(
            "positive_int_field"
        )
        assert isinstance(positive_int_field, fields.PositiveIntegerField)
        assert isinstance(dummy_positive_int_model.positive_int_field, int)
        assert dummy_positive_int_model.positive_int_field > 0


@pytest.mark.django_db
class TestFillingOthersNumericFields:
    def test_filling_FloatField_with_a_random_float(self):
        self.dummy_numbers_model = baker.make(models.DummyNumbersModel)
        float_field = models.DummyNumbersModel._meta.get_field("float_field")
        assert isinstance(float_field, fields.FloatField)
        assert isinstance(self.dummy_numbers_model.float_field, float)

    def test_filling_DecimalField_with_random_decimal(self):
        self.dummy_decimal_model = baker.make(models.DummyDecimalModel)
        decimal_field = models.DummyDecimalModel._meta.get_field("decimal_field")
        assert isinstance(decimal_field, fields.DecimalField)
        assert isinstance(self.dummy_decimal_model.decimal_field, Decimal)


class TestURLFieldsFilling:
    def test_fill_URLField_with_valid_url(self, person):
        blog_field = models.Person._meta.get_field("blog")
        assert isinstance(blog_field, fields.URLField)
        assert isinstance(person.blog, str)


class TestFillingEmailField:
    def test_filling_EmailField(self, person):
        field = models.Person._meta.get_field("email")
        assert isinstance(field, fields.EmailField)
        assert isinstance(person.email, str)


@pytest.mark.django_db
class TestFillingIPAddressField:
    def test_filling_IPAddressField(self):
        obj = baker.make(models.DummyGenericIPAddressFieldModel)
        field = models.DummyGenericIPAddressFieldModel._meta.get_field("ipv4_field")
        assert isinstance(field, fields.GenericIPAddressField)
        assert isinstance(obj.ipv4_field, str)

        validate_ipv4_address(obj.ipv4_field)

        if hasattr(obj, "ipv6_field"):
            assert isinstance(obj.ipv6_field, str)
            assert isinstance(obj.ipv46_field, str)

            validate_ipv6_address(obj.ipv6_field)
            validate_ipv46_address(obj.ipv46_field)


@pytest.mark.django_db
class TestFillingGenericForeignKeyField:
    def test_filling_content_type_field(self):
        dummy = baker.make(models.DummyGenericForeignKeyModel)
        assert isinstance(dummy.content_type, ContentType)
        assert dummy.content_type.model_class() is not None


@pytest.mark.django_db
class TestFillingForeignKeyFieldWithDefaultFunctionReturningId:
    def test_filling_foreignkey_with_default_id(self):
        dummy = baker.make(models.RelatedNamesWithDefaultsModel)
        assert dummy.cake.__class__.objects.count() == 1
        assert dummy.cake.id == models.get_default_cake_id()
        assert dummy.cake.name == "Muffin"

    def test_filling_foreignkey_with_default_id_with_custom_arguments(self):
        dummy = baker.make(
            models.RelatedNamesWithDefaultsModel, cake__name="Baumkuchen"
        )
        assert dummy.cake.__class__.objects.count() == 1
        assert dummy.cake.id == dummy.cake.__class__.objects.get().id
        assert dummy.cake.name == "Baumkuchen"


@pytest.mark.django_db
class TestFillingOptionalForeignKeyField:
    def test_not_filling_optional_foreignkey(self):
        dummy = baker.make(models.RelatedNamesWithEmptyDefaultsModel)
        assert dummy.cake is None

    def test_filling_optional_foreignkey_implicitly(self):
        dummy = baker.make(
            models.RelatedNamesWithEmptyDefaultsModel, cake__name="Carrot cake"
        )
        assert dummy.cake.__class__.objects.count() == 1
        assert dummy.cake.name == "Carrot cake"


@pytest.mark.django_db
class TestsFillingFileField:
    def test_filling_file_field(self):
        dummy = baker.make(models.DummyFileFieldModel, _create_files=True)
        field = models.DummyFileFieldModel._meta.get_field("file_field")
        assert isinstance(field, FileField)
        import time

        path = "%s/%s/mock_file.txt" % (gettempdir(), time.strftime("%Y/%m/%d"))

        assert abspath(path) == abspath(dummy.file_field.path)
        dummy.file_field.delete()

    def test_does_not_create_file_if_not_flagged(self):
        dummy = baker.make(models.DummyFileFieldModel)
        with pytest.raises(ValueError):
            # Django raises ValueError if file does not exist
            assert dummy.file_field.path


@pytest.mark.django_db
class TestFillingCustomFields:
    def test_raises_unsupported_field_for_custom_field(self, custom_cfg):
        """Should raise an exception if a generator is not provided for a custom field."""
        with pytest.raises(TypeError):
            baker.make(models.CustomFieldWithoutGeneratorModel)

    def test_uses_generator_defined_on_settings_for_custom_field(self, custom_cfg):
        """Should use the function defined in settings as a generator."""
        generator_dict = {
            "tests.generic.fields.CustomFieldWithGenerator": generators.gen_value_string
        }
        setattr(settings, "BAKER_CUSTOM_FIELDS_GEN", generator_dict)
        obj = baker.make(models.CustomFieldWithGeneratorModel)
        assert "value" == obj.custom_value

    def test_uses_generator_defined_as_string_on_settings_for_custom_field(
        self, custom_cfg
    ):
        """Should import and use the function present in the import path defined in settings."""
        # fmt: off
        generator_dict = {
            "tests.generic.fields.CustomFieldWithGenerator":
            "tests.generic.generators.gen_value_string"
        }
        # fmt: on
        setattr(settings, "BAKER_CUSTOM_FIELDS_GEN", generator_dict)
        obj = baker.make(models.CustomFieldWithGeneratorModel)
        assert "value" == obj.custom_value

    def test_uses_generator_defined_on_settings_for_custom_foreignkey(self, custom_cfg):
        """Should use the function defined in the import path for a foreign key field."""
        generator_dict = {
            "tests.generic.fields.CustomForeignKey": "model_bakery.random_gen.gen_related"
        }
        setattr(settings, "BAKER_CUSTOM_FIELDS_GEN", generator_dict)
        obj = baker.make(
            models.CustomForeignKeyWithGeneratorModel, custom_fk__email="a@b.com"
        )
        assert "a@b.com" == obj.custom_fk.email

    def test_uses_generator_defined_as_string_for_custom_field(self, custom_cfg):
        """Should import and use the generator function used in the add method."""
        baker.generators.add(
            "tests.generic.fields.CustomFieldWithGenerator",
            "tests.generic.generators.gen_value_string",
        )
        obj = baker.make(models.CustomFieldWithGeneratorModel)
        assert "value" == obj.custom_value

    def test_uses_generator_function_for_custom_foreignkey(self, custom_cfg):
        """Should use the generator function passed as a value for the add method."""
        baker.generators.add("tests.generic.fields.CustomForeignKey", gen_related)
        obj = baker.make(
            models.CustomForeignKeyWithGeneratorModel, custom_fk__email="a@b.com"
        )
        assert "a@b.com" == obj.custom_fk.email

    def test_can_override_django_default_field_functions_generator(self, custom_cfg):
        def gen_char():
            return "Some value"

        baker.generators.add("django.db.models.fields.CharField", gen_char)

        person = baker.make(models.Person)

        assert "Some value" == person.name

    def test_ensure_adding_generators_via_settings_works(self):
        obj = baker.make(models.CustomFieldViaSettingsModel)
        assert "always the same text" == obj.custom_value


@pytest.mark.django_db
class TestFillingAutoFields:
    def test_filling_AutoField(self):
        obj = baker.make(models.DummyEmptyModel)
        field = models.DummyEmptyModel._meta.get_field("id")
        assert isinstance(field, fields.AutoField)
        assert isinstance(obj.id, int)


@pytest.mark.django_db
@pytest.mark.skipif(not models.has_pil, reason="PIL is required to test ImageField")
class TestFillingImageFileField:
    def test_filling_image_file_field(self):
        dummy = baker.make(models.DummyImageFieldModel, _create_files=True)
        field = models.DummyImageFieldModel._meta.get_field("image_field")
        assert isinstance(field, ImageField)
        import time

        path = "%s/%s/mock_img.jpeg" % (gettempdir(), time.strftime("%Y/%m/%d"))

        # These require the file to exist in earlier versions of Django
        assert abspath(path) == abspath(dummy.image_field.path)
        assert dummy.image_field.width
        assert dummy.image_field.height
        dummy.image_field.delete()

    def test_does_not_create_file_if_not_flagged(self):
        dummy = baker.make(models.DummyImageFieldModel)
        with pytest.raises(ValueError):
            # Django raises ValueError if image does not exist
            assert dummy.image_field.path


@pytest.mark.skipif(
    connection.vendor != "postgresql", reason="PostgreSQL specific tests"
)
class TestCIStringFieldsFilling:
    def test_fill_cicharfield_with_a_random_str(self, person):
        ci_char_field = models.Person._meta.get_field("ci_char")
        assert isinstance(ci_char_field, CICharField)
        assert isinstance(person.ci_char, str)
        assert len(person.ci_char) == ci_char_field.max_length

    def test_filling_ciemailfield(self, person):
        ci_email_field = models.Person._meta.get_field("ci_email")
        assert isinstance(ci_email_field, CIEmailField)
        assert isinstance(person.ci_email, str)

    def test_filling_citextfield(self, person):
        ci_text_field = models.Person._meta.get_field("ci_text")
        assert isinstance(ci_text_field, CITextField)
        assert isinstance(person.ci_text, str)

    def test_filling_decimal_range_field(self, person):
        from psycopg2._range import NumericRange

        decimal_range_field = models.Person._meta.get_field("decimal_range")
        assert isinstance(decimal_range_field, DecimalRangeField)
        assert isinstance(person.decimal_range, NumericRange)
        assert isinstance(person.decimal_range.lower, Decimal)
        assert isinstance(person.decimal_range.upper, Decimal)
        assert person.decimal_range.lower < person.decimal_range.upper

    def test_filling_integer_range_field(self, person):
        from psycopg2._range import NumericRange

        int_range_field = models.Person._meta.get_field("int_range")
        assert isinstance(int_range_field, IntegerRangeField)
        assert isinstance(person.int_range, NumericRange)
        assert isinstance(person.int_range.lower, int)
        assert isinstance(person.int_range.upper, int)
        assert person.int_range.lower < person.int_range.upper

    def test_filling_integer_range_field_for_big_int(self, person):
        from psycopg2._range import NumericRange

        bigint_range_field = models.Person._meta.get_field("bigint_range")
        assert isinstance(bigint_range_field, BigIntegerRangeField)
        assert isinstance(person.bigint_range, NumericRange)
        assert isinstance(person.bigint_range.lower, int)
        assert isinstance(person.bigint_range.upper, int)
        assert person.bigint_range.lower < person.bigint_range.upper

    @pytest.mark.skipif(
        FloatRangeField is None,
        reason="FloatRangeField is deprecated since Django 2.2",
    )
    def test_filling_float_range_field(self, person):
        from psycopg2._range import NumericRange

        float_range_field = models.Person._meta.get_field("float_range")
        assert isinstance(float_range_field, FloatRangeField)
        assert isinstance(person.float_range, NumericRange)
        assert isinstance(person.float_range.lower, float)
        assert isinstance(person.float_range.upper, float)
        assert person.float_range.lower < person.float_range.upper

    def test_filling_date_range_field(self, person):
        from psycopg2.extras import DateRange

        date_range_field = models.Person._meta.get_field("date_range")
        assert isinstance(date_range_field, DateRangeField)
        assert isinstance(person.date_range, DateRange)
        assert isinstance(person.date_range.lower, date)
        assert isinstance(person.date_range.upper, date)
        assert person.date_range.lower < person.date_range.upper

    def test_filling_datetime_range_field(self, person):
        from psycopg2.extras import DateTimeTZRange

        datetime_range_field = models.Person._meta.get_field("datetime_range")
        assert isinstance(datetime_range_field, DateTimeRangeField)
        assert isinstance(person.datetime_range, DateTimeTZRange)
        assert isinstance(person.datetime_range.lower, datetime)
        assert isinstance(person.datetime_range.upper, datetime)
        assert person.datetime_range.lower < person.datetime_range.upper


@pytest.mark.skipif(
    connection.vendor != "postgresql", reason="PostgreSQL specific tests"
)
class TestPostgreSQLFieldsFilling:
    def test_fill_arrayfield_with_empty_array(self, person):
        assert person.acquaintances == []

    def test_fill_jsonfield_with_empty_dict(self, person):
        assert person.postgres_data == {}

    def test_fill_hstorefield_with_empty_dict(self, person):
        assert person.hstore_data == {}


@pytest.mark.skipif(not BAKER_GIS, reason="GIS support required for GIS fields")
class TestGisFieldsFilling:
    def assertGeomValid(self, geom):
        assert geom.valid is True, geom.valid_reason

    def test_fill_PointField_valid(self, person):
        print(BAKER_GIS)
        self.assertGeomValid(person.point)

    def test_fill_LineStringField_valid(self, person):
        self.assertGeomValid(person.line_string)

    def test_fill_PolygonField_valid(self, person):
        self.assertGeomValid(person.polygon)

    def test_fill_MultiPointField_valid(self, person):
        self.assertGeomValid(person.multi_point)

    def test_fill_MultiLineStringField_valid(self, person):
        self.assertGeomValid(person.multi_line_string)

    def test_fill_MultiPolygonField_valid(self, person):
        self.assertGeomValid(person.multi_polygon)

    def test_fill_GeometryField_valid(self, person):
        self.assertGeomValid(person.geom)

    def test_fill_GeometryCollectionField_valid(self, person):
        self.assertGeomValid(person.geom_collection)
