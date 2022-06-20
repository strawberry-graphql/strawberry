from __future__ import annotations

import ast
import inspect
import textwrap
from typing import Any, Dict, Optional, cast

import docstring_parser
from backports.cached_property import cached_property


class Docstring:
    def __init__(self, target: Any) -> None:
        self.target = target

    @cached_property
    def parsed(self) -> docstring_parser.Docstring:
        text: Optional[str] = None
        if isinstance(self.target, str):
            text = self.target
        elif hasattr(self.target, "__doc__"):
            text = self.target.__doc__
        ret = docstring_parser.parse(text or "")

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
        Return docstring on class attributes, using PEP 224 syntax
        Based on attributes-doc package
        """

        result: Dict[str, Docstring] = {}
        for parent in reversed(self.target.mro()):
            if self.target is object:
                continue
            try:
                source = inspect.getsource(parent)
                source = textwrap.dedent(source)
                module = ast.parse(source)
                cls_ast = cast(ast.ClassDef, module.body[0])
            except Exception:
                continue

            for stmt1, stmt2 in zip(cls_ast.body, cls_ast.body[1:]):
                if not isinstance(stmt1, (ast.Assign, ast.AnnAssign)) or not isinstance(
                    stmt2, ast.Expr
                ):
                    continue
                doc_expr_value = stmt2.value
                if isinstance(doc_expr_value, ast.JoinedStr):
                    continue  # raise FStringFound
                if isinstance(doc_expr_value, ast.Str):
                    if isinstance(stmt1, ast.AnnAssign):
                        attr_names = [cast(ast.Name, stmt1.target).id]
                    else:
                        attr_names = [
                            cast(ast.Name, target).id for target in stmt1.targets
                        ]
                    for attr_name in attr_names:
                        result[attr_name] = Docstring(doc_expr_value.s)

        return result

    @property
    def main_description(self) -> Optional[str]:
        parts = []
        if self.parsed.short_description:
            parts.append(self.parsed.short_description.strip())
        if self.parsed.blank_after_short_description:
            parts.append("")
        if self.parsed.long_description:
            parts.append(self.parsed.long_description.strip())

        # TODO: Maybe expose other docstring bits (returns, raises, examples, etc)
        return "\n".join(parts).strip() or None

    def child_description(self, name: str) -> Optional[str]:
        """
        Returns the doctring
        """
        for param in self.parsed.params:
            if param.arg_name == name:
                description = (param.description or "").strip()
                if description:
                    return description

        return None

    def attribute_docstring(self, name: str) -> Optional[str]:
        attr_docstring = self.attribute_docstrings.get(name)
        if attr_docstring:
            return attr_docstring.main_description
        return None

    @staticmethod
    def get(obj: Any) -> Optional[Docstring]:
        if isinstance(obj, str) or inspect.isclass(obj) or hasattr(obj, "__doc__"):
            return Docstring(obj)
        else:
            return None
