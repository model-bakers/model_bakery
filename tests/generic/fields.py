from django.db import models
from django.db.models.fields.mixins import FieldCacheMixin


class CustomFieldWithGenerator(models.TextField):
    pass


class CustomFieldWithoutGenerator(models.TextField):
    pass


class CustomFieldViaSettings(models.TextField):
    pass


class FakeListField(models.TextField):
    def to_python(self, value):
        return value.split()

    def get_prep_value(self, value):
        return " ".join(value)


class CustomForeignKey(models.ForeignKey):
    pass


class PrivateMarkerField(FieldCacheMixin):
    """Virtual field that lives only in ``_meta.private_fields``.

    Mirrors how ``GenericForeignKey`` attaches to a model — no DB column, no
    entry in ``_meta.fields`` — but without the contenttypes dependency. Used
    to exercise code paths that must surface private fields regardless of
    whether contenttypes is installed.
    """

    auto_created = False
    concrete = False
    editable = False
    hidden = False
    is_relation = True
    many_to_many = False
    many_to_one = True
    one_to_many = False
    one_to_one = False
    related_model = None
    remote_field = None

    def __str__(self):
        return f"{self.model._meta.label}.{self.name}"

    def contribute_to_class(self, cls, name, **kwargs):
        self.name = name
        self.attname = name
        self.model = cls
        cls._meta.add_field(self, private=True)
