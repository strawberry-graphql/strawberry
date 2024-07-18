class CodegenError(Exception):
    pass


class NoOperationProvidedError(CodegenError):
    pass


class NoOperationNameProvidedError(CodegenError):
    pass


class MultipleOperationsProvidedError(CodegenError):
    pass


__all__ = [
    "CodegenError",
    "NoOperationProvidedError",
    "NoOperationNameProvidedError",
    "MultipleOperationsProvidedError",
]
