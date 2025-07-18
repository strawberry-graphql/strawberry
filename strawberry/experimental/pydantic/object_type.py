from __future__ import annotations

import builtins
import dataclasses
import sys
import warnings
from collections.abc import Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Optional,
    cast,
)

from graphql import GraphQLResolveInfo

from strawberry.annotation import StrawberryAnnotation
from strawberry.experimental.pydantic._compat import (
    CompatModelField,
    PydanticCompat,
)
from strawberry.experimental.pydantic.conversion import (
    convert_pydantic_model_to_strawberry_class,
    convert_strawberry_class_to_pydantic_model,
)
from strawberry.experimental.pydantic.conversion_types import (
    PydanticModel,
    StrawberryTypeFromPydantic,
)
from strawberry.experimental.pydantic.exceptions import MissingFieldsListError
from strawberry.experimental.pydantic.fields import replace_types_recursively
from strawberry.experimental.pydantic.utils import (
    DataclassCreationFields,
    ensure_all_auto_fields_in_pydantic,
    get_default_factory_for_field,
    get_private_fields,
)
from strawberry.types.auto import StrawberryAuto
from strawberry.types.cast import get_strawberry_type_cast
from strawberry.types.field import StrawberryField
from strawberry.types.object_type import _process_type, _wrap_dataclass
from strawberry.types.type_resolver import _get_fields

if TYPE_CHECKING:
    import builtins
    from collections.abc import Sequence

    from graphql import GraphQLResolveInfo


def get_type_for_field(field: CompatModelField, is_input: bool, compat: PydanticCompat):  # noqa: ANN201
    outer_type = field.outer_type_

    replaced_type = replace_types_recursively(outer_type, is_input, compat=compat)

    if field.is_v1:
        # only pydantic v1 has this Optional logic
        should_add_optional: bool = field.allow_none
        if should_add_optional:
            return Optional[replaced_type]

    return replaced_type


def _build_dataclass_creation_fields(
    field: CompatModelField,
    is_input: bool,
    existing_fields: dict[str, StrawberryField],
    auto_fields_set: set[str],
    use_pydantic_alias: bool,
    compat: PydanticCompat,
) -> DataclassCreationFields:
    field_type = (
        get_type_for_field(field, is_input, compat=compat)
        if field.name in auto_fields_set
        else existing_fields[field.name].type
    )

    if (
        field.name in existing_fields
        and existing_fields[field.name].base_resolver is not None
    ):
        # if the user has defined a resolver for this field, always use it
        strawberry_field = existing_fields[field.name]
    else:
        # otherwise we build an appropriate strawberry field that resolves it
        existing_field = existing_fields.get(field.name)
        graphql_name = None
        if existing_field and existing_field.graphql_name:
            graphql_name = existing_field.graphql_name
        elif field.has_alias and use_pydantic_alias:
            graphql_name = field.alias

        strawberry_field = StrawberryField(
            python_name=field.name,
            graphql_name=graphql_name,
            # always unset because we use default_factory instead
            default=dataclasses.MISSING,
            default_factory=get_default_factory_for_field(field, compat=compat),
            type_annotation=StrawberryAnnotation.from_annotation(field_type),
            description=field.description,
            deprecation_reason=(
                existing_field.deprecation_reason if existing_field else None
            ),
            permission_classes=(
                existing_field.permission_classes if existing_field else []
            ),
            directives=existing_field.directives if existing_field else (),
            metadata=existing_field.metadata if existing_field else {},
        )

    return DataclassCreationFields(
        name=field.name,
        field_type=field_type,  # type: ignore
        field=strawberry_field,
    )


if TYPE_CHECKING:
    from strawberry.experimental.pydantic.conversion_types import (
        PydanticModel,
        StrawberryTypeFromPydantic,
    )


def type(
    model: builtins.type[PydanticModel],
    *,
    fields: Optional[list[str]] = None,
    name: Optional[str] = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
    all_fields: bool = False,
    include_computed: bool = False,
    use_pydantic_alias: bool = True,
) -> Callable[..., builtins.type[StrawberryTypeFromPydantic[PydanticModel]]]:
    def wrap(cls: Any) -> builtins.type[StrawberryTypeFromPydantic[PydanticModel]]:
        compat = PydanticCompat.from_model(model)
        model_fields = compat.get_model_fields(model, include_computed=include_computed)

        # OPTIMIZED: Do not recreate sets repeatedly; compute only once.
        existing_fields = getattr(cls, "__annotations__", {})
        existing_field_names = set(existing_fields.keys())

        if fields:
            warnings.warn(
                "`fields` is deprecated, use `auto` type annotations instead",
                DeprecationWarning,
                stacklevel=2,
            )
            original_fields_set = set(fields)
        else:
            original_fields_set = set()

        model_field_keys = set(model_fields.keys())

        # Determine fields_set and auto_fields_set efficiently:
        # OPTIMIZED: Only a single pass over items and avoids building sets via union needlessly.
        # Use set comprehension for performance.

        # these are the fields that matched a field name in the pydantic model
        # and should copy their alias from the pydantic model
        fields_set = original_fields_set.copy()
        fields_set.update(
            existing_field_names & model_field_keys
        )  # Only names present in model_fields

        # these are the fields that were marked with strawberry.auto and
        # should copy their type from the pydantic model
        # OPTIMIZED: process only those with StrawberryAuto
        auto_fields_set = original_fields_set.copy()
        auto_fields_set.update(
            {
                name
                for name, type_ in existing_fields.items()
                if isinstance(type_, StrawberryAuto)
            }
        )

        if all_fields:
            if fields_set:
                warnings.warn(
                    "Using all_fields overrides any explicitly defined fields "
                    "in the model, using both is likely a bug",
                    stacklevel=2,
                )
            fields_set = model_field_keys
            auto_fields_set = model_field_keys

        if not fields_set:
            raise MissingFieldsListError(cls)

        ensure_all_auto_fields_in_pydantic(
            model=model,
            auto_fields=auto_fields_set,
            cls_name=cls.__name__,
            include_computed=include_computed,
        )

        wrapped = _wrap_dataclass(cls)

        # OPTIMIZED: no need to cast result repeatedly nor to build the field->field dict repeatedly
        extra_strawberry_fields = _get_fields(wrapped, {})
        extra_fields = cast("list[dataclasses.Field]", extra_strawberry_fields)
        extra_field_names = set(f.name for f in extra_fields)
        private_fields = get_private_fields(wrapped)

        # OPTIMIZED: Build dict only once, directly
        extra_fields_dict = {field.name: field for field in extra_fields}

        # Only keep relevant fields for model_fields once before expensive comprehensions
        selected_model_fields = [
            (fname, model_fields[fname])
            for fname in fields_set
            if fname in model_fields
        ]

        # OPTIMIZED: Loop-based appends to lists to avoid creating temp lists and to preserve order
        all_model_fields: list[DataclassCreationFields] = []

        for field in extra_fields:
            if field.name not in fields_set:
                all_model_fields.append(
                    DataclassCreationFields(
                        name=field.name,
                        field_type=field.type,  # type: ignore
                        field=field,
                    )
                )
        for field in private_fields:
            if field.name not in fields_set:
                all_model_fields.append(
                    DataclassCreationFields(
                        name=field.name,
                        field_type=field.type,  # type: ignore
                        field=field,
                    )
                )
        for field_name, field in selected_model_fields:
            all_model_fields.append(
                _build_dataclass_creation_fields(
                    field,
                    is_input,
                    extra_fields_dict,
                    auto_fields_set,
                    use_pydantic_alias,
                    compat=compat,
                )
            )

        # Implicitly define `is_type_of` to support interfaces/unions that use
        # pydantic objects (not the corresponding strawberry type)
        @classmethod  # type: ignore
        def is_type_of(cls: builtins.type, obj: Any, _info: GraphQLResolveInfo) -> bool:
            if (type_cast := get_strawberry_type_cast(obj)) is not None:
                return type_cast is cls
            return isinstance(obj, (cls, model))

        namespace = {"is_type_of": is_type_of}

        # OPTIMIZED: Do attribute/qualname checks only once!
        has_custom_from_pydantic = False
        from_pydantic_fn = getattr(cls, "from_pydantic", None)
        if from_pydantic_fn is not None:
            if getattr(from_pydantic_fn, "__qualname__", "").endswith(
                f"{cls.__name__}.from_pydantic"
            ):
                has_custom_from_pydantic = True

        has_custom_to_pydantic = False
        to_pydantic_fn = getattr(cls, "to_pydantic", None)
        if to_pydantic_fn is not None:
            if getattr(to_pydantic_fn, "__qualname__", "").endswith(
                f"{cls.__name__}.to_pydantic"
            ):
                has_custom_to_pydantic = True

        if has_custom_from_pydantic:
            namespace["from_pydantic"] = cls.from_pydantic
        if has_custom_to_pydantic:
            namespace["to_pydantic"] = cls.to_pydantic

        if hasattr(cls, "resolve_reference"):
            namespace["resolve_reference"] = cls.resolve_reference

        kwargs: dict[str, object] = {}

        # Python 3.10.1 introduces the kw_only param to `make_dataclass`.
        # If we're on an older version then generate our own custom init function
        if sys.version_info >= (3, 10, 1):
            kwargs["kw_only"] = dataclasses.MISSING
        else:
            kwargs["init"] = False

        # OPTIMIZED: field.to_tuple() in a single pass.
        fields_tuple_seq = [field.to_tuple() for field in all_model_fields]

        cls = dataclasses.make_dataclass(
            cls.__name__,
            fields_tuple_seq,
            bases=cls.__bases__,
            namespace=namespace,
            **kwargs,  # type: ignore
        )

        if sys.version_info < (3, 10, 1):
            from strawberry.utils.dataclasses import add_custom_init_fn

            add_custom_init_fn(cls)

        _process_type(
            cls,
            name=name,
            is_input=is_input,
            is_interface=is_interface,
            description=description,
            directives=directives,
        )

        if is_input:
            model._strawberry_input_type = cls  # type: ignore
        else:
            model._strawberry_type = cls  # type: ignore
        cls._pydantic_type = model

        # OPTIMIZED: Use locals explicitly, avoid repeated instance lookups.
        def from_pydantic_default(
            instance: PydanticModel, extra: Optional[dict[str, Any]] = None
        ) -> StrawberryTypeFromPydantic[PydanticModel]:
            ret = convert_pydantic_model_to_strawberry_class(
                cls=cls, model_instance=instance, extra=extra
            )
            ret._original_model = instance
            return ret

        def to_pydantic_default(self: Any, **kwargs: Any) -> PydanticModel:
            # OPTIMIZED: Use generator expression for lower memory overhead.
            instance_kwargs = {
                f.name: convert_strawberry_class_to_pydantic_model(
                    getattr(self, f.name)
                )
                for f in dataclasses.fields(self)
            }
            instance_kwargs.update(kwargs)
            return model(**instance_kwargs)

        if not has_custom_from_pydantic:
            cls.from_pydantic = staticmethod(from_pydantic_default)
        if not has_custom_to_pydantic:
            cls.to_pydantic = to_pydantic_default

        return cls

    return wrap


def input(
    model: builtins.type[PydanticModel],
    *,
    fields: Optional[list[str]] = None,
    name: Optional[str] = None,
    is_interface: bool = False,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
    all_fields: bool = False,
    use_pydantic_alias: bool = True,
) -> Callable[..., builtins.type[StrawberryTypeFromPydantic[PydanticModel]]]:
    """Convenience decorator for creating an input type from a Pydantic model.

    Equal to `partial(type, is_input=True)`

    See https://github.com/strawberry-graphql/strawberry/issues/1830.
    """
    return type(
        model=model,
        fields=fields,
        name=name,
        is_input=True,
        is_interface=is_interface,
        description=description,
        directives=directives,
        all_fields=all_fields,
        use_pydantic_alias=use_pydantic_alias,
    )


def interface(
    model: builtins.type[PydanticModel],
    *,
    fields: Optional[list[str]] = None,
    name: Optional[str] = None,
    is_input: bool = False,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
    all_fields: bool = False,
    use_pydantic_alias: bool = True,
) -> Callable[..., builtins.type[StrawberryTypeFromPydantic[PydanticModel]]]:
    """Convenience decorator for creating an interface type from a Pydantic model.

    Equal to `partial(type, is_interface=True)`

    See https://github.com/strawberry-graphql/strawberry/issues/1830.
    """
    return type(
        model=model,
        fields=fields,
        name=name,
        is_input=is_input,
        is_interface=True,
        description=description,
        directives=directives,
        all_fields=all_fields,
        use_pydantic_alias=use_pydantic_alias,
    )
