import collections
from collections.abc import Iterator
from os.path import dirname, join
from typing import (
    Any,
    Callable,
    Generic,
    Optional,
    Union,
    cast,
    overload,
)

from django.apps import apps
from django.conf import settings
from django.db.models import (
    AutoField,
    BooleanField,
    Field,
    FileField,
    ForeignKey,
    ManyToManyField,
    Model,
    OneToOneField,
)
from django.db.models.fields import NOT_PROVIDED
from django.db.models.fields.proxy import OrderWrt
from django.db.models.fields.related import (
    ReverseManyToOneDescriptor as ForeignRelatedObjectsDescriptor,
)
from django.db.models.fields.reverse_related import ManyToOneRel, OneToOneRel

from . import generators, random_gen
from ._types import M, NewM
from .content_types import BAKER_CONTENTTYPES
from .exceptions import (
    AmbiguousModelName,
    CustomBakerNotFound,
    InvalidCustomBaker,
    InvalidQuantityException,
    ModelNotFound,
    RecipeIteratorEmpty,
)
from .utils import (
    import_from_str,
    seq,  # noqa: F401 - Enable seq to be imported from recipes
)

if BAKER_CONTENTTYPES:
    from django.contrib.contenttypes import models as contenttypes_models
    from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
else:
    contenttypes_models = None
    GenericRelation = None

recipes = None

# FIXME: use pkg_resource
mock_file_jpeg = join(dirname(__file__), "mock_img.jpeg")
mock_file_txt = join(dirname(__file__), "mock_file.txt")

MAX_MANY_QUANTITY = 5


def _valid_quantity(quantity: Optional[Union[str, int]]) -> bool:
    return quantity is not None and (not isinstance(quantity, int) or quantity < 1)


def _is_auto_datetime_field(field: Field) -> bool:
    return getattr(field, "auto_now_add", False) or getattr(field, "auto_now", False)


def seed(seed: Union[int, float, str, bytes, bytearray, None]) -> None:
    Baker.seed(seed)


@overload
def make(
    _model: Union[str, type[M]],
    _quantity: None = None,
    make_m2m: bool = False,
    _save_kwargs: Optional[dict[str, Any]] = None,
    _refresh_after_create: bool = False,
    _create_files: bool = False,
    _using: str = "",
    _bulk_create: bool = False,
    **attrs: Any,
) -> M: ...


@overload
def make(
    _model: Union[str, type[M]],
    _quantity: int,
    make_m2m: bool = False,
    _save_kwargs: Optional[dict[str, Any]] = None,
    _refresh_after_create: bool = False,
    _create_files: bool = False,
    _using: str = "",
    _bulk_create: bool = False,
    _fill_optional: Union[list[str], bool] = False,
    **attrs: Any,
) -> list[M]: ...


def make(
    _model,
    _quantity: Optional[int] = None,
    make_m2m: bool = False,
    _save_kwargs: Optional[dict[str, Any]] = None,
    _refresh_after_create: bool = False,
    _create_files: bool = False,
    _using: str = "",
    _bulk_create: bool = False,
    _fill_optional: Union[list[str], bool] = False,
    **attrs: Any,
):
    """Create a persisted instance from a given model its associated models.

    Baker fills the fields with random values, or you can specify which
    fields you want to define its values by yourself.
    """
    _save_kwargs = _save_kwargs or {}
    attrs.update({"_fill_optional": _fill_optional})
    baker: Baker = Baker.create(
        _model, make_m2m=make_m2m, create_files=_create_files, _using=_using
    )
    if _valid_quantity(_quantity):
        raise InvalidQuantityException

    if _quantity and _bulk_create:
        return bulk_create(baker, _quantity, _save_kwargs=_save_kwargs, **attrs)
    elif _quantity:
        return [
            baker.make(
                _save_kwargs=_save_kwargs,
                _refresh_after_create=_refresh_after_create,
                **attrs,
            )
            for _ in range(_quantity)
        ]

    return baker.make(
        _save_kwargs=_save_kwargs, _refresh_after_create=_refresh_after_create, **attrs
    )


@overload
def prepare(
    _model: Union[str, type[M]],
    _quantity: None = None,
    _save_related: bool = False,
    _using: str = "",
    **attrs: Any,
) -> M: ...


@overload
def prepare(
    _model: Union[str, type[M]],
    _quantity: int,
    _save_related: bool = False,
    _using: str = "",
    _fill_optional: Union[list[str], bool] = False,
    **attrs: Any,
) -> list[M]: ...


def prepare(
    _model: Union[str, type[M]],
    _quantity: Optional[int] = None,
    _save_related: bool = False,
    _using: str = "",
    _fill_optional: Union[list[str], bool] = False,
    **attrs: Any,
):
    """Create but do not persist an instance from a given model.

    Baker fills the fields with random values, or you can specify which
    fields you want to define its values by yourself.
    """
    attrs.update({"_fill_optional": _fill_optional})
    baker = Baker.create(_model, _using=_using)
    if _valid_quantity(_quantity):
        raise InvalidQuantityException

    if _quantity:
        return [
            baker.prepare(_save_related=_save_related, **attrs)
            for i in range(_quantity)
        ]

    return baker.prepare(_save_related=_save_related, **attrs)


def _recipe(name: str) -> Any:
    app_name, recipe_name = name.rsplit(".", 1)
    try:
        module = apps.get_app_config(app_name).module
        pkg = module.__package__ if module else app_name
    except LookupError:
        pkg = app_name
    return import_from_str(".".join((pkg, "baker_recipes", recipe_name)))


def make_recipe(baker_recipe_name, _quantity=None, _using="", **new_attrs):
    return _recipe(baker_recipe_name).make(
        _quantity=_quantity, _using=_using, **new_attrs
    )


def prepare_recipe(
    baker_recipe_name, _quantity=None, _save_related=False, _using="", **new_attrs
):
    return _recipe(baker_recipe_name).prepare(
        _quantity=_quantity, _save_related=_save_related, _using=_using, **new_attrs
    )


class ModelFinder:
    """Encapsulates all the logic for finding a model to Baker."""

    _unique_models: Optional[dict[str, type[Model]]] = None
    _ambiguous_models: Optional[list[str]] = None

    def get_model(self, name: str) -> type[Model]:
        """Get a model.

        Args:
        name (str): A name on the form 'applabel.modelname' or 'modelname'

        Returns:
            object: a model class

        """
        try:
            if "." in name:
                app_label, model_name = name.split(".")
                model = apps.get_model(app_label, model_name)
            else:
                model = self.get_model_by_name(name)
        except LookupError:
            model = None

        if not model:
            raise ModelNotFound(f"Could not find model '{name.title()}'.")

        return model

    def get_model_by_name(self, name: str) -> Optional[type[Model]]:
        """Get a model by name.

        If a model with that name exists in more than one app, raises
        AmbiguousModelName.
        """
        name = name.lower()

        if self._unique_models is None or self._ambiguous_models is None:
            self._populate()

        if name in cast(list, self._ambiguous_models):
            raise AmbiguousModelName(
                f"{name.title()} is a model in more than one app. "
                'Use the form "app.model".'
            )

        return cast(dict, self._unique_models).get(name)

    def _populate(self) -> None:
        """Cache models for faster self._get_model."""
        unique_models = {}
        ambiguous_models = []

        all_models = apps.all_models

        for app_model in all_models.values():
            for name, model in app_model.items():
                if name not in unique_models:
                    unique_models[name] = model
                else:
                    ambiguous_models.append(name)

        for name in ambiguous_models:
            unique_models.pop(name, None)

        self._ambiguous_models = ambiguous_models
        self._unique_models = unique_models


def is_iterator(value: Any) -> bool:
    return isinstance(value, collections.abc.Iterator)


def _custom_baker_class() -> Optional[type]:
    """Return the specified custom baker class.

    Returns:
        object: The custom class is specified by BAKER_CUSTOM_CLASS in Django's
        settings, or None if no custom class is defined.

    """
    custom_class_string = getattr(settings, "BAKER_CUSTOM_CLASS", None)
    if custom_class_string is None:
        return None

    try:
        baker_class = import_from_str(custom_class_string)

        for required_function_name in ("make", "prepare"):
            if not hasattr(baker_class, required_function_name):
                raise InvalidCustomBaker(
                    f'Custom Baker classes must have a "{required_function_name}" function'
                )

        return baker_class
    except ImportError:
        raise CustomBakerNotFound(
            f"Could not find custom baker class '{custom_class_string}'"
        )


class Baker(Generic[M]):
    SENTINEL = object()

    attr_mapping: dict[str, Any] = {}
    type_mapping: dict = {}

    _global_seed: Union[object, int, float, str, bytes, bytearray, None] = SENTINEL

    # Note: we're using one finder for all Baker instances to avoid
    # rebuilding the model cache for every make_* or prepare_* call.
    finder = ModelFinder()

    @classmethod
    def seed(cls, seed: Union[int, float, str, bytes, bytearray, None]) -> None:
        random_gen.baker_random.seed(seed)
        cls._global_seed = seed

    @classmethod
    def create(
        cls,
        _model: Union[str, type[NewM]],
        make_m2m: bool = False,
        create_files: bool = False,
        _using: str = "",
    ) -> "Baker[NewM]":
        """Create the baker class defined by the `BAKER_CUSTOM_CLASS` setting."""
        baker_class = _custom_baker_class() or cls
        return cast(type[Baker[NewM]], baker_class)(
            _model, make_m2m, create_files, _using=_using
        )

    def __init__(
        self,
        _model: Union[str, type[M]],
        make_m2m: bool = False,
        create_files: bool = False,
        _using: str = "",
    ) -> None:
        self.make_m2m = make_m2m
        self.create_files = create_files
        self.m2m_dict: dict[str, list] = {}
        self.iterator_attrs: dict[str, Iterator] = {}
        self.model_attrs: dict[str, Any] = {}
        self.rel_attrs: dict[str, Any] = {}
        self.rel_fields: list[str] = []
        self._using = _using

        if isinstance(_model, str):
            self.model = cast(type[M], self.finder.get_model(_model))
        else:
            self.model = cast(type[M], _model)

        self.init_type_mapping()

    def init_type_mapping(self) -> None:
        self.type_mapping = generators.get_type_mapping()
        generators_from_settings = getattr(settings, "BAKER_CUSTOM_FIELDS_GEN", {})
        for k, v in generators_from_settings.items():
            field_class = import_from_str(k)
            generator = import_from_str(v)
            self.type_mapping[field_class] = generator

    def make(
        self,
        _save_kwargs: Optional[dict[str, Any]] = None,
        _refresh_after_create: bool = False,
        _from_manager=None,
        _fill_optional: Union[list[str], bool] = False,
        **attrs: Any,
    ):
        """Create and persist an instance of the model associated with Baker instance."""
        params = {
            "commit": True,
            "commit_related": True,
            "_save_kwargs": _save_kwargs,
            "_refresh_after_create": _refresh_after_create,
            "_from_manager": _from_manager,
            "_fill_optional": _fill_optional,
        }
        params.update(attrs)
        return self._make(**params)

    def prepare(
        self,
        _save_related=False,
        _fill_optional: Union[list[str], bool] = False,
        **attrs: Any,
    ) -> M:
        """Create, but do not persist, an instance of the associated model."""
        params = {
            "commit": False,
            "commit_related": _save_related,
            "_fill_optional": _fill_optional,
        }
        params.update(attrs)
        return self._make(**params)

    def get_fields(self) -> set[Any]:
        return set(self.model._meta.get_fields()) - set(
            self.model._meta.related_objects
        )

    def _make(  # noqa: C901
        self,
        commit=True,
        commit_related=True,
        _save_kwargs=None,
        _refresh_after_create=False,
        _from_manager=None,
        **attrs: Any,
    ) -> M:
        _save_kwargs = _save_kwargs or {}
        if self._using:
            _save_kwargs["using"] = self._using

        self._clean_attrs(attrs)
        for field in self.get_fields():
            if self._skip_field(field):
                continue

            if isinstance(field, ManyToManyField):
                if field.name not in self.model_attrs:
                    self.m2m_dict[field.name] = self.m2m_value(field)
                else:
                    if field.name in self.iterator_attrs:
                        self.model_attrs[field.name] = [
                            next(self.iterator_attrs[field.name])
                        ]
                    else:
                        self.m2m_dict[field.name] = self.model_attrs.pop(field.name)
            # is an _id relation that has a sequence defined
            elif (
                isinstance(field, (OneToOneField, ForeignKey))
                and hasattr(field, "attname")
                and field.attname in self.iterator_attrs
            ):
                self.model_attrs[field.attname] = next(
                    self.iterator_attrs[field.attname]
                )
            elif field.name not in self.model_attrs:
                if (
                    not isinstance(field, ForeignKey)
                    or hasattr(field, "attname")
                    and field.attname not in self.model_attrs
                ):
                    self.model_attrs[field.name] = self.generate_value(
                        field, commit_related
                    )
            elif callable(self.model_attrs[field.name]):
                self.model_attrs[field.name] = self.model_attrs[field.name]()
            elif field.name in self.iterator_attrs:
                try:
                    self.model_attrs[field.name] = next(self.iterator_attrs[field.name])
                except StopIteration:
                    raise RecipeIteratorEmpty(f"{field.name} iterator is empty.")

        instance = self.instance(
            self.model_attrs,
            _commit=commit,
            _from_manager=_from_manager,
            _save_kwargs=_save_kwargs,
        )
        if commit:
            for related in self.model._meta.related_objects:
                self.create_by_related_name(instance, related)

        if _refresh_after_create:
            instance.refresh_from_db()

        return instance

    def m2m_value(self, field: ManyToManyField) -> list[Any]:
        if field.name in self.rel_fields:
            return self.generate_value(field)
        if not self.make_m2m or field.null and not field.fill_optional:
            return []
        return self.generate_value(field)

    def instance(
        self, attrs: dict[str, Any], _commit, _save_kwargs, _from_manager
    ) -> M:
        one_to_many_keys = {}
        auto_now_keys = {}
        generic_foreign_keys = {}

        for k in tuple(attrs.keys()):
            field = getattr(self.model, k, None)

            if not field:
                continue

            if isinstance(field, ForeignRelatedObjectsDescriptor):
                one_to_many_keys[k] = attrs.pop(k)

            if hasattr(field, "field") and _is_auto_datetime_field(field.field):
                auto_now_keys[k] = attrs[k]

            if BAKER_CONTENTTYPES and isinstance(field, GenericForeignKey):
                generic_foreign_keys[k] = {
                    "value": attrs.pop(k),
                    "content_type_field": field.ct_field,
                    "object_id_field": field.fk_field,
                }

        instance = self.model(**attrs)

        self._handle_generic_foreign_keys(instance, generic_foreign_keys)

        if _commit:
            instance.save(**_save_kwargs)
            self._handle_one_to_many(instance, one_to_many_keys)
            self._handle_m2m(instance)
            self._handle_auto_now(instance, auto_now_keys)

            if _from_manager:
                # Fetch the instance using the given Manager, e.g.
                # 'objects'. This will ensure any additional code
                # within its get_queryset() method (e.g. annotations)
                # is run.
                manager = getattr(self.model, _from_manager)
                instance = cast(M, manager.get(pk=instance.pk))

        return instance

    def create_by_related_name(
        self, instance: Model, related: Union[ManyToOneRel, OneToOneRel]
    ) -> None:
        rel_name = related.get_accessor_name()
        if not rel_name or rel_name not in self.rel_fields:
            return

        kwargs = filter_rel_attrs(rel_name, **self.rel_attrs)
        kwargs[related.field.name] = instance

        make(related.field.model, **kwargs)

    def _clean_attrs(self, attrs: dict[str, Any]) -> None:
        def is_rel_field(x: str):
            return "__" in x

        self.fill_in_optional = attrs.pop("_fill_optional", False)
        # error for non existing fields
        if isinstance(self.fill_in_optional, (tuple, list, set)):
            # parents and relations
            wrong_fields = set(self.fill_in_optional) - {
                f.name for f in self.get_fields()
            }
            if wrong_fields:
                raise AttributeError(
                    f"_fill_optional field(s) {list(wrong_fields)} are not "
                    f"related to model {self.model.__name__}"
                )

        self.iterator_attrs = {
            k: v for k, v in attrs.items() if isinstance(v, collections.abc.Iterator)
        }
        self.model_attrs = {k: v for k, v in attrs.items() if not is_rel_field(k)}
        self.rel_attrs = {k: v for k, v in attrs.items() if is_rel_field(k)}
        self.rel_fields = [x.split("__")[0] for x in self.rel_attrs if is_rel_field(x)]

    def _skip_field(self, field: Field) -> bool:  # noqa: C901
        # check for fill optional argument
        if isinstance(self.fill_in_optional, bool):
            field.fill_optional = self.fill_in_optional
        else:
            field.fill_optional = field.name in self.fill_in_optional

        if isinstance(field, FileField) and not self.create_files:
            return True

        # Don't Skip related _id fields defined in the iterator attributes
        if (
            isinstance(field, (OneToOneField, ForeignKey))
            and hasattr(field, "attname")
            and field.attname in self.iterator_attrs
        ):
            return False

        # Skip links to parent so parent is not created twice.
        if isinstance(field, OneToOneField) and self._remote_field(field).parent_link:
            return True

        other_fields_to_skip = [
            AutoField,
            OrderWrt,
        ]

        if BAKER_CONTENTTYPES:
            other_fields_to_skip.extend([GenericRelation, GenericForeignKey])

        if isinstance(field, tuple(other_fields_to_skip)):
            return True

        if all(  # noqa: SIM102
            [
                field.name not in self.model_attrs,
                field.name not in self.rel_fields,
                field.name not in self.attr_mapping,
            ]
        ):
            # Django is quirky in that BooleanFields are always "blank",
            # but have no default.
            if not field.fill_optional and (
                not issubclass(field.__class__, Field)
                or field.has_default()
                or (field.blank and not isinstance(field, BooleanField))
            ):
                return True

        if field.name not in self.model_attrs:  # noqa: SIM102
            if field.name not in self.rel_fields and (
                not field.fill_optional and field.null
            ):
                return True

        return False

    def _handle_auto_now(self, instance: Model, attrs: dict[str, Any]):
        if not attrs:
            return

        # use .update() to force update auto_now fields
        instance.__class__.objects.filter(pk=instance.pk).update(**attrs)

        # to make the resulting instance has the specified values
        for k, v in attrs.items():
            setattr(instance, k, v)

    def _handle_one_to_many(self, instance: Model, attrs: dict[str, Any]):
        for key, values in attrs.items():
            manager = getattr(instance, key)

            if callable(values):
                values = values()

            for value in values:
                # Django will handle any operation to persist nested non-persisted FK because
                # save doesn't do so and, thus, raises constraint errors. That's why save()
                # only gets called if the object doesn't have a pk and also doesn't hold fk
                # pointers.
                fks = any(
                    fk
                    for fk in value._meta.fields
                    if isinstance(fk, (ForeignKey, OneToOneField))
                )
                if not value.pk and not fks:
                    value.save()

            try:
                manager.set(values, bulk=False, clear=True)
            except TypeError:
                # for many-to-many relationships the bulk keyword argument doesn't exist
                manager.set(values, clear=True)

    def _handle_m2m(self, instance: Model):
        for key, values in self.m2m_dict.items():
            if callable(values):
                values = values()

            for value in values:
                if not value.pk:
                    value.save()
            m2m_relation = getattr(instance, key)
            through_model = m2m_relation.through

            # using related manager to fire m2m_changed signal
            if through_model._meta.auto_created:
                m2m_relation.add(*values)
            else:
                for value in values:
                    base_kwargs = {
                        m2m_relation.source_field_name: instance,
                        m2m_relation.target_field_name: value,
                    }
                    make(through_model, _using=self._using, **base_kwargs)

    def _handle_generic_foreign_keys(self, instance: Model, attrs: dict[str, Any]):
        """Set content type and object id for GenericForeignKey fields."""
        for field_name, data in attrs.items():
            ct_field_name = data["content_type_field"]
            oid_field_name = data["object_id_field"]
            value = data["value"]
            if callable(value):
                value = value()
            if is_iterator(value):
                value = next(value)
            if value is None:
                # when GFK is None, we should try to set the content type and object id to None
                content_type_field = instance._meta.get_field(ct_field_name)
                object_id_field = instance._meta.get_field(oid_field_name)
                if content_type_field.null:
                    setattr(instance, ct_field_name, None)
                if object_id_field.null:
                    setattr(instance, oid_field_name, None)
            else:
                setattr(instance, field_name, value)
                setattr(
                    instance,
                    ct_field_name,
                    contenttypes_models.ContentType.objects.get_for_model(
                        value, for_concrete_model=False
                    ),
                )
                setattr(instance, oid_field_name, value.pk)

    def _remote_field(
        self, field: Union[ForeignKey, OneToOneField]
    ) -> Union[OneToOneRel, ManyToOneRel]:
        return field.remote_field

    def generate_value(self, field: Field, commit: bool = True) -> Any:  # noqa: C901
        """Call the associated generator with a field passing all required args.

        Generator Resolution Precedence Order:
        -- `field.default` - model field default value, unless explicitly overwritten during baking
        -- `field.db_default` - model field db default value, unless explicitly overwritten
        -- `attr_mapping` - mapping per attribute name
        -- `choices` -- mapping from available field choices
        -- `type_mapping` - mapping from user defined type associated generators
        -- `default_mapping` - mapping from pre-defined type associated
           generators

        `attr_mapping` and `type_mapping` can be defined easily overwriting the
        model.
        """
        is_content_type_fk = False
        is_generic_fk = False
        if BAKER_CONTENTTYPES:
            is_content_type_fk = isinstance(field, ForeignKey) and issubclass(
                self._remote_field(field).model, contenttypes_models.ContentType
            )
            is_generic_fk = isinstance(field, GenericForeignKey)
        if is_generic_fk:
            generator = self.type_mapping[GenericForeignKey]
        # we only use default unless the field is overwritten in `self.rel_fields`
        elif field.has_default() and field.name not in self.rel_fields:
            if callable(field.default):
                return field.default()
            return field.default
        elif getattr(field, "db_default", NOT_PROVIDED) != NOT_PROVIDED:
            return field.db_default
        elif field.name in self.attr_mapping:
            generator = self.attr_mapping[field.name]
        elif field.choices:
            generator = random_gen.gen_from_choices(field.choices)
        elif is_content_type_fk:
            generator = self.type_mapping[contenttypes_models.ContentType]
        elif generators.get(field.__class__):
            generator = generators.get(field.__class__)
        elif field.__class__ in self.type_mapping:
            generator = self.type_mapping[field.__class__]
        else:
            raise TypeError(
                f"field {field.name} type {field.__class__} is not supported by baker."
            )

        # attributes like max_length, decimal_places are taken into account when
        # generating the value.
        field._using = self._using
        generator_attrs = get_required_values(generator, field)

        if field.name in self.rel_fields:
            generator_attrs.update(filter_rel_attrs(field.name, **self.rel_attrs))

        if (
            field.__class__ in (ForeignKey, OneToOneField, ManyToManyField)
            and not is_content_type_fk
        ):
            # create files also on related models if required
            generator_attrs["_create_files"] = self.create_files

        if not commit:
            generator = getattr(generator, "prepare", generator)

        return generator(**generator_attrs)


def get_required_values(
    generator: Callable, field: Field
) -> dict[str, Union[bool, int, str, list[Callable]]]:
    """Get required values for a generator from the field.

    If required value is a function, calls it with field as argument. If
    required value is a string, simply fetch the value from the field
    and return.
    """
    required_values = {}  # type: dict[str, Any]
    if hasattr(generator, "required"):
        for item in generator.required:  # type: ignore[attr-defined]
            if callable(item):  # baker can deal with the nasty hacking too!
                key, value = item(field)
                required_values[key] = value

            elif isinstance(item, str):
                required_values[item] = getattr(field, item)

            else:
                raise ValueError(
                    f"Required value '{item}' is of wrong type. Don't make baker sad."
                )

    return required_values


def filter_rel_attrs(field_name: str, **rel_attrs) -> dict[str, Any]:
    clean_dict = {}

    for k, v in rel_attrs.items():
        if k.startswith(f"{field_name}__"):
            splitted_key = k.split("__")
            key = "__".join(splitted_key[1:])
            clean_dict[key] = v
        else:
            clean_dict[k] = v

    return clean_dict


def _save_related_objs(model, objects, _using=None) -> None:
    """Recursively save all related foreign keys for each entry."""
    _save_kwargs = {"using": _using} if _using else {}

    fk_fields = [
        f for f in model._meta.fields if isinstance(f, (OneToOneField, ForeignKey))
    ]

    for fk in fk_fields:
        fk_objects = []
        for obj in objects:
            fk_obj = getattr(obj, fk.name, None)
            if fk_obj and not fk_obj.pk:
                fk_objects.append(fk_obj)

        if fk_objects:
            _save_related_objs(fk.related_model, fk_objects)
            for i, fk_obj in enumerate(fk_objects):
                fk_obj.save(**_save_kwargs)
                setattr(objects[i], fk.name, fk_obj)


def bulk_create(baker: Baker[M], quantity: int, **kwargs) -> list[M]:
    """
    Bulk create entries and all related FKs as well.

    Important: there's no way to avoid save calls since Django does
    not return the created objects after a bulk_insert call.
    """
    # Create a list of entries by calling the prepare method of the Baker instance
    # quantity number of times, passing in the additional keyword arguments
    entries = [
        baker.prepare(
            **kwargs,
        )
        for _ in range(quantity)
    ]

    _save_related_objs(baker.model, entries, _using=baker._using)

    # Use the desired database to create the entries
    if baker._using:
        manager = baker.model._base_manager.using(baker._using)
    else:
        manager = baker.model._base_manager

    created_entries = manager.bulk_create(entries)

    # set many-to-many relations from kwargs
    for entry in created_entries:
        for field in baker.model._meta.many_to_many:
            if field.name in kwargs:
                through_model = getattr(entry, field.name).through
                through_model.objects.bulk_create(
                    [
                        through_model(
                            **{
                                field.remote_field.name: entry,
                                field.related_model._meta.model_name: obj,
                            }
                        )
                        for obj in kwargs[field.name]
                    ]
                )

        # set many-to-many relations that are specified using related name from kwargs
        for field in baker.model._meta.get_fields():
            if field.many_to_many and hasattr(field, "related_model"):
                reverse_relation_name = (
                    field.related_query_name
                    or field.related_name
                    or f"{field.related_model._meta.model_name}_set"
                )
                if reverse_relation_name in kwargs:
                    getattr(entry, reverse_relation_name).set(
                        kwargs[reverse_relation_name]
                    )

    return created_entries
