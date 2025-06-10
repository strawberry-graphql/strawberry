from collections.abc import Iterable

from strawberry.types.base import StrawberryObjectDefinition


class InvalidSuperclassInterfaceError(Exception):
    def __init__(
        self, input_name: str, interfaces: Iterable[StrawberryObjectDefinition]
    ) -> None:
        pretty_interface_names = ", ".join(interface.name for interface in interfaces)
        message = (
            f"Input class {input_name!r} cannot inherit "
            f"from interface(s): {pretty_interface_names}"
        )
        super().__init__(message)
