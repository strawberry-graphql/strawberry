# TODO: add links to docs


class MissingReturnAnnotationError(Exception):
    """The field is missing the return annotation"""

    def __init__(self, field_name: str):
        message = (
            f'Return annotation missing for field "{field_name}", '
            "did you forget to add it?"
        )

        super().__init__(message)
