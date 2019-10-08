Basic Usage
===========

Let's say you have an app **family** with a model like this:

File: model.py ::

    class Kid(models.Model):
        """
        Model class Kid of family app
        """
        happy = models.BooleanField()
        name = models.CharField(max_length=30)
        age = models.IntegerField()
        bio = models.TextField()
        wanted_games_qtd = models.BigIntegerField()
        birthday = models.DateField()
        appointment = models.DateTimeField()

To create a persisted instance, just call Mommy:

File: test_model.py ::

    # -*- coding:utf-8 -*-

    #Core Django imports
    from django.test import TestCase

    #Third-party app imports
    from model_mommy import mommy
    from model_mommy.recipe import Recipe, foreign_key

    # Relative imports of the 'app-name' package
    from .models import Kid

    class KidTestModel(TestCase):
        """
        Class to test the model
        Kid
        """

        def setUp(self):
            """
            Set up all the tests
            """
            self.kid = mommy.make(Kid)


No need to pass attributes every damn time.

Importing every model over and over again is boring. So let Mommy import them for you: ::

    from model_mommy import mommy

    # 1st form: app_label.model_name
    kid = mommy.make('family.Kid')

    # 2nd form: model_name
    dog = mommy.make('Dog')

.. note::

    You can only use the 2nd form on unique model names. If you have an app family with a Dog, and an app farm with a Dog, you must use the app_label.model_name form.

.. note::

    model_name is case insensitive.

Model Relationships
-------------------

Mommy also handles relationships. Say the kid has a dog:

File: model.py ::

    class Kid(models.Model):
        """
        Model class Kid of family app
        """
        happy = models.BooleanField()
        name = models.CharField(max_length=30)
        age = models.IntegerField()
        bio = models.TextField()
        wanted_games_qtd = models.BigIntegerField()
        birthday = models.DateField()
        appointment = models.DateTimeField()

        class Meta:
            verbose_name = _(u'Kid')
            verbose_name_plural = _(u'Kids')

        def __unicode__(self):
            """
            Return the name of kid
            """
            return u'%s' % (self.name)

    class Dog(models.Model):
        """
        Model class Dog of family app
        """
        owner = models.ForeignKey('Kid')

when you ask Mommy:

File: test_model.py ::

    # -*- coding:utf-8 -*-

    #Core Django imports
    from django.test import TestCase

    #Third-party app imports
    from model_mommy import mommy
    from model_mommy.recipe import Recipe, foreign_key

    # Relative imports of the 'app-name' package

    class DogTestModel(TestCase):
        """
        Class to test the model
        Dog
        """

        def setUp(self):
            """
            Set up all the tests
            """
            self.rex = mommy.make('family.Dog')

She will also create the Kid, automagically.
**NOTE: ForeignKeys and OneToOneFields**
Since Django 1.8, ForeignKey and OneToOne fields don't accept unpersisted model instances anymore. This means if you do:

    mommy.prepare('family.Dog')

You'll end with a persisted "Kid" instance.

M2M Relationships
-----------------

File: test_model.py ::

    # -*- coding:utf-8 -*-

    #Core Django imports
    from django.test import TestCase

    #Third-party app imports
    from model_mommy import mommy
    from model_mommy.recipe import Recipe, foreign_key

    # Relative imports of the 'app-name' package

    class DogTestModel(TestCase):
        """
        Class to test the model
        Dog
        """

        def setUp(self):
            """
            Set up all the tests
            """
            self.rex = mommy.make('family.Dog', make_m2m=True)

Explicit M2M Relationships
--------------------------
If you want to, you can prepare your own set of related object and pass it to model_mommy. Here's an example:

File: test_models.py ::
    dogs_set = mommy.prepare(models.Dog, _quantity=2)
    home = mommy.make(models.Home, owner=owner, dogs=dogs_set)


Defining some attributes
------------------------

Of course it's possible to explicitly set values for attributes.

File: test_model.py ::

    # -*- coding:utf-8 -*-

    #Core Django imports
    from django.test import TestCase

    #Third-party app imports
    from model_mommy import mommy
    from model_mommy.recipe import Recipe, foreign_key

    # Relative imports of the 'app-name' package
    from .models import Kid

    class KidTestModel(TestCase):
        """
        Class to test the model
        Kid
        """

        def setUp(self):
            """
            Set up all the tests
            """
            self.kid = mommy.make(
                Kid,
                age=3
            )

            self.another_kid = mommy.make(
                'family.Kid',
                age=6
            )

Related objects attributes are also reachable by their name or related names:

File: test_model.py ::

    # -*- coding:utf-8 -*-

    #Core Django imports
    from django.test import TestCase

    #Third-party app imports
    from model_mommy import mommy
    from model_mommy.recipe import Recipe, foreign_key

    # Relative imports of the 'app-name' package
    from .models import Dog

    class DogTestModel(TestCase):
        """
        Class to test the model
        Dog
        """

        def setUp(self):
            """
            Set up all the tests
            """

            self.bobs_dog = mommy.make(
                'family.Dog',
                owner__name='Bob'
            )

Creating Files
--------------

Mommy does not creates files for FileField types. If you need to have the files created, you can pass the flag `_create_files=True` (defaults to `False`) to either `mommy.make` or `mommy.make_recipe`.

**Important**: Mommy does not do any kind of file clean up, so it's up to you to delete the files created by it.


Non persistent objects
----------------------

If you don't need a persisted object, *Mommy* can handle this for you as well:

.. code-block:: python

    from model_mommy import mommy

    kid = mommy.prepare('family.Kid')

It works like `make`, but it doesn't persist the instance neither the related instances.

If you want to persist only the related instances but not your model, you can use the `_save_related` parameter for it:

.. code-block:: python

    from model_mommy import mommy

    dog = mommy.prepare('family.Dog', _save_related=True)
    assert dog.id is None
    assert bool(dog.owner.id) is True

More than one instance
----------------------

If you need to create more than one instance of the model, you can use the `_quantity` parameter for it:

.. code-block:: python

    from model_mommy import mommy

    kids = mommy.make('family.Kid', _quantity=3)
    assert len(kids) == 3

It also works with `prepare`:

.. code-block:: python

    from model_mommy import mommy

    kids = mommy.prepare('family.Kid', _quantity=3)
    assert len(kids) == 3
