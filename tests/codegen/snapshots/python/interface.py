from typing_extensions import TypedDict

class OperationNameResultInterface(TypedDict):
    id: str

class OperationNameResult(TypedDict):
    interface: OperationNameResultInterface
