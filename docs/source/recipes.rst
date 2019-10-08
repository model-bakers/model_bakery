Recipes
=======

If you're not comfortable with random data or even you just want to
improve the semantics of the generated data, there's hope for you.

You can define a recipe, which is a set of rules to generate data
for your models. 

It's also possible to store the Recipes in a module called *mommy_recipes.py*
at your app's root directory. This recipes can later be used with the
`make_recipe` function: ::

    fixtures/
    migrations/
    templates/
    tests/
    __init__.py
    admin.py
    managers.py
    models.py
    mommy_recipes.py
    urls.py
    views.py


File: mommy_recipes.py ::

    from model_mommy.recipe import Recipe
    from family.models import Person

    person = Recipe(
        Person,
        name = 'John Doe',
        nickname = 'joe',
        age = 18,
        birthday = date.today(),
        appointment = datetime.now()
    )

.. note::

    You don't have to declare all the fields if you don't want to. Omitted fields will be generated automatically.


File: test_model.py ::

    from django.test import TestCase

    from model_mommy import mommy
    from model_mommy.recipe import Recipe, foreign_key

    # Relative imports of the 'app-name' package
    from .models import Person, Contact

    class PersonTestModel(TestCase):
        """Class to test the model Person"""

        def setUp(self):
            # Load the recipe 'person' from 'family/mommy_recipes.py'
            self.person_one = mommy.make_recipe(
                'family.person'
            )

            self.person_simpsons = Recipe(
                Person,
                name='Moe',
            )

            self.contact = Recipe(
                Contact,
                person=foreign_key(self.person_simpsons),
                tel='3333333eeeeR'
            )
    
        def test_kind_contact_create_instance(self):
            """True if create instance"""
            contact = self.contact.make()
            self.assertIsInstance(contact, Contact)

Or if you don't want a persisted instance: ::

    from model_mommy import mommy

    mommy.prepare_recipe('family.person')


Another examples

.. note::

    You can use the _quantity parameter as well if you want to create more than one object from a single recipe.

.. note::
    
    You can define recipes locally to your module or test case as well. This can be useful for cases where a particular set of values may be unique to a particular test case, but used repeatedly there.


Look: 

File: mommy_recipes.py ::

    company_recipe = Recipe(Company, name='WidgetCo')

File: test_model.py ::

    class EmployeeTest(TestCase):
        def setUp(self):
            self.employee_recipe = Recipe(
                Employee,
                name=seq('Employee '),
                company=company_recipe.make()
            )

        def test_employee_list(self):
            self.employee_recipe.make(_quantity=3)
            # test stuff....

        def test_employee_tasks(self):
            employee1 = self.employee_recipe.make()
            task_recipe = Recipe(Task, employee=employee1)
            task_recipe.make(status='done')
            task_recipe.make(due_date=datetime(2014, 1, 1))
            # test stuff....

Recipes with foreign keys
-------------------------

You can define `foreign_key` relations:

.. code-block:: python

    from model_mommy.recipe import Recipe, foreign_key
    from family.models import Person, Dog


    person = Recipe(Person,
        name = 'John Doe',
        nickname = 'joe',
        age = 18,
        birthday = date.today(),
        appointment = datetime.now()
    )

    dog = Recipe(Dog,
        breed = 'Pug',
        owner = foreign_key(person)
    )

Notice that `person` is a *recipe*.

You may be thinking: "I can put the Person model instance directly in the owner field". That's not recommended.

Using the `foreign_key` is important for 2 reasons:

* Semantics. You'll know that attribute is a foreign key when you're reading;
* The associated instance will be created only when you call `make_recipe` and not during recipe definition;

You can also use `related`, when you want two or more models to share the same parent:

.. code-block:: python


    from model_mommy.recipe import related, Recipe

    dog = Recipe(Dog,
        breed = 'Pug',
    )
    other_dog = Recipe(Dog,
        breed = 'Boxer',
    )
    person_with_three_dogs = Recipe(Person,
        dog_set = related('dog', 'other_dog')
    )

Note this will only work when calling `make_recipe` because the related manager requires the objects in the related_set to be persisted. That said, calling `prepare_recipe` the related_set will be empty.

If you want to set m2m relationship you can use `related` as well:

.. code-block:: python

    class Dog(models.Model):
        owner = models.ForeignKey('Person')
        breed = models.CharField(max_length=50)
        created = models.DateTimeField(auto_now_add=True)
        friends_with = models.ManyToManyField('Dog')


    from model_mommy.recipe import related, Recipe

    dog = Recipe(Dog,
        breed = 'Pug',
    )

    dog_with_friends = dog.extend(
        friends_with=related(dog, dog),
    )


Recipes with callables
----------------------

It's possible to use *callables* as recipe's attribute value.

.. code-block:: python

    from datetime import date
    from model_mommy.recipe import Recipe
    from family.models import Person

    person = Recipe(Person,
        birthday = date.today,
    )

When you call `make_recipe`, *Mommy* will set the attribute to the value returned by the callable.


Recipes with iterators
----------------------

You can also use *iterators* (including *generators*) to provide multiple values to a recipe.

.. code-block:: python

    from itertools import cycle

    colors = ['red', 'green', 'blue', 'yellow']
    person = Recipe(Person,
        favorite_color = cycle(colors)
    )

*Mommy* will use the next value in the *iterator* every time you create a model from the recipe.

Sequences in recipes
--------------------

Sometimes, you have a field with an unique value and using `make` can cause random errors. Also, passing an attribute value just to avoid uniqueness validation problems can be tedious. To solve this you can define a sequence with `seq`

.. code-block:: python


    from model_mommy.recipe import Recipe, seq
    from family.models import Person

    person = Recipe(Person,
        name = seq('Joe'),
        age = seq(15)
    )

    p = mommy.make_recipe('myapp.person')
    p.name
    >>> 'Joe1'
    p.age
    >>> 16

    p = mommy.make_recipe('myapp.person')
    p.name
    >>> 'Joe2'
    p.age
    >>> 17

This will append a counter to strings to avoid uniqueness problems and it will sum the counter with numerical values.

Sequences can be used not only for recipes, but with `mommy.make` as well:

.. code-block:: python


    # it can be imported directly from model_mommy
    from model_mommy import seq
    from model_mommy import mommy

    p = mommy.make('Person', name=seq('Joe'))
    p.name
    >>> 'Joe1'

    people = mommy.make('Person', name=seq('Chad'), _quantity=3)
    for person in people:
        print(person.name)
    >>> 'Chad1'
    >>> 'Chad2'
    >>> 'Chad3'

You can also provide an optional `increment_by` argument which will modify incrementing behaviour. This can be an integer, float, Decimal or timedelta.

.. code-block:: python


    from datetime import date, timedelta
    from model_mommy.recipe import Recipe, seq
    from family.models import Person


    person = Recipe(Person,
        age = seq(15, increment_by=3)
        height_ft = seq(5.5, increment_by=.25)
        # assume today's date is 21/07/2014
        appointment = seq(date(2014, 7, 21), timedelta(days=1))
    )

    p = mommy.make_recipe('myapp.person')
    p.age
    >>> 18
    p.height_ft
    >>> 5.75
    p.appointment
    >>> datetime.date(2014, 7, 22)

    p = mommy.make_recipe('myapp.person')
    p.age
    >>> 21
    p.height_ft
    >>> 6.0
    p.appointment
    >>> datetime.date(2014, 7, 23)

Overriding recipe definitions
-----------------------------

Passing values when calling `make_recipe` or `prepare_recipe` will override the recipe rule.

.. code-block:: python

    from model_mommy import mommy

    mommy.make_recipe('model_mommy.person', name='Peter Parker')

This is useful when you have to create multiple objects and you have some unique field, for instance.

Recipe inheritance
------------------

If you need to reuse and override existent recipe call extend method:

.. code-block:: python

    dog = Recipe(Dog,
        breed = 'Pug',
        owner = foreign_key(person)
    )
    extended_dog = dog.extend(
        breed = 'Super basset',
    )
