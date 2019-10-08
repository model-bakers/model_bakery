Known Issues
============

django-taggit
-------------

Model-mommy identifies django-taggit's `TaggableManager` as a normal Django field, which can lead to errors:

.. code-block:: pycon

    TypeError: <class 'taggit.managers.TaggableManager'> is not supported by mommy.

The fix for this is to set ``blank=True`` on your ``TaggableManager``.
