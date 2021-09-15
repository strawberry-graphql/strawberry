from typing import Iterable


class InvalidSuperclassInterfaceError(Exception):
    def __init__(self, input_name: str, interface_names: Iterable[str]):
        interface_names = ", ".join(interface_names)
        message = (
            f"An Input class {input_name!r} cannot inherit "
            f"from an Interface(s) {interface_names!r}"
        )
        super().__init__(message)
