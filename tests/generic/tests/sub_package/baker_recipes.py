from datetime import date, datetime

from model_bakery.recipe import Recipe
from tests.generic.models import Person

person = Recipe(
    Person,
    name="John Deeper",
    nickname="joe",
    age=18,
    bio="Someone in the crowd",
    blog="http://joe.blogspot.com",
    days_since_last_login=4,
    birthday=date.today(),
    appointment=datetime.now(),
    birth_time=datetime.now,
)
