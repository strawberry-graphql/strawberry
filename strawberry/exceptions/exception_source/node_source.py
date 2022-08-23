from typing import TYPE_CHECKING, NamedTuple


if TYPE_CHECKING:
    from libcst import CSTNode
    from libcst.metadata import CodeRange


class NodeSource(NamedTuple):
    position: "CodeRange"
    node: "CSTNode"
