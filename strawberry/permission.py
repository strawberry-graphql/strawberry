class BasePermission(object):
    """
    A base permission class 
    """
    def has_permission(self, info):
        raise NotImplementedError(
            "Permission classes should override has_permission method"
        )
