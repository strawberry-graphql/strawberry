from typing_extensions import TypedDict
from typing import Union

class PartialBlogPost(TypedDict):
    # typename: BlogPost
    title: str

class OperationNameResultInterfaceBlogPost(TypedDict):
    # typename: BlogPost
    id: str
    title: str

class OperationNameResultInterfaceImage(TypedDict):
    # typename: Image
    id: str
    url: str

OperationNameResultInterface = Union[OperationNameResultInterfaceBlogPost, OperationNameResultInterfaceImage]

class OperationNameResult(TypedDict):
    interface: OperationNameResultInterface
