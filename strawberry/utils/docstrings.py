from __future__ import annotations

import ast
import inspect
import textwrap
from typing import Any, Dict, Optional, cast

import docstring_parser

from strawberry.utils.cached_property import cached_property


class Docstring:
    """
    Represents the docstring associated with a class/function/etc.

    This is used to automatically produce GraphQL descriptions
    """

    target: Any
    text: Optional[str]

    def __init__(self, target: Any) -> None:
        self.target = target
        if isinstance(self.target, str):
            self.text = self.target
        elif hasattr(self.target, "__doc__"):
            self.text = self.target.__doc__
        else:
            self.text = None

    @cached_property
    def parsed(self) -> docstring_parser.Docstring:
        """
        Returns the parsed docstring associated with the target,
        using the `docstring_parser` package
        """

        ret = docstring_parser.parse(self.text or "")

        # if target is a class, fetch param docstrings from supertypes
        if inspect.isclass(self.target):
            for parent in self.target.mro():
                if parent is self.target:
                    # Ignore main class (already processed)
                    continue
                if parent is object:
                    # Ignore generic object superclass
                    continue
                if parent.__doc__ is None:
                    # Ignore classes without __doc__
                    continue

                # Add docstring data from superclass
                ret.meta += docstring_parser.parse(parent.__doc__).params

        return ret

    @cached_property
    def attribute_docstrings(self) -> Dict[str, Docstring]:
        """
        Return docstrings of all class attributes specified using PEP 224 syntax
        """

        result: Dict[str, Docstring] = {}

        if not inspect.isclass(self.target):
            return result  # Only classes have attributes ;)

        # Examine attributes defined in the target class
        # and its superclasses
        for parent in reversed(self.target.mro()):
            # Extract and parse the source of the class
            try:
                source = inspect.getsource(parent)
            except (TypeError, IOError):
                continue

            source = textwrap.dedent(source)
            module = ast.parse(source)
            cls_body = cast(ast.ClassDef, module.body[0]).body

            # Look for documented attributes
            # PEP 224 docstrings look like an assignment followed by a "free" string
            for stmt1, stmt2 in zip(cls_body[:-1], cls_body[1:]):
                if not isinstance(stmt1, (ast.Assign, ast.AnnAssign)):
                    continue  # 1st statement isn't an assignment

                if not isinstance(stmt2, ast.Expr) or not isinstance(
                    stmt2.value, ast.Str
                ):
                    continue  # 1st statement isn't a free string

                # Extract attribute names from assignment
                if isinstance(stmt1, ast.AnnAssign):
                    attr_names = [cast(ast.Name, stmt1.target).id]
                else:
                    attr_names = [cast(ast.Name, target).id for target in stmt1.targets]

                # Map attr_name to docstring in the result
                for attr_name in attr_names:
                    result[attr_name] = Docstring(stmt2.value.s)

        return result

    @property
    def main_description(self) -> Optional[str]:
        """
        Returns the main description from the docstring.

        Docstring sections for attributes, arguments, examples, etc are not returned here
        """

        # Docstring parser splits the description into "short" (first line) and
        # long (remaining lines), and reassembling it is a bit more clumsy than expected,
        # as:
        # - Leading whitespace is properly normalized
        # - Trailling whitespace is kept (we need to .rstrip() each line)
        # - Trailling lines are kept (we need to .rstrip() the final result)

        parts = []
        if self.parsed.short_description:
            parts += self.parsed.short_description.splitlines()
        if self.parsed.blank_after_short_description:
            parts.append("")
        if self.parsed.long_description:
            parts += self.parsed.long_description.splitlines()

        # Join every
        return "\n".join(part.rstrip() for part in parts).rstrip() or None

    def child_description(self, name: str) -> Optional[str]:
        """
        Returns the doctring of a named subitem,
        usually an argument (for functions) or an attribute (for classes),
        specified in the main docstring using special syntax,
        like an `Args:` section
        """
        for param in self.parsed.params:
            if param.arg_name == name:
                description = (param.description or "").strip()
                if description:
                    return description

        return None

    def attribute_docstring(self, name: str) -> Optional[str]:
        """
        Return docstrings of the given class attribute specified using PEP 224 syntax
        """
        attr_docstring = self.attribute_docstrings.get(name)
        if attr_docstring:
            return attr_docstring.main_description
        return None
