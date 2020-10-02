class Private:
    """Represent a private field that won't be converted into a GraphQL field

    Example:

    >>> import strawberry
    >>> @strawberry.type
    ... class User:
    ...     name: str
    ...     age: strawberry.Private[int]
    """

    __slots__ = ("type",)

    def __init__(self, type):
        self.type = type

    def __repr__(self):
        if isinstance(self.type, type):
            type_name = self.type.__name__
        else:
            # typing objects, e.g. List[int]
            type_name = repr(self.type)
        return f"strawberry.Private[{type_name}]"

    def __class_getitem__(cls, type):
        return Private(type)
