import inspect
from typing import Any, Optional

import docstring_parser
from attributes_doc import get_attributes_doc


class Docstring:
    def __init__(self, target: Any) -> None:
        self.target = target
        self._docstring: Optional[docstring_parser.Docstring] = None
        self._attribute_raw_docstrings: Optional[dict[str, str]] = None
        self._attribute_docstrings: Optional[dict[str, Docstring]] = None

    @property
    def parsed_docstring(self) -> Optional[docstring_parser.Docstring]:
        # Parse docstrings lazily, to avoid extra processing if
        # config descriptions_from_docstrings is disabled
        if self._docstring is None:
            if isinstance(self.target, str):
                self._docstring = docstring_parser.parse(self.target)
            else:
                self._docstring = docstring_parser.parse(self.target.__doc__ or "")

            # if target is a class, fetch param docstrings from supertypes
            if inspect.isclass(self.target):
                for parent in self.target.mro():
                    if parent is self.target or parent is object:
                        continue
                    if parent.__doc__ is None:
                        continue
                    parent_docstring = docstring_parser.parse(parent.__doc__)
                    self._docstring.meta += parent_docstring.params

        return self._docstring

    @property
    def main_description(self) -> Optional[str]:
        docstring = self.parsed_docstring
        if docstring is None:
            return None

        parts = []
        if docstring.short_description:
            parts.append(docstring.short_description)
        if docstring.blank_after_short_description:
            parts.append("")
        if docstring.long_description:
            parts.append(docstring.long_description)

        # TODO: Expose other docstring bits (returns, raises, examples, etc)
        return "\n".join(parts).strip() or None

    def child_description(self, child_name: str) -> Optional[str]:
        docstring = self.parsed_docstring
        if docstring is None:
            return None

        for param in docstring.params:
            if param.arg_name == child_name and param.description:
                description = param.description.strip()
                if description:
                    return description

        return None

    def attribute_docstring(self, name: str) -> Optional[str]:
        if self._attribute_raw_docstrings is None:
            self._attribute_raw_docstrings = get_attributes_doc(self.target)
            self._attribute_docstrings = {}
        if name not in self._attribute_docstrings:
            raw_docstring = self._attribute_raw_docstrings.get(name)
            docstring = None if raw_docstring is None else Docstring(raw_docstring)
            self._attribute_docstrings[name] = docstring

        return self._attribute_docstrings[name]

    @staticmethod
    def get(obj: Any) -> Optional["Docstring"]:
        if obj is None:
            return None

        if inspect.isclass(obj):
            # If this is a class and neither it or any of the
            # other superclasses have docstrings
            if all([x.__doc__ is None for x in obj.mro()]):
                return None
        else:
            # If it doesn't have a docstring
            if obj.__doc__ is None:
                return None
        return Docstring(obj)
