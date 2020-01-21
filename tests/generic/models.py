#######################################
# TESTING PURPOSE ONLY MODELS!!       #
# DO NOT ADD THE APP TO INSTALLED_APPS#
#######################################
import datetime as base_datetime
from decimal import Decimal
from tempfile import gettempdir

from model_bakery.gis import BAKER_GIS

from django.core.files.storage import FileSystemStorage

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey

from .fields import (
    CustomFieldWithGenerator,
    CustomFieldWithoutGenerator,
    CustomFieldViaSettings,
    FakeListField,
    CustomForeignKey,
)
from model_bakery.timezone import smart_datetime as datetime

# check whether or not PIL is installed
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

GENDER_CHOICES = [
    ("M", "male"),
    ("F", "female"),
    ("N", "non-binary"),
]

OCCUPATION_CHOICES = (
    ("Service Industry", (("waitress", "Waitress"), ("bartender", "Bartender"))),
    ("Education", (("teacher", "Teacher"), ("principal", "Principal"))),
)

TEST_TIME = base_datetime.datetime(2014, 7, 21, 15, 39, 58, 457698)


class ModelWithImpostorField(models.Model):
    pass


class Profile(models.Model):
    email = models.EmailField()


class User(models.Model):
    profile = models.ForeignKey(
        Profile, blank=True, null=True, on_delete=models.CASCADE
    )


class PaymentBill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    value = models.FloatField()


class Person(models.Model):
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    happy = models.BooleanField(default=True)
    unhappy = models.BooleanField(default=False)
    bipolar = models.BooleanField(default=False)
    name = models.CharField(max_length=30)
    nickname = models.SlugField(max_length=36)
    age = models.IntegerField()
    bio = models.TextField()
    birthday = models.DateField()
    birth_time = models.TimeField()
    appointment = models.DateTimeField()
    blog = models.URLField()
    occupation = models.CharField(max_length=10, choices=OCCUPATION_CHOICES)
    uuid = models.UUIDField(primary_key=False)
    name_hash = models.BinaryField(max_length=16)
    wanted_games_qtd = models.BigIntegerField()
    duration_of_sleep = models.DurationField()
    email = models.EmailField()
    id_document = models.CharField(unique=True, max_length=10)

    try:
        from django.contrib.postgres.fields import ArrayField, HStoreField, JSONField
        from django.contrib.postgres.fields.citext import (
            CICharField,
            CIEmailField,
            CITextField,
        )

        acquaintances = ArrayField(models.IntegerField())
        data = JSONField()
        hstore_data = HStoreField()
        ci_char = CICharField(max_length=30)
        ci_email = CIEmailField()
        ci_text = CITextField()
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


class RelatedNamesModel(models.Model):
    name = models.CharField(max_length=256)
    one_to_one = models.OneToOneField(
        Person, related_name="one_related", on_delete=models.CASCADE
    )
    foreign_key = models.ForeignKey(
        Person, related_name="fk_related", on_delete=models.CASCADE
    )


class ModelWithOverridedSave(Dog):
    def save(self, *args, **kwargs):
        self.owner = kwargs.pop("owner")
        return super(ModelWithOverridedSave, self).save(*args, **kwargs)


class Classroom(models.Model):
    students = models.ManyToManyField(Person, null=True)
    active = models.NullBooleanField()


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


class DummyNumbersModel(models.Model):
    float_field = models.FloatField()


class DummyDecimalModel(models.Model):
    decimal_field = models.DecimalField(max_digits=1, decimal_places=0)


class UnsupportedField(models.Field):
    description = "I'm bad company, baker doesn't know me"

    def __init__(self, *args, **kwargs):
        super(UnsupportedField, self).__init__(*args, **kwargs)


class UnsupportedModel(models.Model):
    unsupported_field = UnsupportedField()


class DummyGenericForeignKeyModel(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")


class DummyGenericRelationModel(models.Model):
    relation = GenericRelation(DummyGenericForeignKeyModel)


class DummyNullFieldsModel(models.Model):
    null_foreign_key = models.ForeignKey(
        "DummyBlankFieldsModel", null=True, on_delete=models.CASCADE
    )
    null_integer_field = models.IntegerField(null=True)


class DummyBlankFieldsModel(models.Model):
    blank_char_field = models.CharField(max_length=50, blank=True)
    blank_text_field = models.TextField(max_length=300, blank=True)


class DummyDefaultFieldsModel(models.Model):
    default_id = models.AutoField(primary_key=True)
    default_char_field = models.CharField(max_length=50, default="default")
    default_text_field = models.TextField(default="default")
    default_int_field = models.IntegerField(default=123)
    default_float_field = models.FloatField(default=123.0)
    default_date_field = models.DateField(default="2012-01-01")
    default_date_time_field = models.DateTimeField(default=datetime(2012, 1, 1))
    default_time_field = models.TimeField(default="00:00:00")
    default_decimal_field = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0")
    )
    default_email_field = models.EmailField(default="foo@bar.org")
    default_slug_field = models.SlugField(default="a-slug")


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


class DummyMultipleInheritanceModel(DummyDefaultFieldsModel, Person):
    my_id = models.AutoField(primary_key=True)
    my_dummy_field = models.IntegerField()


class Ambiguous(models.Model):
    name = models.CharField(max_length=20)


class School(models.Model):
    name = models.CharField(max_length=10)
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
        """Annotate queryset with an alias field 'name'.

        We want to test whether this annotation has been run after
        calling baker.make().
        """
        return super(MovieManager, self).get_queryset().annotate(name=models.F("title"))


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
    class Meta(object):
        abstract = True

    name = models.CharField(max_length=30)


class SubclassOfAbstract(AbstractModel):
    height = models.IntegerField()
