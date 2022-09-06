from __future__ import annotations

import dataclasses
import warnings
from typing import Any, Callable, Dict, List, Optional, Sequence, Type

from pydantic.fields import ModelField
from pydantic.main import BaseModel as PydanticModel

from graphql import GraphQLResolveInfo

from strawberry.auto import StrawberryAuto
from strawberry.experimental.pydantic.conversion import (
    convert_pydantic_model_to_strawberry_class,
    convert_strawberry_class_to_pydantic_model,
)
from strawberry.experimental.pydantic.exceptions import MissingFieldsListError
from strawberry.experimental.pydantic.fields import replace_types_recursively
from strawberry.experimental.pydantic.utils import (
    ensure_all_auto_fields_in_pydantic,
    get_default_factory_for_field,
)
from strawberry.field import _UNRESOLVED, StrawberryField
from strawberry.types.types import StrawberryObject, TypeDefinition


def get_type_for_field(field: ModelField, is_input: bool):
    outer_type = field.outer_type_
    replaced_type = replace_types_recursively(outer_type, is_input)

    if not field.required:
        return Optional[replaced_type]
    else:
        return replaced_type


class StrawDanticField(StrawberryField):
    origin: Type["StrawDanticObject"] = None

    def __post_init__(self):
        super().__post_init__()
        pydantic_field = self.origin._pydantic_type.__fields__.get(
            self.python_name, None
        )
        if pydantic_field:
            if self.default is not _UNRESOLVED and not self.default:
                self.default = _UNRESOLVED
            if not self.default_factory:
                self.default_factory = get_default_factory_for_field(pydantic_field)
            if not self.description:
                self.description = pydantic_field.field_info.description


class StrawDanticTypeDefinition(TypeDefinition):
    field_class = StrawDanticField

    @classmethod
    def __pre_dataclass_creation__(
        cls,
        origin: StrawDanticObject,
        strawberry_fields: Dict[str, StrawberryField],
        **kwargs,
    ) -> Dict[str, StrawberryField]:
        defined_fields = kwargs.get("fields", None)
        if defined_fields:
            warnings.warn(
                "Using all_fields overrides any explicitly defined fields "
                "in the model, using both is likely a bug",
                stacklevel=2,
            )
        all_fields = kwargs["all_fields"]
        is_input = kwargs["is_input"]
        use_pydantic_alias = kwargs["use_pydantic_alias"]
        model = kwargs["model"]
        assert issubclass(model, PydanticModel)
        model_fields = model.__fields__
        defined_fields: List[str] = list(defined_fields) if defined_fields else []
        existing_fields = getattr(origin, "__annotations__", {})
        overridden_fields: Dict[str, StrawberryField] = {}
        if defined_fields:
            warnings.warn(
                "`fields` is deprecated, use `auto` type annotations instead",
                DeprecationWarning,
            )
        # these are the fields that matched a field name in the pydantic model
        # and should copy their alias from the pydantic model
        for name, sb_field in strawberry_fields.items():
            if isinstance(sb_field.type, StrawberryAuto):
                defined_fields.append(sb_field.python_name)
            elif name in model_fields.keys():
                overridden_fields[name] = sb_field
                overridden_fields[model_fields[name].alias] = sb_field

        defined_fields.extend(
            [
                name
                for name, annot in existing_fields.items()
                if name in model_fields and isinstance(annot, StrawberryAuto)
            ]
        )

        auto_fields_set = set(defined_fields)
        if overridden_fields:
            auto_fields_set = auto_fields_set.union(set(overridden_fields.keys()))

        if all_fields:
            if auto_fields_set:
                warnings.warn(
                    "Using all_fields overrides any explicitly defined fields "
                    "in the model, using both is likely a bug",
                    stacklevel=2,
                )
            auto_fields_set = set(model_fields.keys())
        if not auto_fields_set:
            raise MissingFieldsListError(model)

        ensure_all_auto_fields_in_pydantic(
            model=model, auto_fields=auto_fields_set, cls_name=origin.__name__
        )
        # build strawberry fields.
        for field_name, field in model_fields.items():
            if field_name not in auto_fields_set:
                continue
            field_type = get_type_for_field(field, is_input)
            origin.__annotations__[field_name] = field_type
            sb_field = strawberry_fields.get(
                field_name, StrawDanticField(origin=origin, python_name=field_name)
            )
            # don't override base_resolvers.
            if sb_field.base_resolver:
                continue
            if sb_field.python_name in overridden_fields:
                origin.__annotations__[field_name] = overridden_fields[field_name].type
            sb_field = sb_field(origin)  # re-evaluate annotations.
            if field.has_alias and use_pydantic_alias and not sb_field.graphql_name:
                sb_field.graphql_name = field.alias

            strawberry_fields[sb_field.python_name] = sb_field

        if is_input:
            model._strawberry_input_type = origin  # type: ignore
        else:
            model._strawberry_type = origin  # type: ignore

        return strawberry_fields


class StrawDanticObject(StrawberryObject):
    _type_definition: StrawDanticTypeDefinition = dataclasses.field(init=False)
    _pydantic_type: Type[PydanticModel] = None

    @classmethod
    def is_type_of(cls, instance: type, _info: GraphQLResolveInfo) -> bool:
        return isinstance(instance, (StrawDanticObject, cls._pydantic_type))

    @classmethod
    def _from_class(cls, **kwargs) -> Type[StrawDanticObject]:
        model = kwargs["model"]
        assert issubclass(model, PydanticModel)
        new_class = super()._from_class(**kwargs)
        assert issubclass(new_class, StrawDanticObject)
        new_class._pydantic_type = model
        return new_class

    @classmethod
    def _fill_ns(cls, origin, kwargs, ns):
        super()._fill_ns(origin, kwargs, ns)
        model = kwargs["model"]
        ns.update({"_pydantic_type": model})

    @classmethod
    def from_pydantic(
        cls, instance: PydanticModel, extra: Dict[str, Any] = None
    ) -> StrawDanticObject:
        return convert_pydantic_model_to_strawberry_class(
            cls=cls, model_instance=instance, extra=extra
        )

    def to_pydantic(self, **kwargs) -> PydanticModel:
        instance_kwargs = {
            f.name: convert_strawberry_class_to_pydantic_model(getattr(self, f.name))
            for f in dataclasses.fields(self)
        }
        instance_kwargs.update(kwargs)
        return self._pydantic_type(**instance_kwargs)

    @classmethod
    def _create_type_definition(cls, **kwargs):
        return StrawDanticTypeDefinition.from_class(**kwargs)


def type(
    model: Type[PydanticModel],
    *,
    fields: Optional[List[str]] = None,
    name: Optional[str] = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
    all_fields: bool = False,
    use_pydantic_alias: bool = True,
) -> Callable[..., Type[StrawDanticObject]]:
    def wrap(cls: Any) -> Type[StrawDanticObject]:
        cls = StrawDanticObject._from_class(
            origin=cls,
            name=name,
            is_input=is_input,
            is_interface=is_interface,
            description=description,
            directives=directives,
            model=model,
            all_fields=all_fields,
            fields=fields,
            use_pydantic_alias=use_pydantic_alias,
        )

        return cls

    return wrap


def input(
    model: Type[PydanticModel],
    *,
    fields: Optional[List[str]] = None,
    name: Optional[str] = None,
    is_interface: bool = False,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
    all_fields: bool = False,
    use_pydantic_alias: bool = True,
) -> Callable[..., Type[StrawDanticObject]]:
    """Convenience decorator for creating an input type from a Pydantic model.
    Equal to partial(type, is_input=True)
    See https://github.com/strawberry-graphql/strawberry/issues/1830
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
    model: Type[PydanticModel],
    *,
    fields: Optional[List[str]] = None,
    name: Optional[str] = None,
    is_input: bool = False,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
    all_fields: bool = False,
    use_pydantic_alias: bool = True,
) -> Callable[..., Type[StrawDanticObject]]:
    """Convenience decorator for creating an interface type from a Pydantic model.
    Equal to partial(type, is_interface=True)
    See https://github.com/strawberry-graphql/strawberry/issues/1830
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
