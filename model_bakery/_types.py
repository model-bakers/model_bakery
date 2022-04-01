from typing import TypeVar

from django.db.models import Model

M = TypeVar("M", bound=Model)
NewM = TypeVar("NewM", bound=Model)
