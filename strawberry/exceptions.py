# TODO: add links to docs

from typing import List, Set


class MissingReturnAnnotationError(Exception):
    """The field is missing the return annotation"""

    def __init__(self, field_name: str):
        message = (
            f'Return annotation missing for field "{field_name}", '
            "did you forget to add it?"
        )

        super().__init__(message)


class MissingArgumentsAnnotationsError(Exception):
    """The field is missing the annotation for one or more arguments"""

    def __init__(self, field_name: str, arguments: Set[str]):
        arguments_list: List[str] = sorted(list(arguments))

        if len(arguments_list) == 1:
            argument = f'argument "{arguments_list[0]}"'
        else:
            head = ", ".join(arguments_list[:-1])
            argument = f'arguments "{head}" and "{arguments_list[-1]}"'

        message = (
            f"Missing annotation for {argument} "
            f'in field "{field_name}", did you forget to add it?'
        )

        super().__init__(message)
