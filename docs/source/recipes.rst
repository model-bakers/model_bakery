Recipes
=======

If you're not comfortable with random data or even if you just want to
improve the semantics of the generated data, there's hope for you.

You can define a **Recipe**, which is a set of rules to generate data
for your models.

It's also possible to store the Recipes in a module called *baker_recipes.py*
at your app's root directory. This recipes can later be used with the
``make_recipe`` function: ::

    shop/
      migrations/
      __init__.py
      admin.py
      apps.py
      baker_recipes.py   <--- where you should place your Recipes
      models.py
      tests.py
      views.py


File: **baker_recipes.py** ::

    from model_bakery.recipe import Recipe
    from shop.models import Customer

    customer_joe = Recipe(
        Customer,
        name='John Doe',
        nickname='joe',
        age=18,
        birthday=date.today(),
        last_shopping=datetime.now()
    )

.. note::

    You don't have to declare all the fields if you don't want to. Omitted fields will be generated automatically.


File: **test_model.py** ::

    from django.test import TestCase

    from model_bakery import baker

    from shop.models import Customer, Contact

    class CustomerTestModel(TestCase):

        def setUp(self):
            # Load the recipe 'customer_joe' from 'shop/baker_recipes.py'
            self.customer_one = baker.make_recipe(
                'shop.customer_joe'
            )


Or if you don't want a persisted instance: ::

    from model_bakery import baker

    baker.prepare_recipe('shop.customer_joe')


.. note::

    You don't have to place necessarily your ``baker_recipes.py`` file inside your app's root directory.
    If you have a tests directory within the app, for example, you can add your recipes inside it and still
    use ``make_recipe``/``prepare_recipe`` by adding the tests module to the string you've passed as an argument.
    For example: ``baker.make_recipe("shop.tests.customer_joe")``

    So, short summary, you can place your ``barker_recipes.py`` **anywhere** you want to and to use it having in mind
    you'll only have to simulate an import but ofuscating the ``barker_recipes`` module from the import string.


.. note::

    You can use the _quantity parameter as well if you want to create more than one object from a single recipe.


You can define recipes locally to your module or test case as well. This can be useful for cases where a particular set of values may be unique to a particular test case, but used repeatedly there. For example:

File: **baker_recipes.py** ::

    company_recipe = Recipe(Company, name='WidgetCo')

File: **test_model.py** ::

    class EmployeeTest(TestCase):
        def setUp(self):
            self.employee_recipe = Recipe(
                Employee,
                name=seq('Employee '),
                company=baker.make_recipe('app.company_recipe')
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

You can define ``foreign_key`` relations:

.. code-block:: python

    from model_bakery.recipe import Recipe, foreign_key
    from shop.models import Customer, PurchaseHistory

    customer = Recipe(Customer,
        name='John Doe',
        nickname='joe',
        age=18,
        birthday=date.today(),
        appointment=datetime.now()
    )

    history = Recipe(PurchaseHistory,
        owner=foreign_key(customer)
    )

Notice that ``customer`` is a *recipe*.

You may be thinking: "I can put the Customer model instance directly in the owner field". That's not recommended.

Using the ``foreign_key`` is important for 2 reasons:

* Semantics. You'll know that attribute is a foreign key when you're reading;
* The associated instance will be created only when you call ``make_recipe`` and not during recipe definition;

You can also use ``related``, when you want two or more models to share the same parent:

.. code-block:: python


    from model_bakery.recipe import related, Recipe
    from shop.models import Customer, PurchaseHistory

    history = Recipe(PurchaseHistory)
    customer_with_2_histories = Recipe(Customer,
        name='Albert',
        purchasehistory_set=related('history', 'history'),
    )

Note this will only work when calling ``make_recipe`` because the related manager requires the objects in the related_set to be persisted. That said, calling ``prepare_recipe`` the related_set will be empty.

If you want to set m2m relationship you can use ``related`` as well:

.. code-block:: python

    from model_bakery.recipe import related, Recipe

    pencil = Recipe(Product, name='Pencil')
    pen = Recipe(Product, name='Pen')
    history = Recipe(PurchaseHistory)

    history_with_prods = history.extend(
        products=related(pencil, pen)
    )

When creating models based on a ``foreign_key`` recipe using the ``_quantity`` argument, only one related model will be created for all new instances.

.. code-block:: python
    from model_baker.recipe import foreign_key, Recipe

    person = Recipe(Person, name='Albert')
    dog = Recipe(Dog, owner=foreign_key(person))

    # All dogs share the same owner
    dogs = dog.make_recipe(_quantity=2)
    assert dogs[0].owner.id == dogs[1].owner.id

This will cause an issue if your models use ``OneToOneField``. In that case, you can provide ``one_to_one=True`` to the recipe to make sure every instance created by ``_quantity`` has a unique id.

.. code-block:: python
    from model_baker.recipe import foreign_key, Recipe

    person = Recipe(Person, name='Albert')
    dog = Recipe(Dog, owner=foreign_key(person, one_to_one=True))

    # Each dog has a unique owner
    dogs = dog.make_recipe(_quantity=2)
    assert dogs[0].owner.id != dogs[1].owner.id



Recipes with callables
----------------------

It's possible to use ``callables`` as recipe's attribute value.

.. code-block:: python

    from datetime import date
    from model_bakery.recipe import Recipe
    from shop.models import Customer

    customer = Recipe(
        Customer,
        birthday=date.today,
    )

When you call ``make_recipe``, Model Bakery will set the attribute to the value returned by the callable.


Recipes with iterators
----------------------

You can also use *iterators* (including *generators*) to provide multiple values to a recipe.

.. code-block:: python

    from itertools import cycle

    names = ['Ada Lovelace', 'Grace Hopper', 'Ida Rhodes', 'Barbara Liskov']
    customer = Recipe(Customer,
        name=cycle(names)
    )

Model Bakery will use the next value in the *iterator* every time you create a model from the recipe.

Sequences in recipes
--------------------

Sometimes, you have a field with an unique value and using ``make`` can cause random errors. Also, passing an attribute value just to avoid uniqueness validation problems can be tedious. To solve this you can define a sequence with ``seq``

.. code-block:: python


    >>> from model_bakery.recipe import Recipe, seq
    >>> from shop.models import Customer

    >>> customer = Recipe(Customer,
        name=seq('Joe'),
        age=seq(15)
    )

    >>> customer = baker.make_recipe('shop.customer')
    >>> customer.name
    'Joe1'
    >>> customer.age
    16

    >>> new_customer = baker.make_recipe('shop.customer')
    >>> new_customer.name
    'Joe2'
    >>> new_customer.age
    17

This will append a counter to strings to avoid uniqueness problems and it will sum the counter with numerical values.

An optional ``suffix`` parameter can be supplied to augment the value for cases like generating emails
or other strings with common suffixes.

.. code-block:: python

    >>> from model_bakery import.recipe import Recipe, seq
    >>> from shop.models import Customer

    >>> customer = Recipe(Customer, email=seq('user', suffix='@example.com'))

    >>> customer = baker.make_recipe('shop.customer')
    >>> customer.email
    'user1@example.com'

    >>> customer = baker.make_recipe('shop.customer')
    >>> customer.email
    'user2@example.com'

Sequences and iterables can be used not only for recipes, but with ``baker`` as well:

.. code-block:: python


    >>> from model_bakery import baker

    >>> customer = baker.make('Customer', name=baker.seq('Joe'))
    >>> customer.name
    'Joe1'

    >>> customers = baker.make('Customer', name=baker.seq('Chad'), _quantity=3)
    >>> for customer in customers:
    ...     print(customer.name)
    'Chad1'
    'Chad2'
    'Chad3'

You can also provide an optional ``increment_by`` argument which will modify incrementing behaviour. This can be an integer, float, Decimal or timedelta. If you want to start your increment differently, you can use the ``start`` argument, only if it's not a sequence for ``date``, ``datetime`` or ``time`` objects.

.. code-block:: python


    >>> from datetime import date, timedelta
    >>> from model_bakery.recipe import Recipe, seq
    >>> from shop.models import Customer


    >>> customer = Recipe(Customer,
        age=seq(15, increment_by=3)
        height_ft=seq(5.5, increment_by=.25)
        # assume today's date is 21/07/2014
        appointment=seq(date(2014, 7, 21), timedelta(days=1)),
        name=seq('Custom num: ', increment_by=2, start=5),
    )

    >>> customer = baker.make_recipe('shop.customer')
    >>> customer.age
    18
    >>> customer.height_ft
    5.75
    >>> customer.appointment
    datetime.date(2014, 7, 22)
    >>> customer.name
    'Custom num: 5'

    >>> new_customer = baker.make_recipe('shop.customer')
    >>> new_customer.age
    21
    >>> new_customer.height_ft
    6.0
    >>> new_customer.appointment
    datetime.date(2014, 7, 23)
    >>> customer.name
    'Custom num: 7'

Overriding recipe definitions
-----------------------------

Passing values when calling ``make_recipe`` or ``prepare_recipe`` will override the recipe rule.

.. code-block:: python

    from model_bakery import baker

    baker.make_recipe('shop.customer', name='Ada Lovelace')

This is useful when you have to create multiple objects and you have some unique field, for instance.

Recipe inheritance
------------------

If you need to reuse and override existent recipe call extend method:

.. code-block:: python

    customer = Recipe(
        Customer,
        bio='Some customer bio',
        age=30,
        enjoy_jards_macale=True,
    )
    sad_customer = customer.extend(
        enjoy_jards_macale=False,
    )
