from django.apps import apps

BAKER_GIS = apps.is_installed("django.contrib.gis")

default_gis_mapping = {}

__all__ = ["BAKER_GIS", "default_gis_mapping"]

if BAKER_GIS:
    from django.contrib.gis.db.models import (
        GeometryCollectionField,
        GeometryField,
        LineStringField,
        MultiLineStringField,
        MultiPointField,
        MultiPolygonField,
        PointField,
        PolygonField,
    )

    from . import random_gen

    default_gis_mapping[GeometryField] = random_gen.gen_geometry
    default_gis_mapping[PointField] = random_gen.gen_point
    default_gis_mapping[LineStringField] = random_gen.gen_line_string
    default_gis_mapping[PolygonField] = random_gen.gen_polygon
    default_gis_mapping[MultiPointField] = random_gen.gen_multi_point
    default_gis_mapping[MultiLineStringField] = random_gen.gen_multi_line_string
    default_gis_mapping[MultiPolygonField] = random_gen.gen_multi_polygon
    default_gis_mapping[GeometryCollectionField] = random_gen.gen_geometry_collection
