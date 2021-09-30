"""Reference implementation of [PEP-0661](https://www.python.org/dev/peps/pep-0661/)

See https://github.com/taleinat/python-stdlib-sentinels
"""

import sys as _sys
from typing import Optional


__all__ = ["sentinel"]


def sentinel(
    name: str,
    repr: Optional[str] = None,
):
    """Create a unique sentinel object.
    *name* should be the fully-qualified name of the variable to which the
    return value shall be assigned.
    *repr*, if supplied, will be used for the repr of the sentinel object.
    If not provided, "<name>" will be used (with any leading class names
    removed).
    """
    try:
        module_globals = _get_parent_frame().f_globals
        module = module_globals.get("__name__", "__main__")
    except (AttributeError, ValueError):  # pragma: no cover
        # Store the class in the sentinels module namespace.
        module_globals = globals()
        module = __name__

    name = _sys.intern(str(name))
    repr_string = repr or f'<{name.split(".")[-1]}>'
    class_name = _sys.intern(_get_class_name(name, module))

    # If a sentinel with the same name was already defined in the module,
    # return it.
    if class_name in module_globals:
        return module_globals[class_name]()

    class_namespace = {
        "__repr__": lambda self: repr_string,
    }
    cls = type(class_name, (), class_namespace)

    # For copying and pickling+unpickling to work, the class's __module__
    # is set to the name of a module where the class may be found by its
    # name.
    cls.__module__ = module
    module_globals[class_name] = cls
    del module_globals  # Avoid a reference cycle.

    sentinel = cls()

    def __new__(cls_):
        return sentinel

    __new__.__qualname__ = f"{class_name}.__new__"
    cls.__new__ = __new__  # type: ignore

    return sentinel


if hasattr(_sys, "_getframe"):

    def _get_parent_frame():
        """Return the frame object for the caller's parent stack frame."""
        return _sys._getframe(2)


else:  # pragma: no cover

    def _get_parent_frame():
        """Return the frame object for the caller's parent stack frame."""
        try:
            raise Exception
        except Exception:
            info = _sys.exc_info()[2]
            if not info:
                return None
            f_back = info.tb_frame.f_back
            if not f_back:
                return None
            return f_back.f_back


def _get_class_name(
    sentinel_qualname: str,
    module_name: Optional[str] = None,
) -> str:
    return (
        "_sentinel_type__"
        f'{(module_name.replace(".", "_") + "__") if module_name else ""}'
        f'{sentinel_qualname.replace(".", "_")}'
    )
