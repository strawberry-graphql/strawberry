from graphql.type.scalars import GraphQLScalarType

from .type_converter import REGISTRY


def _process_scalar(cls, *, description, serialize, parse_value, parse_literal):
    name = cls.__name__

    REGISTRY[cls] = GraphQLScalarType(
        name=name,
        description=description,
        serialize=serialize,
        parse_value=parse_value,
        parse_literal=parse_literal,
    )

    return cls


def scalar(cls=None, *, description=None, serialize, parse_value, parse_literal=None):
    """Annotates a class or type as a GraphQL custom scalar.

    Example usages:

    >>> strawberry.scalar(
    >>>     datetime.date,
    >>>     serialize=lambda value: value.isoformat(),
    >>>     parse_value=datetime.parse_date)

    >>> Base64Encoded = strawberry.scalar(
    >>>     NewType("Base64Encoded", bytes),
    >>>     serialize=base64.b64encode,
    >>>     parse_value=base64.b64decode)

    >>> @strawberry.scalar(
    >>>     serialize=lambda value: ",".join(value.items),
    >>>     parse_value=lambda value: CustomList(value.split(",")))
    >>> class CustomList:
    >>>     def __init__(self, items):
    >>>         self.items = items

    """

    def wrap(cls):
        return _process_scalar(
            cls,
            description=description,
            serialize=serialize,
            parse_value=parse_value,
            parse_literal=parse_literal,
        )

    if cls is None:
        return wrap

    return wrap(cls)
