Migrating from Model Mommy
==========================

Model Bakery has a `Python script <https://github.com/model-bakers/model_bakery/blob/master/utils/from_mommy_to_bakery.py>`_ to help you to migrate your project's test code to depend upon it instead of legacy Model Mommy. **From your project's root dir**, the following snippet can work as an example of how to migrate it:

.. code-block:: console

    $ pip uninstall model_mommy
    $ pip install model_bakery
    $ https://raw.githubusercontent.com/model-bakers/model_bakery/master/utils/from_mommy_to_bakery.py
    $ python from_mommy_to_bakery.py --dry-run  # will list the files that'll be manipulated
    $ python from_mommy_to_bakery.py            # migrate model_mommy to model_bakery
    $ python manage.py test
