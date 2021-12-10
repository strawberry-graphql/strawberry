from typing import Type, Any

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
    def __init__(self, type: BaseModel):
        message = (
            f"Cannot find a Strawberry Type for {type} did you forget to register it?"
        )

        super().__init__(message)


class DefaultAndDefaultFactoryDefined(Exception):
    def __init__(self, default: Any, default_factory: NoArgAnyCallable):
        message = f"Not allowed to specify both default and default_factory. default:{default} default_factory:{default_factory}"

        super().__init__(message)
