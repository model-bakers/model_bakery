import os

import django
from django.conf import settings


def pytest_configure():
    test_db = os.environ.get("TEST_DB", "sqlite")
    installed_apps = [
        "django.contrib.contenttypes",
        "tests.generic",
        "tests.ambiguous",
        "tests.ambiguous2",
    ]

    if test_db == "sqlite":
        db_engine = "django.db.backends.sqlite3"
        db_name = ":memory:"
    elif test_db == "postgresql":
        db_engine = "django.db.backends.postgresql_psycopg2"
        db_name = "postgres"
        installed_apps = ["django.contrib.postgres"] + installed_apps
    elif test_db == "postgis":
        db_engine = "django.contrib.gis.db.backends.postgis"
        db_name = "postgres"
        installed_apps = [
            "django.contrib.postgres",
            "django.contrib.gis",
        ] + installed_apps
    else:
        raise NotImplementedError("Tests for % are not supported", test_db)
    settings.configure(
        DATABASES={"default": {"ENGINE": db_engine, "NAME": db_name}},
        INSTALLED_APPS=installed_apps,
        LANGUAGE_CODE="en",
        SITE_ID=1,
        MIDDLEWARE=(),
        USE_TZ=os.environ.get("USE_TZ", False),
    )
    django.setup()
