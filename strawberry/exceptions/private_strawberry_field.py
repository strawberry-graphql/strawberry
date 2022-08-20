from typing import Type

from .exception import ExceptionSourceIsClassAttribute, StrawberryException


class PrivateStrawberryFieldError(ExceptionSourceIsClassAttribute, StrawberryException):
    documentation_url = "https://errors.strawberry.rocks/private-strawberry-field"

    def __init__(self, field_name: str, cls: Type):
        self.cls = cls
        self.field_name = field_name

        self.message = (
            f"Field {field_name} on type {cls.__name__} cannot be both "
            "private and a strawberry.field"
        )
        self.rich_message = (
            f"[underline]{self.field_name}[/]` field cannot be both "
            "private and a strawberry.field "
        )
        self.annotation_message = "private field defined here"
        self.suggestion = (
            "To fix this error you should either make the field non private, "
            "or remove the strawberry.field annotation."
        )
