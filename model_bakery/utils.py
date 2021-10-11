import datetime
import importlib
import inspect
import itertools
import warnings
from types import ModuleType
from typing import Any, Callable, Optional, Union

from django.apps import apps

from .timezone import tz_aware

__all__ = ["import_from_str", "get_calling_module", "seq"]


def import_from_str(import_string: Optional[Union[Callable, str]]) -> Any:
    """Import an object defined as import if it is an string.

    If `import_string` follows the format `path.to.module.object_name`,
    this method imports it; else it just return the object.
    """
    if isinstance(import_string, str):
        path, field_name = import_string.rsplit(".", 1)

        if apps:
            model = apps.all_models.get(path, {}).get(field_name.lower())
            if model:
                return model

        module = importlib.import_module(path)
        return getattr(module, field_name)
    else:
        return import_string


def get_calling_module(levels_back: int) -> Optional[ModuleType]:
    """Get the module some number of stack frames back from the current one.

    Make sure to account for the number of frames between the "calling" code
    and the one that calls this function.

    Args:
        levels_back (int): Number of stack frames back from the current

    Returns:
        (ModuleType): the module from which the code was called
    """
    frame = inspect.stack()[levels_back + 1][0]
    return inspect.getmodule(frame)


def seq(value, increment_by=1, start=None, suffix=None):
    """Generate a sequence of values based on a running count.

    This function can be used to generate sequences of `int`, `float`,
    `datetime`, `date`, `time`, or `str`: whatever the `type` is of the
    provided `value`.

    Args:
        value (object): the value at which to begin generation (this will
            be ignored for types `datetime`, `date`, and `time`)
        increment_by (`int` or `float`, optional): the amount by which to
            increment for each generated value (defaults to `1`)
        start (`int` or `float`, optional): the value at which the sequence
            will begin to add to `value` (if `value` is a `str`, `start` will
            be appended to it)
        suffix (`str`, optional): for `str` `value` sequences, this will be
            appended to the end of each generated value (after the counting
            value is appended)

    Returns:
        object: generated values for sequential data
    """
    _validate_sequence_parameters(value, increment_by, start, suffix)

    if type(value) in [datetime.datetime, datetime.date, datetime.time]:
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
            if suffix:
                yield value + str(n) + suffix
            else:
                yield value + type(value)(n)


def _validate_sequence_parameters(value, increment_by, start, suffix) -> None:
    if suffix:
        if not isinstance(suffix, str):
            raise TypeError("Sequences suffix can only be a string")

        if not isinstance(value, str):
            raise TypeError("Sequences with suffix can only be used with text values")

    if type(value) in [datetime.datetime, datetime.date, datetime.time]:
        if not isinstance(increment_by, datetime.timedelta):
            raise TypeError(
                "Sequences with values datetime.datetime, datetime.date and datetime.time, "
                "incremente_by must be a datetime.timedelta."
            )

        if start:
            warnings.warn(
                "start parameter is ignored when using seq with date, time or datetime objects"
            )
