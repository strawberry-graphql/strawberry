class _StrawberryMappedScalar:
    def __init__(self, scalar_type: type) -> None:
        self.scalar_type = scalar_type


def _mapped_scalar(cls: type) -> type:
    return _StrawberryMappedScalar(cls)
