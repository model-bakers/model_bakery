import collections
import copy
import itertools
from typing import (
    Any,
    Generic,
    TypeVar,
    cast,
    overload,
)

from django.db.models import Model

from . import baker
from ._types import M
from .exceptions import RecipeNotFound
from .utils import (
    get_calling_module,
    seq,  # noqa: F401 - Enable seq to be imported from recipes
)

finder = baker.ModelFinder()


class Recipe(Generic[M]):
    _T = TypeVar("_T", bound="Recipe[M]")

    def __init__(self, _model: str | type[M], **attrs: Any) -> None:
        self.attr_mapping = attrs
        self._model = _model
        # _iterator_backups will hold values of the form (backup_iterator, usable_iterator).
        self._iterator_backups = {}  # type: dict[str, Any]

    def _mapping(  # noqa: C901
        self, _using: str, new_attrs: dict[str, Any]
    ) -> dict[str, Any]:
        _save_related = new_attrs.get("_save_related", True)
        _quantity = new_attrs.get("_quantity", 1)
        rel_fields_attrs = {k: v for k, v in new_attrs.items() if "__" in k}
        new_attrs = {k: v for k, v in new_attrs.items() if "__" not in k}
        mapping = self.attr_mapping.copy()
        for k, v in self.attr_mapping.items():
            # do not generate values if field value is provided
            if k in new_attrs:
                continue
            elif isinstance(v, collections.abc.Iterator):
                if isinstance(self._model, str):
                    m = finder.get_model(self._model)
                else:
                    m = self._model
                if k not in self._iterator_backups or not m.objects.exists():
                    self._iterator_backups[k] = itertools.tee(
                        self._iterator_backups.get(k, [v])[0]
                    )
                mapping[k] = self._iterator_backups[k][1]
            elif isinstance(v, RecipeForeignKey):
                attrs = {}
                # Remove any related field attrs from the recipe attrs before filtering
                for key, _value in list(rel_fields_attrs.items()):
                    if key.startswith(f"{k}__"):
                        attrs[key] = rel_fields_attrs.pop(key)
                recipe_attrs = baker.filter_rel_attrs(k, **attrs)
                if _save_related:
                    # Create a unique foreign key for each quantity if one_to_one required
                    if v.one_to_one is True:
                        rel_gen = [
                            v.recipe.make(_using=_using, **recipe_attrs)
                            for _ in range(_quantity)
                        ]
                        mapping[k] = itertools.cycle(rel_gen)
                    # Otherwise create shared foreign key for each quantity
                    else:
                        mapping[k] = v.recipe.make(_using=_using, **recipe_attrs)
                else:
                    mapping[k] = v.recipe.prepare(_using=_using, **recipe_attrs)
            elif isinstance(v, related):
                mapping[k] = v.make
            elif isinstance(v, collections.abc.Container):
                mapping[k] = copy.deepcopy(v)

        mapping.update(new_attrs)
        mapping.update(rel_fields_attrs)
        return mapping

    @overload
    def make(
        self,
        _quantity: None = None,
        make_m2m: bool = False,
        _refresh_after_create: bool = False,
        _create_files: bool = False,
        _using: str = "",
        _bulk_create: bool = False,
        _save_kwargs: dict[str, Any] | None = None,
        **attrs: Any,
    ) -> M: ...

    @overload
    def make(
        self,
        _quantity: int,
        make_m2m: bool = False,
        _refresh_after_create: bool = False,
        _create_files: bool = False,
        _using: str = "",
        _bulk_create: bool = False,
        _save_kwargs: dict[str, Any] | None = None,
        **attrs: Any,
    ) -> list[M]: ...

    def make(
        self,
        _quantity: int | None = None,
        make_m2m: bool | None = None,
        _refresh_after_create: bool | None = None,
        _create_files: bool | None = None,
        _using: str = "",
        _bulk_create: bool | None = None,
        _save_kwargs: dict[str, Any] | None = None,
        **attrs: Any,
    ) -> M | list[M]:
        defaults = {}
        if _quantity is not None:
            defaults["_quantity"] = _quantity
        if make_m2m is not None:
            defaults["make_m2m"] = make_m2m
        if _refresh_after_create is not None:
            defaults["_refresh_after_create"] = _refresh_after_create
        if _create_files is not None:
            defaults["_create_files"] = _create_files
        if _bulk_create is not None:
            defaults["_bulk_create"] = _bulk_create
        if _save_kwargs is not None:
            defaults["_save_kwargs"] = _save_kwargs  # type: ignore[assignment]

        defaults.update(attrs)
        return baker.make(self._model, _using=_using, **self._mapping(_using, defaults))

    @overload
    def prepare(
        self,
        _quantity: None = None,
        _save_related: bool = False,
        _using: str = "",
        **attrs: Any,
    ) -> M: ...

    @overload
    def prepare(
        self,
        _quantity: int,
        _save_related: bool = False,
        _using: str = "",
        **attrs: Any,
    ) -> list[M]: ...

    def prepare(
        self,
        _quantity: int | None = None,
        _save_related: bool = False,
        _using: str = "",
        **attrs: Any,
    ) -> M | list[M]:
        defaults = {
            "_save_related": _save_related,
        }
        if _quantity is not None:
            defaults["_quantity"] = _quantity  # type: ignore[assignment]

        defaults.update(attrs)
        return baker.prepare(
            self._model, _using=_using, **self._mapping(_using, defaults)
        )

    def extend(self: _T, **attrs: Any) -> _T:
        attr_mapping = self.attr_mapping.copy()
        attr_mapping.update(attrs)
        return type(self)(self._model, **attr_mapping)


def _load_recipe_from_calling_module(recipe: str) -> Recipe[Model]:
    """Load `Recipe` from the string attribute given from the calling module.

    Args:
        recipe (str): the name of the recipe attribute within the module from
            which it should be loaded

    Returns:
        (Recipe): recipe resolved from calling module
    """
    recipe = getattr(get_calling_module(2), recipe)
    if recipe:
        return cast(Recipe[Model], recipe)
    else:
        raise RecipeNotFound


class RecipeForeignKey(Generic[M]):
    """A `Recipe` to use for making ManyToOne and OneToOne related objects."""

    def __init__(self, recipe: Recipe[M], one_to_one: bool) -> None:
        if isinstance(recipe, Recipe):
            self.recipe = recipe
            self.one_to_one = one_to_one
        else:
            raise TypeError("Not a recipe")


def foreign_key(
    recipe: Recipe[M] | str, one_to_one: bool = False
) -> RecipeForeignKey[M]:
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

    return RecipeForeignKey(cast(Recipe[M], recipe), one_to_one)


class related(Generic[M]):  # FIXME
    def __init__(self, *args: str | Recipe[M]) -> None:
        self.related = []  # type: list[Recipe[M]]
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

    def make(self) -> list[M | list[M]]:
        """Persist objects to m2m relation."""
        return [m.make() for m in self.related]
