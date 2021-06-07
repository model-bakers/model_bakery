from django.utils.timezone import now

from model_bakery.recipe import Recipe
from tests.generic.models import Person

person = Recipe(
    Person,
    name="Uninstalled",
    nickname="uninstalled",
    age=18,
    bio="Uninstalled",
    blog="http://uninstalled.com",
    days_since_last_login=4,
    birthday=now().date(),
    appointment=now(),
    birth_time=now(),
)
