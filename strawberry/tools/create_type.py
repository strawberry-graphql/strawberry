import types
from collections.abc import Sequence
from typing import Optional

import strawberry
from strawberry.types.field import StrawberryField


def create_type(
    name: str,
    fields: list[StrawberryField],
    is_input: bool = False,
    is_interface: bool = False,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
    extend: bool = False,
) -> type:
    """Create a Strawberry type from a list of StrawberryFields.

    Args:
        name: The GraphQL name of the type.
        fields: The fields of the type.
        is_input: Whether the type is an input type.
        is_interface: Whether the type is an interface.
        description: The GraphQL description of the type.
        directives: The directives to attach to the type.
        extend: Whether the type is an extension.

    Example usage:

    ```python
    import strawberry


    @strawberry.field
    def hello(info) -> str:
        return "World"


    Query = create_type(name="Query", fields=[hello])
    ```
    """
    if not fields:
        raise ValueError(f'Can\'t create type "{name}" with no fields')

    namespace = {}
    annotations = {}

    for field in fields:
        if not isinstance(field, StrawberryField):
            raise TypeError("Field is not an instance of StrawberryField")

        # Fields created using `strawberry.field` without a resolver don't have a
        # `python_name`. In that case, we fall back to the field's `graphql_name`
        # set via the `name` argument passed to `strawberry.field`.
        field_name = field.python_name or field.graphql_name

        if field_name is None:
            raise ValueError(
                "Field doesn't have a name. Fields passed to "
                "`create_type` must define a name by passing the "
                "`name` argument to `strawberry.field`."
            )

        namespace[field_name] = field
        annotations[field_name] = field.type

    namespace["__annotations__"] = annotations  # type: ignore

    cls = types.new_class(name, (), {}, lambda ns: ns.update(namespace))

    return strawberry.type(
        cls,
        is_input=is_input,
        is_interface=is_interface,
        description=description,
        directives=directives,
        extend=extend,
    )


__all__ = ["create_type"]
