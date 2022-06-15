from typing import Any, List, Type

from pydantic import BaseModel
from pydantic.typing import NoArgAnyCallable


class MissingFieldsListError(Exception):
    def __init__(self, type: Type[BaseModel]):
        message = (
            f"List of fields to copy from {type} is empty. Add fields with the "
            f"`auto` type annotation"
        )

        super().__init__(message)


class UnsupportedTypeError(Exception):
    pass


class UnregisteredTypeException(Exception):
    def __init__(self, type: Type[BaseModel]):
        message = (
            f"Cannot find a Strawberry Type for {type} did you forget to register it?"
        )

        super().__init__(message)


class BothDefaultAndDefaultFactoryDefinedError(Exception):
    def __init__(self, default: Any, default_factory: NoArgAnyCallable):
        message = (
            f"Not allowed to specify both default and default_factory. "
            f"default:{default} default_factory:{default_factory}"
        )

        super().__init__(message)


class AutoFieldsNotInBaseModelError(Exception):
    def __init__(self, fields: List[str], cls_name: str, model: Type[BaseModel]):
        message = (
            f"{cls_name} defines {fields} with strawberry.auto. "
            f"Field(s) not present in {model.__name__} BaseModel."
        )

        super().__init__(message)
