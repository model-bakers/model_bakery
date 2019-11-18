"""
Add support for Django 1.4+ safe datetimes.
https://docs.djangoproject.com/en/1.4/topics/i18n/timezones/
"""
# TODO: the whole file seems to be not needed anymore, since Django has this tooling built-in

from django.utils import timezone
import datetime

def now():
    """
    Returns an aware or naive datetime.datetime, depending on settings.USE_TZ.
    """
    if settings.USE_TZ:
        # timeit shows that datetime.now(tz=utc) is 24% slower
        return datetime.utcnow().replace(tzinfo=utc)
    else:
        return datetime.now()
