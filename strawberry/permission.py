class BasePermission:
    """
    Base class for creating permissions
    """

    def has_permission(self, source, info, **kwargs):
        raise NotImplementedError(
            "Permission classes should override has_permission method"
        )
