from graphql.type.scalars import GraphQLScalarType

from .type_registry import register_type


def _process_scalar(cls, *, name, description, serialize, parse_value, parse_literal):
    if name is None:
        name = cls.__name__

    graphql_type = GraphQLScalarType(
        name=name,
        description=description,
        serialize=serialize,
        parse_value=parse_value,
        parse_literal=parse_literal,
    )

    register_type(cls, graphql_type, store_type_information=False)

    return cls


def identity(x):
    return x


def scalar(
    cls=None,
    *,
    name=None,
    description=None,
    serialize=identity,
    parse_value=None,
    parse_literal=None
):
    """Annotates a class or type as a GraphQL custom scalar.

    Example usages:

    >>> strawberry.scalar(
    >>>     datetime.date,
    >>>     serialize=lambda value: value.isoformat(),
    >>>     parse_value=datetime.parse_date
    >>> )

    >>> Base64Encoded = strawberry.scalar(
    >>>     NewType("Base64Encoded", bytes),
    >>>     serialize=base64.b64encode,
    >>>     parse_value=base64.b64decode
    >>> )

    >>> @strawberry.scalar(
    >>>     serialize=lambda value: ",".join(value.items),
    >>>     parse_value=lambda value: CustomList(value.split(","))
    >>> )
    >>> class CustomList:
    >>>     def __init__(self, items):
    >>>         self.items = items

    """

    if parse_value is None:
        parse_value = cls

    def wrap(cls):
        return _process_scalar(
            cls,
            name=name,
            description=description,
            serialize=serialize,
            parse_value=parse_value,
            parse_literal=parse_literal,
        )

    if cls is None:
        return wrap

    return wrap(cls)
