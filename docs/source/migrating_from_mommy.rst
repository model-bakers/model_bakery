Migrating from Model Mommy
==========================

Model Bakery has a `Python script <https://github.com/model-bakers/model_bakery/blob/master/utils/from_mommy_to_bakery.py>`_ to help you to migrate your project's test code from Model Mommy to Model Bakery. This script will rename recipe files and replace legacy imports by the new ones.

**From your project's root dir**, execute the following commands:

.. code-block:: console

    $ pip uninstall model_mommy
    $ pip install model_bakery
    $ wget https://raw.githubusercontent.com/model-bakers/model_bakery/master/utils/from_mommy_to_bakery.py
    $ python from_mommy_to_bakery.py --dry-run  # will list the files that'll be manipulated
    $ python from_mommy_to_bakery.py            # migrate from model_mommy to model_bakery
    $ python manage.py test
