from typing import Union

import libcst as cst
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand


class ConvertUnionToAnnotatedUnion(VisitorBasedCodemodCommand):
    # TODO: support Union and | syntax, also in errors? ugh
    DESCRIPTION: str = (
        "Converts strawberry.union(..., types=(...)) to Annotated[Union[...]]"
    )

    def __init__(self, context: CodemodContext) -> None:
        super().__init__(context)

    def leave_SimpleString(
        self, original_node: cst.SimpleString, updated_node: cst.SimpleString
    ) -> Union[cst.SimpleString, cst.Name]:
        return original_node
