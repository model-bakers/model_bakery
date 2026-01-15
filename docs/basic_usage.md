# Basic Usage

Let's say you have an app **shop** with a model like this:

File: **models.py**

```python
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
```

To create a persisted instance, just call Model Bakery:

File: **test_models.py**

```python
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
```

Importing every model over and over again is boring. So let Model Bakery import them for you:

```python
from model_bakery import baker

# 1st form: app_label.model_name
customer = baker.make('shop.Customer')

# 2nd form: model_name
product = baker.make('Product')
```

```{note}
You can only use the 2nd form on unique model names. If you have an app shop with a Product, and an app stock with a Product, you must use the app_label.model_name form.
```

```{note}
model_name is case insensitive.
```

## Model Relationships

Model Bakery also handles relationships. Let's say the customer has a purchase history:

File: **models.py**

```python
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
```

You can use Model Bakery as:

```python
from django.test import TestCase

from model_bakery import baker

class PurchaseHistoryTestModel(TestCase):

    def setUp(self):
        self.history = baker.make('shop.PurchaseHistory')
        print(self.history.customer)
```

It will also create the Customer, automagically.

**NOTE: ForeignKeys and OneToOneFields** - Since Django 1.8, ForeignKey and OneToOne fields don't accept non persisted model instances anymore. This means that if you run:

```python
baker.prepare('shop.PurchaseHistory')
```

You'll end up with a persisted "Customer" instance.

**NOTE: GenericForeignKey** - `model-bakery` defines the content type for this relation based in how
the relation configures their [`for_concrete_model` flag](https://docs.djangoproject.com/en/5.2/ref/contrib/contenttypes/#django.contrib.contenttypes.fields.GenericForeignKey.for_concrete_model).

## M2M Relationships

By default, Model Bakery doesn't create related instances for many-to-many relationships.
If you want them to be created, you have to turn it on as the following:

```python
from django.test import TestCase

from model_bakery import baker

class PurchaseHistoryTestModel(TestCase):

    def setUp(self):
        self.history = baker.make('shop.PurchaseHistory', make_m2m=True)
        print(self.history.products.count())
```

## Explicit M2M Relationships

If you want to, you can prepare your own set of related object and pass it to Model Bakery. Here's an example:

```python
products_set = baker.prepare(Product, _quantity=5)
history = baker.make(PurchaseHistory, products=products_set)
```

## Explicit values for fields

By default, Model Bakery uses random values to populate the model's fields. But it's possible to explicitly set values for them as well.

```python
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
```

You can use callable to explicitly set values as:

```python
import random

from django.test import TestCase

from model_bakery import baker

class CustomerTestModel(TestCase):
    def get_random_name(self):
        return random.choice(["Suraj Magdum", "Avadhut More", "Rohit Chile"])

    def setUp(self):
        self.customer = baker.make(
            'shop.Customer',
            age=21,
            name = self.get_random_name
        )
```

You can also use iterable to explicitly set values as:

```python
from django.test import TestCase

from model_bakery import baker

class CustomerTestModel(TestCase):
    def setUp(self):
        names = ("Onkar Awale", "Pruthviraj Patil", "Shubham Ojha")

        self.customer = baker.make(
            'shop.Customer',
            age=21,
            name = itertools.cycle(names)
        )
```

Sometimes, you have a field with an unique value and using `make` can cause random errors. Also, passing an attribute value just to avoid uniqueness validation problems can be tedious. To solve this you can define a sequence with `seq`

```python
from django.test import TestCase

from model_bakery import baker

class CustomerTestModel(TestCase):
    def setUp(self):
        self.customer = baker.make(
            'shop.Customer',
            age=21,
            name = baker.seq('Joe')
        )
```

Related objects fields are also reachable by their name or related names in a very similar way as Django does with [field lookups](https://docs.djangoproject.com/en/dev/ref/models/querysets/#field-lookups):

```python
from django.test import TestCase

from model_bakery import baker

class PurchaseHistoryTestModel(TestCase):

    def setUp(self):
        self.bob_history = baker.make(
            'shop.PurchaseHistory',
            customer__name='Bob'
        )
```

## Creating Files

Model Bakery does not create files for FileField types. If you need to have the files created, you can pass the flag `_create_files=True` (defaults to `False`) to either `baker.make` or `baker.make_recipe`.

**Important**: the lib does not do any kind of file clean up, so it's up to you to delete the files created by it.

## Refreshing Instances After Creation

By default, Model Bakery does not refresh the instance after it is created and saved.
If you want to refresh the instance after it is created,
you can pass the flag `_refresh_after_create=True` to either `baker.make` or `baker.make_recipe`.
This ensures that any changes made by the database or signal handlers are reflected in the instance.

```python
from model_bakery import baker

# default behavior
customer = baker.make('shop.Customer', birthday='1990-01-01', _refresh_after_create=False)
assert customer.birthday == '1990-01-01'

customer = baker.make('shop.Customer', birthday='1990-01-01', _refresh_after_create=True)
assert customer.birthday == datetime.date(1990, 1, 1)
```

## Non persistent objects

If you don't need a persisted object, Model Bakery can handle this for you as well with the **prepare** method:

```python
from model_bakery import baker

customer = baker.prepare('shop.Customer')
```

It works like `make` method, but it doesn't persist the instance neither the related instances.

If you want to persist only the related instances but not your model, you can use the `_save_related` parameter for it:

```python
from model_bakery import baker

history = baker.prepare('shop.PurchaseHistory', _save_related=True)
assert history.id is None
assert bool(history.customer.id) is True
```

## More than one instance

If you need to create more than one instance of the model, you can use the `_quantity` parameter for it:

```python
from model_bakery import baker

customers = baker.make('shop.Customer', _quantity=3)
assert len(customers) == 3
```

It also works with `prepare`:

```python
from model_bakery import baker

customers = baker.prepare('shop.Customer', _quantity=3)
assert len(customers) == 3
```

The `make` method also accepts a parameter `_bulk_create` to use Django's [bulk_create](https://docs.djangoproject.com/en/3.0/ref/models/querysets/#bulk-create) method instead of calling `obj.save()` for each created instance.

```{note}
Django's `bulk_create` does not update the created object primary key as explained in their docs. Because of that, there's no way for model-bakery to avoid calling `save` method for all the foreign keys. But this behavior can depends on which Django version and database backend you're using.

So, for example, if you're trying to create 20 instances of a model with a foreign key using `_bulk_create` this will result in 21 queries (20 for each foreign key object and one to bulk create your 20 instances).
```

If you want to avoid that, you'll have to perform individual bulk creations per foreign keys as the following example:

```python
from model_bakery import baker

baker.prepare(User, _quantity=5, _bulk_create=True)
user_iter = User.objects.all().iterator()
baker.prepare(Profile, user=user_iter, _quantity=5, _bulk_create=True)
```

## Multi-database support

Model Bakery supports django application with more than one database.
If you want to determine which database bakery should use, you have the `_using` parameter:

```python
from model_bakery import baker

custom_db = "your_custom_db"
assert custom_db in settings.DATABASES
history = baker.make('shop.PurchaseHistory', _using=custom_db)
assert history in PurchaseHistory.objects.using(custom_db).all()
assert history.customer in Customer.objects.using(custom_db).all()
# default database tables with no data
assert not PurchaseHistory.objects.exists()
assert not Customer.objects.exists()
```
