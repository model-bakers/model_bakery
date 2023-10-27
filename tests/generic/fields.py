from django.db import models


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
