import builtins
import dataclasses
from typing import Dict, Iterable, Tuple, Type, Union, cast

from strawberry.union import StrawberryUnion, union
from strawberry.utils.str_converters import capitalize_first
from strawberry.utils.typing import is_type_var, is_union

from .types import FederationFieldParams, FieldDefinition, TypeDefinition


def get_name_from_types(types: Iterable[Union[Type, StrawberryUnion]]):
    names = []

    for type_ in types:
        if isinstance(type_, StrawberryUnion):
            return type_.name
        elif hasattr(type_, "_type_definition"):
            name = capitalize_first(type_._type_definition.name)
        else:
            name = capitalize_first(type_.__name__)

        names.append(name)

    return "".join(names)


def copy_union_with(
    types: Tuple[Type, ...],
    params_to_type: Dict[Type, Union[Type, StrawberryUnion]] = None,
    description=None,
) -> StrawberryUnion:
    types = cast(
        Tuple[Type, ...],
        tuple(copy_type_with(t, params_to_type=params_to_type) for t in types),
    )

    return union(
        name=get_name_from_types(types),
        types=types,
        description=description,
    )


def copy_type_with(
    base: Type,
    *types: Type,
    params_to_type: Dict[Type, Union[Type, StrawberryUnion]] = None
) -> Type:
    if params_to_type is None:
        params_to_type = {}

    if isinstance(base, StrawberryUnion):
        return copy_union_with(
            base.types, params_to_type=params_to_type, description=base.description
        )

    if hasattr(base, "_type_definition"):
        definition = cast(TypeDefinition, base._type_definition)

        if definition.type_params:
            fields = []

            type_params = definition.type_params.values()

            for param, type_ in zip(type_params, types):
                if is_union(type_):
                    params_to_type[param] = copy_union_with(
                        type_.__args__, params_to_type=params_to_type
                    )
                else:
                    params_to_type[param] = type_

            name = get_name_from_types(params_to_type.values()) + definition.name

            for field in definition.fields:
                kwargs = dataclasses.asdict(field)

                if field.is_list:
                    child = cast(FieldDefinition, field.child)
                    child_type = cast(Type, child.type)

                    # TODO: nested list

                    kwargs["child"] = FieldDefinition(
                        name=child.name,
                        origin=child.origin,
                        origin_name=child.origin_name,
                        is_optional=child.is_optional,
                        type=copy_type_with(child_type, params_to_type=params_to_type),
                    )

                else:
                    field_type = cast(Type, field.type)

                    kwargs["type"] = copy_type_with(
                        field_type, params_to_type=params_to_type
                    )

                federation_args = kwargs.pop("federation")
                kwargs["federation"] = FederationFieldParams(**federation_args)

                fields.append(FieldDefinition(**kwargs))

            type_definition = TypeDefinition(
                name=name,
                is_input=definition.is_input,
                origin=definition.origin,
                is_interface=definition.is_interface,
                is_generic=False,
                federation=definition.federation,
                interfaces=definition.interfaces,
                description=definition.description,
                _fields=fields,
            )
            type_definition._type_params = {}

            copied_type = builtins.type(
                name,
                (),
                {"_type_definition": type_definition},
            )

            if not hasattr(base, "_copies"):
                base._copies = {}

            base._copies[types] = copied_type

            return copied_type

    if is_type_var(base):
        # TODO: we ignore the type issue here as we'll improve how types
        # are represented internally (using StrawberryTypes) so we can improve
        # typings later
        return params_to_type[base]  # type: ignore

    return base
