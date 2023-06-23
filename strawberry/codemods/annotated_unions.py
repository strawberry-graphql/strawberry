import libcst as cst
import libcst.matchers as m
from libcst._nodes.expression import BaseExpression, Call
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand
from libcst.codemod.visitors import AddImportsVisitor


class ConvertUnionToAnnotatedUnion(VisitorBasedCodemodCommand):
    # TODO: support Union and | syntax, also in errors? ugh
    DESCRIPTION: str = (
        "Converts strawberry.union(..., types=(...)) to Annotated[Union[...]]"
    )

    def __init__(self, context: CodemodContext) -> None:
        super().__init__(context)

    # TODO: add types
    @m.leave(m.Call(func=m.Attribute(value=m.Name("strawberry"), attr=m.Name("union"))))
    def leave_union_call(
        self, original_node: Call, updated_node: Call
    ) -> BaseExpression:
        AddImportsVisitor.add_needed_import(
            self.context, "typing_extensions", "Annotated"
        )

        types = original_node.args[1].value.elements
        name = original_node.args[0].value.value

        # create Annotated[Union[...], strawberry.type(...)]
        annotated_union = cst.parse_expression(
            f"Annotated[Union[{', '.join(str(t.value.value) for t in types)}], "
            f"strawberry.type(name={name})]"
        )

        return annotated_union
