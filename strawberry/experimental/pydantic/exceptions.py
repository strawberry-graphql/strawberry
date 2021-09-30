from typing import Type

from pydantic import BaseModel


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
