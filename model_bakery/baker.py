from os.path import dirname, join
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    Type,
    Union,
    cast,
    overload,
)

from django.apps import apps
from django.conf import settings
from django.contrib import contenttypes
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
from django.db.models.fields.proxy import OrderWrt
from django.db.models.fields.related import (
    ReverseManyToOneDescriptor as ForeignRelatedObjectsDescriptor,
)
from django.db.models.fields.reverse_related import (
    ManyToManyRel,
    ManyToOneRel,
    OneToOneRel,
)

from . import generators, random_gen
from ._types import M, NewM
from .exceptions import (
    AmbiguousModelName,
    CustomBakerNotFound,
    InvalidCustomBaker,
    InvalidQuantityException,
    ModelNotFound,
    RecipeIteratorEmpty,
)
from .utils import seq  # NoQA: enable seq to be imported from baker
from .utils import import_from_str

recipes = None

# FIXME: use pkg_resource
mock_file_jpeg = join(dirname(__file__), "mock_img.jpeg")
mock_file_txt = join(dirname(__file__), "mock_file.txt")

MAX_MANY_QUANTITY = 5


def _valid_quantity(quantity: Optional[Union[str, int]]) -> bool:
    return quantity is not None and (not isinstance(quantity, int) or quantity < 1)


@overload
def make(
    _model: Union[str, Type[M]],
    _quantity: None = None,
    make_m2m: bool = False,
    _save_kwargs: Optional[Dict] = None,
    _refresh_after_create: bool = False,
    _create_files: bool = False,
    _using: str = "",
    _bulk_create: bool = False,
    **attrs: Any,
) -> M:
    ...


@overload
def make(
    _model: Union[str, Type[M]],
    _quantity: int,
    make_m2m: bool = False,
    _save_kwargs: Optional[Dict] = None,
    _refresh_after_create: bool = False,
    _create_files: bool = False,
    _using: str = "",
    _bulk_create: bool = False,
    _fill_optional: Union[List[str], bool] = False,
    **attrs: Any,
) -> List[M]:
    ...


def make(
    _model,
    _quantity: Optional[int] = None,
    make_m2m: bool = False,
    _save_kwargs: Optional[Dict] = None,
    _refresh_after_create: bool = False,
    _create_files: bool = False,
    _using: str = "",
    _bulk_create: bool = False,
    _fill_optional: Union[List[str], bool] = False,
    **attrs: Any,
):
    """Create a persisted instance from a given model its associated models.

    It fill the fields with random values or you can specify which
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
    _model: Union[str, Type[M]],
    _quantity: None = None,
    _save_related: bool = False,
    _using: str = "",
    **attrs,
) -> M:
    ...


@overload
def prepare(
    _model: Union[str, Type[M]],
    _quantity: int,
    _save_related: bool = False,
    _using: str = "",
    _fill_optional: Union[List[str], bool] = False,
    **attrs,
) -> List[M]:
    ...


def prepare(
    _model: Union[str, Type[M]],
    _quantity: Optional[int] = None,
    _save_related: bool = False,
    _using: str = "",
    _fill_optional: Union[List[str], bool] = False,
    **attrs,
):
    """Create but do not persist an instance from a given model.

    It fill the fields with random values or you can specify which
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
    else:
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

    _unique_models: Optional[Dict[str, Type[Model]]] = None
    _ambiguous_models: Optional[List[str]] = None

    def get_model(self, name: str) -> Type[Model]:
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
            raise ModelNotFound("Could not find model '%s'." % name.title())

        return model

    def get_model_by_name(self, name: str) -> Optional[Type[Model]]:
        """Get a model by name.

        If a model with that name exists in more than one app, raises
        AmbiguousModelName.
        """
        name = name.lower()

        if self._unique_models is None or self._ambiguous_models is None:
            self._populate()

        if name in cast(List, self._ambiguous_models):
            raise AmbiguousModelName(
                "%s is a model in more than one app. "
                'Use the form "app.model".' % name.title()
            )

        return cast(Dict, self._unique_models).get(name)

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
    if not hasattr(value, "__iter__"):
        return False

    return hasattr(value, "__next__")


def _custom_baker_class() -> Optional[Type]:
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

        for required_function_name in ["make", "prepare"]:
            if not hasattr(baker_class, required_function_name):
                raise InvalidCustomBaker(
                    'Custom Baker classes must have a "%s" function'
                    % required_function_name
                )

        return baker_class
    except ImportError:
        raise CustomBakerNotFound(
            "Could not find custom baker class '%s'" % custom_class_string
        )


class Baker(Generic[M]):
    attr_mapping: Dict[str, Any] = {}
    type_mapping: Dict = {}

    # Note: we're using one finder for all Baker instances to avoid
    # rebuilding the model cache for every make_* or prepare_* call.
    finder = ModelFinder()

    @classmethod
    def create(
        cls,
        _model: Union[str, Type[NewM]],
        make_m2m: bool = False,
        create_files: bool = False,
        _using: str = "",
    ) -> "Baker[NewM]":
        """Create the baker class defined by the `BAKER_CUSTOM_CLASS` setting."""
        baker_class = _custom_baker_class() or cls
        return cast(Type[Baker[NewM]], baker_class)(
            _model, make_m2m, create_files, _using=_using
        )

    def __init__(
        self,
        _model: Union[str, Type[M]],
        make_m2m: bool = False,
        create_files: bool = False,
        _using: str = "",
    ) -> None:
        self.make_m2m = make_m2m
        self.create_files = create_files
        self.m2m_dict: Dict[str, List] = {}
        self.iterator_attrs: Dict[str, Iterator] = {}
        self.model_attrs: Dict[str, Any] = {}
        self.rel_attrs: Dict[str, Any] = {}
        self.rel_fields: List[str] = []
        self._using = _using

        if isinstance(_model, str):
            self.model = cast(Type[M], self.finder.get_model(_model))
        else:
            self.model = cast(Type[M], _model)

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
        _save_kwargs: Optional[Dict[str, Any]] = None,
        _refresh_after_create: bool = False,
        _from_manager=None,
        _fill_optional: Union[List[str], bool] = False,
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
        _fill_optional: Union[List[str], bool] = False,
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

    def get_fields(self) -> Any:
        return set(self.model._meta.get_fields()) - set(self.get_related())

    def get_related(
        self,
    ) -> List[Union[ManyToOneRel, OneToOneRel, ManyToManyRel]]:
        return [r for r in self.model._meta.related_objects]

    def _make(
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
                (isinstance(field, OneToOneField) or isinstance(field, ForeignKey))
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
                    raise RecipeIteratorEmpty(
                        "{0} iterator is empty.".format(field.name)
                    )

        instance = self.instance(
            self.model_attrs,
            _commit=commit,
            _from_manager=_from_manager,
            _save_kwargs=_save_kwargs,
        )
        if commit:
            for related in self.get_related():
                self.create_by_related_name(instance, related)

        if _refresh_after_create:
            instance.refresh_from_db()

        return instance

    def m2m_value(self, field: ManyToManyField) -> List[Any]:
        if field.name in self.rel_fields:
            return self.generate_value(field)
        if not self.make_m2m or field.null and not field.fill_optional:
            return []
        return self.generate_value(field)

    def instance(
        self, attrs: Dict[str, Any], _commit, _save_kwargs, _from_manager
    ) -> M:
        one_to_many_keys = {}
        for k in tuple(attrs.keys()):
            field = getattr(self.model, k, None)
            if isinstance(field, ForeignRelatedObjectsDescriptor):
                one_to_many_keys[k] = attrs.pop(k)

        instance = self.model(**attrs)
        # m2m only works for persisted instances
        if _commit:
            instance.save(**_save_kwargs)
            self._handle_one_to_many(instance, one_to_many_keys)
            self._handle_m2m(instance)

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

    def _clean_attrs(self, attrs: Dict[str, Any]) -> None:
        def is_rel_field(x: str):
            return "__" in x

        self.fill_in_optional = attrs.pop("_fill_optional", False)
        # error for non existing fields
        if isinstance(self.fill_in_optional, (tuple, list, set)):
            # parents and relations
            wrong_fields = set(self.fill_in_optional) - set(
                f.name for f in self.get_fields()
            )
            if wrong_fields:
                raise AttributeError(
                    "_fill_optional field(s) %s are not related to model %s"
                    % (list(wrong_fields), self.model.__name__)
                )
        self.iterator_attrs = dict((k, v) for k, v in attrs.items() if is_iterator(v))
        self.model_attrs = dict((k, v) for k, v in attrs.items() if not is_rel_field(k))
        self.rel_attrs = dict((k, v) for k, v in attrs.items() if is_rel_field(k))
        self.rel_fields = [
            x.split("__")[0] for x in self.rel_attrs.keys() if is_rel_field(x)
        ]

    def _skip_field(self, field: Field) -> bool:
        from django.contrib.contenttypes.fields import GenericRelation

        # check for fill optional argument
        if isinstance(self.fill_in_optional, bool):
            field.fill_optional = self.fill_in_optional
        else:
            field.fill_optional = field.name in self.fill_in_optional

        if isinstance(field, FileField) and not self.create_files:
            return True

        # Don't Skip related _id fields defined in the iterator attributes
        if (
            (isinstance(field, OneToOneField) or isinstance(field, ForeignKey))
            and hasattr(field, "attname")
            and field.attname in self.iterator_attrs
        ):
            return False

        # Skip links to parent so parent is not created twice.
        if isinstance(field, OneToOneField) and self._remote_field(field).parent_link:
            return True

        if isinstance(field, (AutoField, GenericRelation, OrderWrt)):
            return True

        if all(
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

        if field.name not in self.model_attrs:
            if field.name not in self.rel_fields and (
                field.null and not field.fill_optional
            ):
                return True

        return False

    def _handle_one_to_many(self, instance: Model, attrs: Dict[str, Any]):
        for key, values in attrs.items():
            manager = getattr(instance, key)

            for value in values:
                # Django will handle any operation to persist nested non-persisted FK because
                # save doesn't do so and, thus, raises constraint errors. That's why save()
                # only gets called if the object doesn't have a pk and also doesn't hold fk
                # pointers.
                fks = any(
                    [
                        fk
                        for fk in value._meta.fields
                        if isinstance(fk, ForeignKey) or isinstance(fk, OneToOneField)
                    ]
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

    def _remote_field(
        self, field: Union[ForeignKey, OneToOneField]
    ) -> Union[OneToOneRel, ManyToOneRel]:
        return field.remote_field

    def generate_value(self, field: Field, commit: bool = True) -> Any:
        """Call the associated generator with a field passing all required args.

        Generator Resolution Precedence Order:
        -- `field.default` - model field default value, unless explicitly overwritten during baking
        -- `attr_mapping` - mapping per attribute name
        -- `choices` -- mapping from available field choices
        -- `type_mapping` - mapping from user defined type associated generators
        -- `default_mapping` - mapping from pre-defined type associated
           generators

        `attr_mapping` and `type_mapping` can be defined easily overwriting the
        model.
        """
        is_content_type_fk = isinstance(field, ForeignKey) and issubclass(
            self._remote_field(field).model, contenttypes.models.ContentType
        )
        # we only use default unless the field is overwritten in `self.rel_fields`
        if field.has_default() and field.name not in self.rel_fields:
            if callable(field.default):
                return field.default()
            return field.default
        elif field.name in self.attr_mapping:
            generator = self.attr_mapping[field.name]
        elif getattr(field, "choices"):
            generator = random_gen.gen_from_choices(field.choices)
        elif is_content_type_fk:
            generator = self.type_mapping[contenttypes.models.ContentType]
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

        if not commit:
            generator = getattr(generator, "prepare", generator)

        return generator(**generator_attrs)


def get_required_values(
    generator: Callable, field: Field
) -> Dict[str, Union[bool, int, str, List[Callable]]]:
    """Get required values for a generator from the field.

    If required value is a function, calls it with field as argument. If
    required value is a string, simply fetch the value from the field
    and return.
    """
    # FIXME: avoid abbreviations
    rt = {}  # type: Dict[str, Any]
    if hasattr(generator, "required"):
        for item in generator.required:  # type: ignore[attr-defined]

            if callable(item):  # baker can deal with the nasty hacking too!
                key, value = item(field)
                rt[key] = value

            elif isinstance(item, str):
                rt[item] = getattr(field, item)

            else:
                raise ValueError(
                    "Required value '%s' is of wrong type. \
                                  Don't make baker sad."
                    % str(item)
                )

    return rt


def filter_rel_attrs(field_name: str, **rel_attrs) -> Dict[str, Any]:
    clean_dict = {}

    for k, v in rel_attrs.items():
        if k.startswith(field_name + "__"):
            splitted_key = k.split("__")
            key = "__".join(splitted_key[1:])
            clean_dict[key] = v
        else:
            clean_dict[k] = v

    return clean_dict


def bulk_create(baker: Baker[M], quantity: int, **kwargs) -> List[M]:
    """
    Bulk create entries and all related FKs as well.

    Important: there's no way to avoid save calls since Django does
    not return the created objects after a bulk_insert call.
    """
    _save_kwargs = {}
    if baker._using:
        _save_kwargs = {"using": baker._using}

    def _save_related_objs(model, objects) -> None:
        fk_fields = [
            f
            for f in model._meta.fields
            if isinstance(f, OneToOneField) or isinstance(f, ForeignKey)
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

    entries = [
        baker.prepare(
            **kwargs,
        )
        for _ in range(quantity)
    ]
    _save_related_objs(baker.model, entries)

    if baker._using:
        # Try to use the desired DB and let Django fail if spanning
        # relationships without the proper router setup
        manager = baker.model._base_manager.using(baker._using)
    else:
        manager = baker.model._base_manager

    return manager.bulk_create(entries)
