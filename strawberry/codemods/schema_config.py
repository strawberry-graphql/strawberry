from __future__ import annotations

import libcst as cst
import libcst.matchers as m
from libcst._nodes.expression import BaseExpression  # noqa: TCH002
from libcst.codemod import VisitorBasedCodemodCommand
from libcst.codemod.visitors import RemoveImportsVisitor


class ConvertStrawberryConfigToDict(VisitorBasedCodemodCommand):
    DESCRIPTION: str = "Converts StrawberryConfig(...) to dict"

    @m.leave(m.Call(func=m.Name("StrawberryConfig")))
    def leave_strawberry_config_call(
        self, original_node: cst.Call, _: cst.Call
    ) -> BaseExpression:
        RemoveImportsVisitor.remove_unused_import(
            self.context, "strawberry.schema.config", "StrawberryConfig"
        )
        return cst.Call(func=cst.Name(value="dict"), args=original_node.args)
