from django.apps import apps

BAKER_CONTENTTYPES = apps.is_installed("django.contrib.contenttypes")

default_contenttypes_mapping = {}

__all__ = ["BAKER_CONTENTTYPES", "default_contenttypes_mapping"]

if BAKER_CONTENTTYPES:
    from django.contrib.contenttypes.fields import GenericForeignKey
    from django.contrib.contenttypes.models import ContentType

    from . import random_gen

    default_contenttypes_mapping[ContentType] = random_gen.gen_content_type
    # a small hack to generate random object for GenericForeignKey
    default_contenttypes_mapping[GenericForeignKey] = random_gen.gen_content_type
