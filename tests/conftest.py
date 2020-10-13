import os

import django
from django.conf import settings


def pytest_configure():
    test_db = os.environ.get("TEST_DB", "sqlite")
    installed_apps = [
        "django.contrib.contenttypes",
        "django.contrib.auth",
        "tests.generic",
        "tests.ambiguous",
        "tests.ambiguous2",
    ]

    using_postgres_flag = False
    if test_db == "sqlite":
        db_engine = "django.db.backends.sqlite3"
        db_name = ":memory:"
    elif test_db == "postgresql":
        using_postgres_flag = True
        db_engine = "django.db.backends.postgresql_psycopg2"
        db_name = "postgres"
        installed_apps = ["django.contrib.postgres"] + installed_apps
    elif test_db == "postgis":
        using_postgres_flag = True
        db_engine = "django.contrib.gis.db.backends.postgis"
        db_name = "postgres"
        installed_apps = [
            "django.contrib.postgres",
            "django.contrib.gis",
        ] + installed_apps
    else:
        raise NotImplementedError("Tests for % are not supported", test_db)

    settings.configure(
        DATABASES={
            "default": {
                "ENGINE": db_engine,
                "NAME": db_name,
                "HOST": "localhost",
                # The following DB settings are only used for `postgresql` and `postgis`
                "PORT": os.environ.get("PGPORT", ""),
                "USER": os.environ.get("PGUSER", ""),
                "PASSWORD": os.environ.get("PGPASSWORD", "")
            }
        },
        INSTALLED_APPS=installed_apps,
        LANGUAGE_CODE="en",
        SITE_ID=1,
        MIDDLEWARE=(),
        USE_TZ=os.environ.get("USE_TZ", False),
        USING_POSTGRES=using_postgres_flag,
    )

    from model_bakery import baker

    def gen_same_text():
        return "always the same text"

    baker.generators.add("tests.generic.fields.CustomFieldViaSettings", gen_same_text)

    django.setup()
