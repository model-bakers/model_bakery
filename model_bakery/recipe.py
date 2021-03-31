import itertools
from typing import Any, Dict, List, Type, Union, cast

from django.db.models import Model

from . import baker
from .exceptions import RecipeNotFound
from .utils import (  # NoQA: Enable seq to be imported from recipes
    get_calling_module,
    seq,
)

finder = baker.ModelFinder()


class Recipe(object):
    def __init__(self, _model: Union[str, Type[Model]], **attrs) -> None:
        self.attr_mapping = attrs
        self._model = _model
        # _iterator_backups will hold values of the form (backup_iterator, usable_iterator).
        self._iterator_backups = {}  # type: Dict[str, Any]

    def _mapping(self, _using, new_attrs: Dict[str, Any]) -> Dict[str, Any]:
        _save_related = new_attrs.get("_save_related", True)
        _quantity = new_attrs.get("_quantity")
        if _quantity is None:
            _quantity = 1
        rel_fields_attrs = dict((k, v) for k, v in new_attrs.items() if "__" in k)
        new_attrs = dict((k, v) for k, v in new_attrs.items() if "__" not in k)
        mapping = self.attr_mapping.copy()
        for k, v in self.attr_mapping.items():
            # do not generate values if field value is provided
            if new_attrs.get(k):
                continue
            elif baker.is_iterator(v):
                if isinstance(self._model, str):
                    m = finder.get_model(self._model)
                else:
                    m = self._model
                if k not in self._iterator_backups or m.objects.count() == 0:
                    self._iterator_backups[k] = itertools.tee(
                        self._iterator_backups.get(k, [v])[0]
                    )
                mapping[k] = self._iterator_backups[k][1]
            elif isinstance(v, RecipeForeignKey):
                a = {}
                for key, value in list(rel_fields_attrs.items()):
                    if key.startswith("%s__" % k):
                        a[key] = rel_fields_attrs.pop(key)
                recipe_attrs = baker.filter_rel_attrs(k, **a)
                if _save_related:
                    # Create a unique foreign key for each quantity if one_to_one required
                    if v.one_to_one is True:
                        rel_gen = []
                        for i in range(_quantity):
                            rel_gen.append(v.recipe.make(_using=_using, **recipe_attrs))
                        mapping[k] = itertools.cycle(rel_gen)
                    # Otherwise create shared foreign key for each quantity
                    else:
                        mapping[k] = v.recipe.make(_using=_using, **recipe_attrs)
                else:
                    mapping[k] = v.recipe.prepare(_using=_using, **recipe_attrs)
            elif isinstance(v, related):
                mapping[k] = v.make()
        mapping.update(new_attrs)
        mapping.update(rel_fields_attrs)
        return mapping

    def make(self, _using="", **attrs: Any) -> Union[Model, List[Model]]:
        return baker.make(self._model, _using=_using, **self._mapping(_using, attrs))

    def prepare(self, _using="", **attrs: Any) -> Union[Model, List[Model]]:
        defaults = {"_save_related": False}
        defaults.update(attrs)
        return baker.prepare(
            self._model, _using=_using, **self._mapping(_using, defaults)
        )

    def extend(self, **attrs) -> "Recipe":
        attr_mapping = self.attr_mapping.copy()
        attr_mapping.update(attrs)
        return type(self)(self._model, **attr_mapping)


def _load_recipe_from_calling_module(recipe: str) -> Recipe:
    """Load `Recipe` from the string attribute given from the calling module.

    Args:
        recipe (str): the name of the recipe attribute within the module from
            which it should be loaded

    Returns:
        (Recipe): recipe resolved from calling module
    """
    recipe = getattr(get_calling_module(2), recipe)
    if recipe:
        return cast(Recipe, recipe)
    else:
        raise RecipeNotFound


class RecipeForeignKey(object):
    """A `Recipe` to use for making ManyToOne and OneToOne related objects."""

    def __init__(self, recipe: Recipe, one_to_one: bool) -> None:
        if isinstance(recipe, Recipe):
            self.recipe = recipe
            self.one_to_one = one_to_one
        else:
            raise TypeError("Not a recipe")


def foreign_key(
    recipe: Union[Recipe, str], one_to_one: bool = False
) -> RecipeForeignKey:
    """Return a `RecipeForeignKey`.

    Return the callable, so that the associated `_model` will not be created
    during the recipe definition.

    This resolves recipes supplied as strings from other module paths or from
    the calling code's module.
    """
    if isinstance(recipe, str):
        # Load `Recipe` from string before handing off to `RecipeForeignKey`
        try:
            # Try to load from another module
            recipe = baker._recipe(recipe)
        except (AttributeError, ImportError, ValueError):
            # Probably not in another module, so load it from calling module
            recipe = _load_recipe_from_calling_module(cast(str, recipe))

    return RecipeForeignKey(cast(Recipe, recipe), one_to_one)


class related(object):  # FIXME
    def __init__(self, *args) -> None:
        self.related = []  # type: List[Recipe]
        for recipe in args:
            if isinstance(recipe, Recipe):
                self.related.append(recipe)
            elif isinstance(recipe, str):
                recipe = _load_recipe_from_calling_module(recipe)
                if recipe:
                    self.related.append(recipe)
                else:
                    raise RecipeNotFound
            else:
                raise TypeError("Not a recipe")

    def make(self) -> List[Union[Model, List[Model]]]:
        """Persist objects to m2m relation."""
        return [m.make() for m in self.related]
