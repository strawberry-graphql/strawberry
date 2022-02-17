from typing import Any, Optional

import docstring_parser


Docstring = docstring_parser.Docstring


def get(obj: Any) -> Optional[Docstring]:
    if obj is None or obj.__doc__ is None:
        return None
    return docstring_parser.parse(obj.__doc__)


# TODO: GraphQL descriptions should be be formatted as Markdown,
# do we need to perform convertions?


def type_description(docstring: Optional[Docstring]) -> Optional[str]:
    if docstring is None:
        return None

    parts = []
    if docstring.short_description:
        parts.append(docstring.short_description)
    if (
        docstring.blank_after_short_description
        and docstring.short_description
        and docstring.long_description
    ):
        parts.append("")
    if docstring.long_description:
        parts.append(docstring.long_description)

    # TODO: Expose other docstring bits (returns, raises, examples, etc)
    return "\n".join(parts)


def func_description(docstring: Optional[Docstring]) -> Optional[str]:
    return type_description(docstring)


def arg_description(docstring: Optional[Docstring], name: str) -> Optional[str]:
    if docstring is None:
        return None

    for param in docstring.params:
        if param.args[0] == "param" and param.arg_name == name:
            return param.description
    return None


def attribute_description(docstring: Optional[Docstring], name: str) -> Optional[str]:
    if docstring is None:
        return None

    for param in docstring.params:
        if param.args[0] == "attribute" and param.arg_name == name:
            return param.description
    return None
