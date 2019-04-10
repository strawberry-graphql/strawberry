import typing


def is_list(annotation):
    """Returns True if annotation is a typing.List"""

    annotation_origin = getattr(annotation, "__origin__", None)

    return annotation_origin == list


def is_union(annotation):
    """Returns True if annotation is a typing.Union"""

    annotation_origin = getattr(annotation, "__origin__", None)

    return annotation_origin == typing.Union


def is_optional(annotation):
    """Returns True if the annotation is typing.Optional[SomeType]"""

    # Optionals are represented as unions

    if not is_union(annotation):
        return False

    types = annotation.__args__

    # A Union to be optional needs to have at least one None type
    return any([x == None.__class__ for x in types])  # noqa:E721


def get_optional_annotation(annotation):
    types = annotation.__args__
    non_none_types = [x for x in types if x != None.__class__]  # noqa:E721

    return non_none_types[0]


def get_list_annotation(annotation):
    return annotation.__args__[0]
