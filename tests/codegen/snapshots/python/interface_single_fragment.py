from typing_extensions import TypedDict

class OperationNameResultInterfaceBlogPost(TypedDict):
    # typename: BlogPost
    id: str
    title: str

class OperationNameResult(TypedDict):
    interface: OperationNameResultInterfaceBlogPost
