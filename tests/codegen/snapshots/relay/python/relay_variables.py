from typing_extensions import TypedDict

class RelayVariablesResultNode(TypedDict):
    id: str
    name: str

class RelayVariablesResult(TypedDict):
    node: RelayVariablesResultNode

class RelayVariablesVariables(TypedDict):
    nodeId: str
