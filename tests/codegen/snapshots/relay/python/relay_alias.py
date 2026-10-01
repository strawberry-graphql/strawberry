from typing_extensions import TypedDict

class RelayAliasResultNode(TypedDict):
    # alias for id
    nodeId: str
    # alias for name
    userName: str

class RelayAliasResult(TypedDict):
    node: RelayAliasResultNode
