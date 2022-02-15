from typing import Any, Optional

import docstring_parser


Docstring = docstring_parser.Docstring


def get(obj: Any) -> Optional[Docstring]:
    if obj is None or obj.__doc__ is None:
        return None
    return docstring_parser.parse(obj.__doc__)


def type_description(docstring: Optional[Docstring]) -> Optional[str]:
    if docstring is not None:
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
        # TODO: GraphQL expects descriptions to be formatted as Markdown,
        # convertion may be needed (See pydoc-markdown)
        return "\n".join(parts)
    return None


def func_description(docstring: Optional[Docstring]) -> Optional[str]:
    return type_description(docstring)


def arg_description(docstring: Optional[Docstring], name: str) -> Optional[str]:
    if docstring is not None:
        for param in docstring.params:
            if param.args[0] == "param" and param.arg_name == name:
                return param.description
    return None


def attribute_description(docstring: Optional[Docstring], name: str) -> Optional[str]:
    if docstring is not None:
        for param in docstring.params:
            if param.args[0] == "attribute" and param.arg_name == name:
                return param.description
    return None
