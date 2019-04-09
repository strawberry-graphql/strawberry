import typing


def is_optional(annotation):
    """Returns True if the annotation is typing.Optional[SomeType]"""

    annotation_origin = getattr(annotation, "__origin__", None)

    # Optionals are represented as unions
    if annotation_origin != typing.Union:
        return False

    types = annotation.__args__

    # A Union to be optional needs to have at least one None type
    return any([x == None.__class__ for x in types])  # noqa:E721


def get_optional_annotation(annotation):
    types = annotation.__args__
    non_none_types = [x for x in types if x != None.__class__]  # noqa:E721

    return non_none_types[0]
