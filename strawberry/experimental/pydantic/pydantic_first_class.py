from strawberry.annotation import StrawberryAnnotation
from strawberry.experimental.pydantic._compat import CompatModelField, get_model_fields
from strawberry.experimental.pydantic.fields import replace_types_recursively
from strawberry.experimental.pydantic.utils import get_default_factory_for_field
from strawberry.field import StrawberryField


from pydantic import BaseModel


import dataclasses
from typing import Callable, Dict, List, Optional, Sequence, Type

from strawberry.object_type import _get_interfaces
from strawberry.types.types import StrawberryObjectDefinition
from strawberry.utils.deprecations import DEPRECATION_MESSAGES, DeprecatedDescriptor
from strawberry.utils.str_converters import to_camel_case

from strawberry.experimental.pydantic.conversion_types import PydanticModel


def _get_strawberry_fields_from_basemodel(
    model: Type[BaseModel], is_input: bool, use_pydantic_alias: bool
) -> List[StrawberryField]:
    """Get all the strawberry fields off a pydantic BaseModel cls
    This function returns a list of StrawberryFields (one for each field item), while
    also paying attention the name and typing of the field.
    model:
        A pure pydantic field. Will not have a StrawberryField; one will need to
        be created in this function. Type annotation is required.
    """
    fields: list[StrawberryField] = []

    # BaseModel already has fields, so we need to get them from there
    model_fields: Dict[str, CompatModelField] = get_model_fields(model)
    for name, field in model_fields.items():
        converted_type = replace_types_recursively(field.outer_type_, is_input=is_input)
        if field.allow_none:
            converted_type = Optional[converted_type]
        graphql_before_case = (
            field.alias or field.name if use_pydantic_alias else field.name
        )
        camel_case_name = to_camel_case(graphql_before_case)
        fields.append(
            StrawberryField(
                python_name=name,
                graphql_name=camel_case_name,
                # always unset because we use default_factory instead
                default=dataclasses.MISSING,
                default_factory=get_default_factory_for_field(field),
                type_annotation=StrawberryAnnotation.from_annotation(converted_type),
                description=field.description,
                deprecation_reason=None,
                permission_classes=[],
                directives=[],
                metadata={},
            )
        )

    return fields


def first_class_process_basemodel(
    model: Type[BaseModel],
    *,
    name: Optional[str] = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
    extend: bool = False,
    use_pydantic_alias: bool = True,
):
    name = name or to_camel_case(model.__name__)

    interfaces = _get_interfaces(model)
    fields: List[StrawberryField] = _get_strawberry_fields_from_basemodel(
        model, is_input=is_input, use_pydantic_alias=use_pydantic_alias
    )
    is_type_of = getattr(model, "is_type_of", None)
    resolve_type = getattr(model, "resolve_type", None)

    model.__strawberry_definition__ = StrawberryObjectDefinition(
        name=name,
        is_input=is_input,
        is_interface=is_interface,
        interfaces=interfaces,
        description=description,
        directives=directives,
        origin=model,
        extend=extend,
        fields=fields,
        is_type_of=is_type_of,
        resolve_type=resolve_type,
    )
    # TODO: remove when deprecating _type_definition
    DeprecatedDescriptor(
        DEPRECATION_MESSAGES._TYPE_DEFINITION,
        model.__strawberry_definition__,
        "_type_definition",
    ).inject(model)

    return model


def register_first_class(
    model: Type[PydanticModel],
    *,
    name: Optional[str] = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: Optional[str] = None,
    use_pydantic_alias: bool = True,
) -> Type[PydanticModel]:
    """A function for registering a pydantic model as a first class strawberry type.
    This is useful when your pydantic model is some code that you can't edit
    (e.g. from a third party library).

    Example:
        class User(BaseModel):
            id: int
            name: str

        register_first_class(User)

        @strawberry.type
        class Query:
            @strawberry.field
            def user(self) -> User:
                return User(id=1, name="Patrick")
    """

    first_class_process_basemodel(
        model,
        name=name or to_camel_case(model.__name__),
        is_input=is_input,
        is_interface=is_interface,
        description=description,
        use_pydantic_alias=use_pydantic_alias,
    )

    if is_input:
        # TODO: Probably should check if the name clashes with an existing type?
        model._strawberry_input_type = model  # type: ignore
    else:
        model._strawberry_type = model  # type: ignore

    return model


def first_class(
    name: Optional[str] = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: Optional[str] = None,
    use_pydantic_alias: bool = True,
) -> Callable[[Type[PydanticModel]], Type[PydanticModel]]:
    """A decorator to make a pydantic class work on strawberry without creating
    a separate strawberry type.

    Example:
        @strawberry.experimental.pydantic.first_class()
        class User(BaseModel):
            id: int
            name: str

        @strawberry.type
        class Query:
            @strawberry.field
            def user(self) -> User:
                return User(id=1, name="Patrick")

    """

    def wrap(model: Type[PydanticModel]) -> Type[PydanticModel]:
        return register_first_class(
            model,
            name=name,
            is_input=is_input,
            is_interface=is_interface,
            description=description,
            use_pydantic_alias=use_pydantic_alias,
        )

    return wrap
