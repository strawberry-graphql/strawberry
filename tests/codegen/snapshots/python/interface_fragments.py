from typing import Union

class OperationNameResultInterfaceBlogPost:
    # typename: BlogPost
    id: str
    title: str

class OperationNameResultInterfaceImage:
    # typename: Image
    id: str
    url: str

OperationNameResultInterface = Union[OperationNameResultInterfaceBlogPost, OperationNameResultInterfaceImage]

class OperationNameResult:
    interface: OperationNameResultInterface
