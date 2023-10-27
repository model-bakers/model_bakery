Test Runners
============

Most of the code examples shown so far have used the `Django TestCase <https://docs.djangoproject.com/en/3.1/topics/testing/tools/#testcase>`_ to explain how Model Bakery is used.

However `pytest <https://docs.pytest.org/en/stable/>`_ (with the `pytest-django <https://pytest-django.readthedocs.io/en/latest/>`_ plugin) is often preferred for it's simplicity and other benefits. See `here <https://realpython.com/django-pytest-fixtures/>`_.

The following examples show Model Bakery usage with different test runners.

Django
------
::

    # Core Django imports
    from django.test import TestCase

    # Third-party app imports
    from model_bakery import baker

    from shop.models import Customer

    class CustomerTestModel(TestCase):
        """
        Class to test the model Customer
        """

        def setUp(self):
            """Set up test class."""
            self.customer = baker.make(Customer)

        def test_using_customer(self):
            """Test function using baked model."""
            self.assertIsInstance(self.customer, Customer)

pytest
------
::

    # pytest import
    import pytest

    # Third-party app imports
    from model_bakery import baker

    from shop.models import Customer

    @pytest.fixture
    def customer():
        """Fixture for baked Customer model."""
        return baker.make(Customer)

    def test_using_customer(customer):
        """Test function using fixture of baked model."""
        assert isinstance(customer, Customer)
