from typing import Any, Optional

import docstring_parser


class Docstring:
    def __init__(self, target: Any) -> None:
        self.target = target
        self._resolved = False
        self._docstring: Optional[docstring_parser.Docstring] = None

    @property
    def parsed_docstring(self) -> Optional[docstring_parser.Docstring]:
        # Parse docstrings lazily, to avoid extra processing if
        # config description_from_docstrings is disabled
        if not self._resolved:
            self._docstring = docstring_parser.parse(self.target.__doc__)
            self._resolved = True
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

    @staticmethod
    def get(obj: Any) -> Optional["Docstring"]:
        if obj is None or obj.__doc__ is None:
            return None
        return Docstring(obj)
