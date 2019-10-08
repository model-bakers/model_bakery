from model_mommy.recipe import Recipe
from tests.generic.models import Person

from datetime import date, datetime

person = Recipe(
    Person,
    name='John Deeper',
    nickname='joe',
    age=18,
    bio='Someone in the crowd',
    blog='http://joe.blogspot.com',
    wanted_games_qtd=4,
    birthday=date.today(),
    appointment=datetime.now(),
    birth_time=datetime.now
)
