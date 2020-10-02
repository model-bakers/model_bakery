import datetime
import importlib
import itertools
import warnings

from .timezone import tz_aware


def import_from_str(import_string):
    """Import an object defined as import if it is an string.

    If `import_string` follows the format `path.to.module.object_name`,
    this method imports it; else it just return the object.
    """
    if isinstance(import_string, str):
        path, field_name = import_string.rsplit(".", 1)
        module = importlib.import_module(path)
        return getattr(module, field_name)
    else:
        return import_string


def seq(value, increment_by=1, start=None, suffix=None):
    if type(value) in [datetime.datetime, datetime.date, datetime.time]:
        if start:
            msg = "start parameter is ignored when using seq with date, time or datetime objects"
            warnings.warn(msg)

        if type(value) is datetime.date:
            date = datetime.datetime.combine(value, datetime.datetime.now().time())
        elif type(value) is datetime.time:
            date = datetime.datetime.combine(datetime.date.today(), value)
        else:
            date = value

        # convert to epoch time
        start = (date - datetime.datetime(1970, 1, 1)).total_seconds()
        increment_by = increment_by.total_seconds()
        for n in itertools.count(increment_by, increment_by):
            series_date = tz_aware(datetime.datetime.utcfromtimestamp(start + n))
            if type(value) is datetime.time:
                yield series_date.time()
            elif type(value) is datetime.date:
                yield series_date.date()
            else:
                yield series_date
    else:
        for n in itertools.count(start or increment_by, increment_by):
            yield value + type(value)(n) + (suffix or type(value)())
