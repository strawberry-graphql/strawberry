from collections.abc import Iterable

from strawberry.types.base import StrawberryObjectDefinition


class InvalidSuperclassInterfaceError(Exception):
    def __init__(
        self, input_name: str, interfaces: Iterable[StrawberryObjectDefinition]
    ) -> None:
        pretty_interface_names = ", ".join(interface.name for interface in interfaces)
        message = (
            f"An Input class {input_name!r} cannot inherit "
            f"from an Interface(s) {pretty_interface_names!r}"
        )
        super().__init__(message)
