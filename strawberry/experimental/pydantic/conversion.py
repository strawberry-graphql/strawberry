import dataclasses
from typing import Any, Dict, Iterable, List, Type, Union, cast

import pydantic

from strawberry.enum import EnumDefinition
from strawberry.field import StrawberryField
from strawberry.type import StrawberryList, StrawberryOptional, StrawberryType
from strawberry.union import StrawberryUnion


def _convert_from_pydantic_to_strawberry_type(
    type_: Union[StrawberryType, type], data_from_model=None, extra=None
):
    data = data_from_model if data_from_model is not None else extra

    if isinstance(type_, StrawberryOptional):
        if data is None:
            return data
        return _convert_from_pydantic_to_strawberry_type(
            type_.of_type, data_from_model=data, extra=extra
        )
    if isinstance(type_, StrawberryUnion):
        for option_type in type_.types:
            if hasattr(option_type, "_pydantic_type"):
                source_type = option_type._pydantic_type  # type: ignore
            else:
                source_type = cast(type, option_type)
            if isinstance(data, source_type):
                return _convert_from_pydantic_to_strawberry_type(
                    option_type, data_from_model=data, extra=extra
                )
    if isinstance(type_, EnumDefinition):
        return data
    if isinstance(type_, StrawberryList):
        items = []
        for index, item in enumerate(data):
            items.append(
                _convert_from_pydantic_to_strawberry_type(
                    type_.of_type,
                    data_from_model=item,
                    extra=extra[index] if extra else None,
                )
            )

        return items

    if hasattr(type_, "_type_definition"):
        # in the case of an interface, the concrete type may be more specific
        # than the type in the field definition
        if hasattr(type(data), "_strawberry_type"):
            type_ = type(data)._strawberry_type
        return convert_pydantic_model_to_strawberry_class(
            type_, model_instance=data_from_model, extra=extra
        )

    return data


def convert_pydantic_model_to_strawberry_class(cls, *, model_instance=None, extra=None):
    extra = extra or {}
    kwargs = {}

    for field in cls._type_definition.fields:
        field = cast(StrawberryField, field)
        python_name = field.python_name

        data_from_extra = extra.get(python_name, None)
        data_from_model = (
            getattr(model_instance, python_name, None) if model_instance else None
        )

        # only convert and add fields to kwargs if they are present in the `__init__`
        # method of the class
        if field.init:
            kwargs[python_name] = _convert_from_pydantic_to_strawberry_type(
                field.type, data_from_model, extra=data_from_extra
            )

    return cls(**kwargs)


def _convert_pydantic_error(cls: Type, loc: Iterable, error: str) -> Any:
    first_loc, *rest = loc

    if isinstance(cls, StrawberryOptional):
        return _convert_pydantic_error(cls.of_type, loc, error)

    if isinstance(cls, StrawberryUnion):
        for option_type in cls.types:
            try:
                return _convert_pydantic_error(option_type, loc, error)
            except (ValueError, TypeError, KeyError):
                pass

    if isinstance(first_loc, str):
        args: Dict[str, Any] = {}
        fields: Dict[str, StrawberryField] = {}
        if isinstance(cls, StrawberryList):
            return _convert_pydantic_error(cls.of_type, loc, error)

        for field in cls._type_definition.fields:
            field = cast(StrawberryField, field)
            fields[field.graphql_name or field.python_name] = field
        if rest:
            args[first_loc] = _convert_pydantic_error(
                cast(Type, fields[first_loc].type), rest, error
            )
        else:
            field_name = fields[first_loc].graphql_name or fields[first_loc].python_name
            field_errors = args.get(field_name, [])
            field_errors.append(error)
            args[field_name] = field_errors
        return cls(**args)

    error_args: List[Any] = [None] * first_loc
    if rest:
        error_args.append(
            _convert_pydantic_error(
                cls.of_type,
                rest,
                error,
            )
        )
    else:
        error_args.append([error])
    return error_args


def _convert_pydantic_error_to_srawberry_type(
    strawberry_cls: Type, cls: Type, error: pydantic.ValidationError
) -> Any:
    if error.model != cls:
        raise TypeError(f"Class {strawberry_cls} received an error for model {cls}")

    args: Dict[str, Any] = {}
    fields: Dict[str, StrawberryField] = {}
    for field in strawberry_cls._type_definition.fields:
        field = cast(StrawberryField, field)
        field_name = field.graphql_name or field.python_name
        fields[field_name] = field
    for e in error.errors():
        loc = e["loc"]
        field_name = loc[0]
        field = fields[field_name]
        existing = args.get(field_name)
        if len(loc) == 1:
            new_errors = [f'{e["type"]}: {e["msg"]}']
        else:
            new_errors = _convert_pydantic_error(
                field.type, loc[1:], f'{e["type"]}: {e["msg"]}'
            )
        args[field_name] = _merge_error_args(new_errors, existing)

    final_args = {fields[k].python_name: v for k, v in args.items()}
    return strawberry_cls(**final_args)


def _merge_error_args(args1: Any, args2: Any) -> Union[Dict[str, Any], List[Any]]:
    if not args2:
        return args1
    if not args1:
        return args2

    if isinstance(args1, dict):
        new_args_dict: Dict[str, Any] = {}
        for key, value in args1.items():
            existing_value = new_args_dict.get(key, [])
            other_value = args2.get(key)
            new_args_dict[key] = _merge_error_args(
                existing_value, [*(value or []), *(other_value or [])]
            )
        return new_args_dict

    if isinstance(args1, list):
        new_args: List[Any] = []
        for args1_item, args2_item in zip(args1, args2):
            new_args.append(_merge_error_args(args1_item, args2_item))

        longer = args1 if len(args1) > len(args2) else args2
        for extra in longer[len(new_args) :]:
            new_args.append(extra)
        return new_args

    if dataclasses.is_dataclass(args1) and type(args1) == type(args2):
        return type(args1)(
            **_merge_error_args(dataclasses.asdict(args1), dataclasses.asdict(args2))
        )
    elif dataclasses.is_dataclass(args1):  # unions
        return [args1, args2]

    return [a for a in [args1, args2] if a]


def convert_pydantic_error_to_strawberry_class(
    cls: Type, error: pydantic.ValidationError
) -> Any:
    return _convert_pydantic_error_to_srawberry_type(cls, cls._pydantic_type, error)
