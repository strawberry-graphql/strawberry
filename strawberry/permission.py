class BasePermission:
    """
    Base class for creating permissions
    """

    def has_permission(self, info):
        raise NotImplementedError(
            "Permission classes should override has_permission method"
        )
