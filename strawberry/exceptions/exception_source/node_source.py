from typing import NamedTuple

import libcst as cst
from libcst.metadata import CodeRange


class NodeSource(NamedTuple):
    position: CodeRange
    node: cst.CSTNode
