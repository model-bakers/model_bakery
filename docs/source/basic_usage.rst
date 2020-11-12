Basic Usage
===========

Let's say you have an app **shop** with a model like this:

File: **models.py** ::

    class Customer(models.Model):
        """
        Model class Customer of shop app
        """
        enjoy_jards_macale = models.BooleanField()
        name = models.CharField(max_length=30)
        email = models.EmailField()
        age = models.IntegerField()
        bio = models.TextField()
        days_since_last_login = models.BigIntegerField()
        birthday = models.DateField()
        last_shopping = models.DateTimeField()

To create a persisted instance, just call Model Bakery:

File: **test_models.py** ::

    #Core Django imports
    from django.test import TestCase

    #Third-party app imports
    from model_bakery import baker

    from shop.models import Customer

    class CustomerTestModel(TestCase):
        """
        Class to test the model Customer
        """

        def setUp(self):
            self.customer = baker.make(Customer)

Importing every model over and over again is boring. So let Model Bakery import them for you: ::

    from model_bakery import baker

    # 1st form: app_label.model_name
    customer = baker.make('shop.Customer')

    # 2nd form: model_name
    product = baker.make('Product')

.. note::

    You can only use the 2nd form on unique model names. If you have an app shop with a Product, and an app stock with a Product, you must use the app_label.model_name form.

.. note::

    model_name is case insensitive.

Model Relationships
-------------------

Model Bakery also handles relationships. Let's say the customer has a purchase history:

File: **models.py** ::

    class Customer(models.Model):
        """
        Model class Customer of shop app
        """
        enjoy_jards_macale = models.BooleanField()
        name = models.CharField(max_length=30)
        email = models.EmailField()
        age = models.IntegerField()
        bio = models.TextField()
        days_since_last_login = models.BigIntegerField()
        birthday = models.DateField()
        appointment = models.DateTimeField()

    class PurchaseHistory(models.Model):
        """
        Model class PurchaseHistory of shop app
        """
        customer = models.ForeignKey('Customer')
        products = models.ManyToManyField('Product')
        year = models.IntegerField()

You can use Model Bakery as: ::

    from django.test import TestCase

    from model_bakery import baker

    class PurchaseHistoryTestModel(TestCase):

        def setUp(self):
            self.history = baker.make('shop.PurchaseHistory')
            print(self.history.customer)

It will also create the Customer, automagically.

**NOTE: ForeignKeys and OneToOneFields** - Since Django 1.8, ForeignKey and OneToOne fields don't accept unpersisted model instances anymore. This means that if you run: ::

    baker.prepare('shop.PurchaseHistory')

You'll end up with a persisted "Customer" instance.

M2M Relationships
-----------------

By default Model Bakery doesn't create related instances for many-to-many relationships. If you want them to be created, you have to turn it on as following: ::

    from django.test import TestCase

    from model_bakery import baker

    class PurchaseHistoryTestModel(TestCase):

        def setUp(self):
            self.history = baker.make('shop.PurchaseHistory', make_m2m=True)
            print(self.history.products.count())


Explicit M2M Relationships
--------------------------
If you want to, you can prepare your own set of related object and pass it to Model Bakery. Here's an example: ::

    products_set = baker.prepare(Product, _quantity=5)
    history = baker.make(PurchaseHistory, products=products_set)


Explicit values for fields
--------------------------

By default, Model Bakery uses random values to populate the model's fields. But it's possible to explicitly set values for them as well. ::

    from django.test import TestCase

    from model_bakery import baker

    class CustomerTestModel(TestCase):

        def setUp(self):
            self.customer = baker.make(
                'shop.Customer',
                age=21
            )

            self.older_customer = baker.make(
                'shop.Customer',
                age=42
            )

Related objects fields are also reachable by their name or related names in a very similar way as Django does with `field lookups <https://docs.djangoproject.com/en/dev/ref/models/querysets/#field-lookups>`_: ::

    from django.test import TestCase

    from model_bakery import baker

    class PurchaseHistoryTestModel(TestCase):

        def setUp(self):
            self.bob_history = baker.make(
                'shop.PurchaseHistory',
                customer__name='Bob'
            )

Creating Files
--------------

Model Bakery does not create files for FileField types. If you need to have the files created, you can pass the flag ``_create_files=True`` (defaults to ``False``) to either ``baker.make`` or ``baker.make_recipe``.

**Important**: the lib does not do any kind of file clean up, so it's up to you to delete the files created by it.


Non persistent objects
----------------------

If you don't need a persisted object, Model Bakery can handle this for you as well with the **prepare** method:

.. code-block:: python

    from model_bakery import baker

    customer = baker.prepare('shop.Customer')

It works like ``make`` method, but it doesn't persist the instance neither the related instances.

If you want to persist only the related instances but not your model, you can use the ``_save_related`` parameter for it:

.. code-block:: python

    from model_bakery import baker

    history = baker.prepare('shop.PurchaseHistory', _save_related=True)
    assert history.id is None
    assert bool(history.customer.id) is True

More than one instance
----------------------

If you need to create more than one instance of the model, you can use the ``_quantity`` parameter for it:

.. code-block:: python

    from model_bakery import baker

    customers = baker.make('shop.Customer', _quantity=3)
    assert len(customers) == 3

It also works with ``prepare``:

.. code-block:: python

    from model_bakery import baker

    customers = baker.prepare('shop.Customer', _quantity=3)
    assert len(customers) == 3

Multi-database support
----------------------

Model Bakery supports django application with more than one database.
If you want to determine which database bakery should use, you have the ``_using`` parameter:


.. code-block:: python

    from model_bakery import baker

    custom_db = "your_custom_db"
    assert custom_db in settings.DATABASES
    history = baker.make('shop.PurchaseHistory', _using=custom_db)
    assert history in PurchaseHistory.objects.using(custom_db).all()
    assert history.customer in Customer.objects.using(custom_db).all()
    # default database tables with no data
    assert not PurchaseHistory.objects.exists()
    assert not Customer.objects.exists()
