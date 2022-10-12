type OperationNameResultInterfaceBlogPost = {
    id: string
    title: string
}

type OperationNameResultInterfaceImage = {
    id: string
    url: string
}

type OperationNameResultInterface = OperationNameResultInterfaceBlogPost | OperationNameResultInterfaceImage

type OperationNameResult = {
    interface: OperationNameResultInterface
}
