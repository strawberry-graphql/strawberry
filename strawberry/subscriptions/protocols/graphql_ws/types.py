from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Union
from typing_extensions import TypedDict

from graphql import GraphQLFormattedError

from strawberry import UNSET

ConnectionInitPayload = Dict[str, Any]


ConnectionErrorPayload = Dict[str, Any]


@dataclass
class GraphQLTransportMessage:
    def as_dict(self) -> dict:
        data = asdict(self)
        if getattr(self, "payload", None) is UNSET:
            # Unset fields must have a JSON value of "undefined" not "null"
            data.pop("payload")
        return data


@dataclass
class StartPayload(GraphQLTransportMessage):
    query: str
    variables: Optional[Dict[str, Any]] = field(default_factory=dict)
    operationName: Optional[str] = None


class DataPayload(TypedDict, total=False):
    data: Any

    # Optional list of formatted graphql.GraphQLError objects
    errors: Optional[List[GraphQLFormattedError]]


ErrorPayload = GraphQLFormattedError


OperationMessagePayload = Union[
    ConnectionInitPayload,
    ConnectionErrorPayload,
    StartPayload,
    DataPayload,
    ErrorPayload,
]


@dataclass
class OperationMessage(GraphQLTransportMessage):
    type: str
    id: Optional[str] = ""
    payload: Optional[OperationMessagePayload] = field(default_factory=dict)
