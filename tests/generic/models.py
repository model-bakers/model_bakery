########################################
# TESTING PURPOSE ONLY MODELS!!        #
# DO NOT ADD THE APP TO INSTALLED_APPS #
########################################
import datetime
from decimal import Decimal
from tempfile import gettempdir

import django
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.timezone import now

from model_bakery.baker import BAKER_CONTENTTYPES
from model_bakery.gis import BAKER_GIS
from model_bakery.timezone import tz_aware

from .fields import (
    CustomFieldViaSettings,
    CustomFieldWithGenerator,
    CustomFieldWithoutGenerator,
    CustomForeignKey,
    FakeListField,
)

# check whether PIL is installed
try:
    from PIL import ImageFile as PilImageFile  # NoQA
except ImportError:
    has_pil = False
else:
    has_pil = True

if BAKER_GIS:
    from django.contrib.gis.db import models
else:
    from django.db import models


# check if the contenttypes app is installed
if BAKER_CONTENTTYPES:
    from django.contrib.contenttypes import models as contenttypes
    from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
else:
    contenttypes = None
    GenericRelation = None
    GenericForeignKey = None

GENDER_CHOICES = [
    ("M", "male"),
    ("F", "female"),
    ("N", "non-binary"),
]

OCCUPATION_CHOICES = (
    ("Service Industry", (("waitress", "Waitress"), ("bartender", "Bartender"))),
    ("Education", (("teacher", "Teacher"), ("principal", "Principal"))),
)

TEST_TIME = datetime.datetime(2014, 7, 21, 15, 39, 58, 457698)


class ModelWithImpostorField(models.Model):
    pass


class Profile(models.Model):
    email = models.EmailField()


class User(models.Model):
    profile = models.ForeignKey(
        Profile, blank=True, null=True, on_delete=models.CASCADE
    )
    username = models.CharField(max_length=32)


class PaymentBill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    value = models.FloatField()


class Person(models.Model):
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    #  Jards Macalé is an amazing brazilian musician! =]
    enjoy_jards_macale = models.BooleanField(default=True)
    like_metal_music = models.BooleanField(default=False)
    name = models.CharField(max_length=30)
    nickname = models.SlugField(max_length=36)
    age = models.IntegerField()
    bio_summary = models.TextField(max_length=120)
    bio = models.TextField()
    birthday = models.DateField()
    birth_time = models.TimeField()
    appointment = models.DateTimeField()
    blog = models.URLField()
    occupation = models.CharField(max_length=10, choices=OCCUPATION_CHOICES)
    uuid = models.UUIDField(primary_key=False)
    name_hash = models.BinaryField(max_length=16)
    days_since_last_login = models.SmallIntegerField()
    days_since_account_creation = models.BigIntegerField()
    duration_of_sleep = models.DurationField()
    email = models.EmailField()
    id_document = models.CharField(unique=True, max_length=10)
    data = models.JSONField()
    if django.VERSION >= (5, 0):
        retirement_age = models.IntegerField(db_default=20)

    try:
        from django.contrib.postgres.fields import (
            ArrayField,
            HStoreField,
        )
        from django.contrib.postgres.fields.citext import (
            CICharField,
            CIEmailField,
            CITextField,
        )
        from django.contrib.postgres.fields.ranges import (
            BigIntegerRangeField,
            DateRangeField,
            DateTimeRangeField,
            DecimalRangeField,
            IntegerRangeField,
        )

        if settings.USING_POSTGRES:
            long_name = (
                models.CharField()
            )  # max_length is not required as PostgresSQL supports unlimited VARCHAR
            acquaintances = ArrayField(models.IntegerField())
            hstore_data = HStoreField()
            ci_char = CICharField(max_length=30)
            ci_email = CIEmailField()
            ci_text = CITextField()
            ci_text_max_length = CITextField(max_length=120)
            int_range = IntegerRangeField()
            bigint_range = BigIntegerRangeField()
            date_range = DateRangeField()
            datetime_range = DateTimeRangeField()
            decimal_range = DecimalRangeField()
    except ImportError:
        # Skip PostgreSQL-related fields
        pass

    if BAKER_GIS:
        geom = models.GeometryField()
        point = models.PointField()
        line_string = models.LineStringField()
        polygon = models.PolygonField()
        multi_point = models.MultiPointField()
        multi_line_string = models.MultiLineStringField()
        multi_polygon = models.MultiPolygonField()
        geom_collection = models.GeometryCollectionField()


class Dog(models.Model):
    class Meta:
        order_with_respect_to = "owner"

    owner = models.ForeignKey("Person", on_delete=models.CASCADE)
    breed = models.CharField(max_length=50)
    created = models.DateTimeField(auto_now_add=True)
    friends_with = models.ManyToManyField("Dog")


class GuardDog(Dog):
    pass


class Home(models.Model):
    address = models.CharField(max_length=200)
    owner = models.ForeignKey("Person", on_delete=models.CASCADE)
    dogs = models.ManyToManyField("Dog")


class LonelyPerson(models.Model):
    only_friend = models.OneToOneField(Person, on_delete=models.CASCADE)


class Cake(models.Model):
    name = models.CharField(max_length=64)


class RelatedNamesModel(models.Model):
    name = models.CharField(max_length=256)
    one_to_one = models.OneToOneField(
        Person, related_name="one_related", on_delete=models.CASCADE
    )
    foreign_key = models.ForeignKey(
        Person, related_name="fk_related", on_delete=models.CASCADE
    )


def get_default_cake_id():
    instance, _ = Cake.objects.get_or_create(name="Muffin")
    return instance.id


class RelatedNamesWithDefaultsModel(models.Model):
    name = models.CharField(max_length=256, default="Bravo")
    cake = models.ForeignKey(
        Cake,
        on_delete=models.CASCADE,
        default=get_default_cake_id,
    )


class RelatedNamesWithEmptyDefaultsModel(models.Model):
    name = models.CharField(max_length=256, default="Bravo")
    cake = models.ForeignKey(
        Cake,
        on_delete=models.CASCADE,
        null=True,
        default=None,
    )


class ModelWithOverwrittenSave(Dog):
    def save(self, *args, **kwargs):
        self.owner = kwargs.pop("owner")
        return super().save(*args, **kwargs)


class ModelWithSaveKwargs(Dog):
    def save(self, *args, **kwargs):
        self.breed = kwargs.pop("breed")
        return super().save(*args, **kwargs)


class Classroom(models.Model):
    students = models.ManyToManyField(Person, null=True)
    active = models.BooleanField(null=True)


class ClassroomM2MRelated(models.Model):
    """
    Regression test for #248.

    A model with an M2M field (Classroom) being also used as an M2M field from another model (ClassroomM2MRelated).
    """

    related_classrooms = models.ManyToManyField(Classroom)


class Store(models.Model):
    customers = models.ManyToManyField(Person, related_name="favorite_stores")
    employees = models.ManyToManyField(Person, related_name="employers")
    suppliers = models.ManyToManyField(
        Person, related_name="suppliers", blank=True, null=True
    )


class DummyEmptyModel(models.Model):
    pass


class DummyIntModel(models.Model):
    int_field = models.IntegerField()
    small_int_field = models.SmallIntegerField()
    big_int_field = models.BigIntegerField()


class DummyPositiveIntModel(models.Model):
    positive_small_int_field = models.PositiveSmallIntegerField()
    positive_int_field = models.PositiveIntegerField()
    positive_big_int_field = models.PositiveBigIntegerField()


class DummyNumbersModel(models.Model):
    float_field = models.FloatField()


class DummyDecimalModel(models.Model):
    decimal_field = models.DecimalField(max_digits=1, decimal_places=0)


class UnsupportedField(models.Field):
    description = "I'm bad company, baker doesn't know me"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def db_type(self, connection):
        # Return a real database type so Django can create the column
        # The field remains "unsupported" by Baker (no generator defined)
        return "varchar(255)"


class UnsupportedModel(models.Model):
    unsupported_field = UnsupportedField()


if BAKER_CONTENTTYPES:

    class DummyGenericForeignKeyModel(models.Model):
        content_type = models.ForeignKey(
            contenttypes.ContentType,
            on_delete=models.CASCADE,
            limit_choices_to={"model__in": ["person", "dog"]},
        )
        object_id = models.PositiveIntegerField()
        content_object = GenericForeignKey("content_type", "object_id")

    class DummyGenericRelationModel(models.Model):
        relation = GenericRelation(DummyGenericForeignKeyModel)

    class GenericForeignKeyModelWithOptionalData(models.Model):
        content_type = models.ForeignKey(
            contenttypes.ContentType,
            on_delete=models.CASCADE,
            blank=True,
            null=True,
            limit_choices_to={"model__in": ["person", "dog"]},
        )
        object_id = models.PositiveIntegerField(blank=True, null=True)
        content_object = GenericForeignKey("content_type", "object_id")

    class GenericRelationModelWithOptionalData(models.Model):
        relation = GenericRelation(GenericForeignKeyModelWithOptionalData)


class DummyNullFieldsModel(models.Model):
    null_foreign_key = models.ForeignKey(
        "DummyBlankFieldsModel", null=True, on_delete=models.CASCADE
    )
    null_integer_field = models.IntegerField(null=True)


class DummyBlankFieldsModel(models.Model):
    blank_char_field = models.CharField(max_length=50, blank=True)
    blank_text_field = models.TextField(max_length=300, blank=True)


class ExtendedDefaultField(models.IntegerField):
    pass


class DummyDefaultFieldsModel(models.Model):
    default_id = models.AutoField(primary_key=True)
    default_char_field = models.CharField(max_length=50, default="default")
    default_text_field = models.TextField(default="default")
    default_int_field = models.IntegerField(default=123)
    default_float_field = models.FloatField(default=123.0)
    default_date_field = models.DateField(default="2012-01-01")
    default_date_time_field = models.DateTimeField(
        default=tz_aware(datetime.datetime(2012, 1, 1))
    )
    default_time_field = models.TimeField(default="00:00:00")
    default_decimal_field = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0")
    )
    default_email_field = models.EmailField(default="foo@bar.org")
    default_slug_field = models.SlugField(default="a-slug")
    default_unknown_class_field = ExtendedDefaultField(default=42)
    default_callable_int_field = models.IntegerField(default=lambda: 12)
    default_callable_datetime_field = models.DateTimeField(default=now)


class DummyFileFieldModel(models.Model):
    fs = FileSystemStorage(location=gettempdir())
    file_field = models.FileField(upload_to="%Y/%m/%d", storage=fs)


if has_pil:

    class DummyImageFieldModel(models.Model):
        fs = FileSystemStorage(location=gettempdir())
        image_field = models.ImageField(upload_to="%Y/%m/%d", storage=fs)

else:
    # doesn't matter, won't be using
    class DummyImageFieldModel(models.Model):
        pass


class NestedFileFieldModel(models.Model):
    attached_file = models.ForeignKey(DummyFileFieldModel, on_delete=models.CASCADE)


class DummyMultipleInheritanceModel(DummyDefaultFieldsModel, Person):
    my_id = models.AutoField(primary_key=True)
    my_dummy_field = models.IntegerField()


class Ambiguous(models.Model):
    name = models.CharField(max_length=20)


class School(models.Model):
    name = models.CharField(max_length=50)
    students = models.ManyToManyField(Person, through="SchoolEnrollment")


class SchoolEnrollment(models.Model):
    start_date = models.DateField(auto_now_add=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    student = models.ForeignKey(Person, on_delete=models.CASCADE)


class NonAbstractPerson(Person):
    dummy_count = models.IntegerField()


class CustomFieldWithGeneratorModel(models.Model):
    custom_value = CustomFieldWithGenerator()


class CustomFieldWithoutGeneratorModel(models.Model):
    custom_value = CustomFieldWithoutGenerator()


class CustomFieldViaSettingsModel(models.Model):
    custom_value = CustomFieldViaSettings()


class CustomForeignKeyWithGeneratorModel(models.Model):
    custom_fk = CustomForeignKey(
        Profile, blank=True, null=True, on_delete=models.CASCADE
    )


class DummyUniqueIntegerFieldModel(models.Model):
    value = models.IntegerField(unique=True)


class ModelWithNext(models.Model):
    attr = models.CharField(max_length=10)

    def next(self):
        return "foo"


class BaseModelForNext(models.Model):
    fk = models.ForeignKey(ModelWithNext, on_delete=models.CASCADE)


class BaseModelForList(models.Model):
    fk = FakeListField()


class Movie(models.Model):
    title = models.CharField(max_length=30)


class MovieManager(models.Manager):
    def get_queryset(self):
        """
        Annotate queryset with an alias field 'name'.

        We want to test whether this annotation has been run after
        calling `baker.make()`.
        """
        return super().get_queryset().annotate(name=models.F("title"))


class MovieWithAnnotation(Movie):
    objects = MovieManager()


class CastMember(models.Model):
    movie = models.ForeignKey(
        Movie, related_name="cast_members", on_delete=models.CASCADE
    )
    person = models.ForeignKey(Person, on_delete=models.CASCADE)


class DummyGenericIPAddressFieldModel(models.Model):
    ipv4_field = models.GenericIPAddressField(protocol="IPv4")
    ipv6_field = models.GenericIPAddressField(protocol="IPv6")
    ipv46_field = models.GenericIPAddressField(protocol="both")


class AbstractModel(models.Model):
    class Meta:
        abstract = True

    name = models.CharField(max_length=30)


class SubclassOfAbstract(AbstractModel):
    height = models.IntegerField()


class NonStandardManager(models.Model):
    name = models.CharField(max_length=30)

    manager = models.Manager()


# The following models were added after issue 291
# Since they don't hold much meaning, they are only numbered ones
class Issue291Model1(models.Model):
    pass


class Issue291Model2(models.Model):
    m2m_model_1 = models.ManyToManyField(Issue291Model1)


class Issue291Model3(models.Model):
    fk_model_2 = models.ForeignKey(
        Issue291Model2, related_name="bazs", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=32)


class ModelWithAutoNowFields(models.Model):
    sent_date = models.DateTimeField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
