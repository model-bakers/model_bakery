Deprecation Warnings
====================

Because of the changes of model_mommy's API, the following methods are deprecated and will be removed in one of the future releases:

After **1.5.0** release:
  * `mommy.make` and `mommy.prepare` methods renamed `model` parameter to `_model`.

After **1.4.0** release:
  * model_mommy does not create file automagically anymore. To enable it, you have to pass the parameter `_create_files` to `mommy.make` or `mommy.make_recipe` method.
  * `MOMMY_CUSTOM_FIELDS_GEN` -> should use the method `mommy.generators.add` instead

Older Warnings:
  * `mommy.make_one` -> should use the method `mommy.make` instead
  * `mommy.prepare_one` -> should use the method `mommy.prepare` instead
  * `mommy.make_many` -> should use the method `mommy.make` with the `_quantity` parameter instead
  * `mommy.make_many_from_recipe` -> should use the method `mommy.make_recipe` with the `_quantity` parameter instead
