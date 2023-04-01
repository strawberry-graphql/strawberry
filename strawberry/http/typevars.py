from typing import TypeVar

Request = TypeVar("Request", contravariant=True)
Response = TypeVar("Response")
Context = TypeVar("Context")
RootValue = TypeVar("RootValue")
