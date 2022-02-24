from typing import Union

class OperationNameResultInterfaceBlogPost:
    id: str
    title: str

class OperationNameResultInterfaceImage:
    id: str
    url: str

OperationNameResultInterface = Union[OperationNameResultInterfaceBlogPost, OperationNameResultInterfaceImage]

class OperationNameResult:
    interface: OperationNameResultInterface
