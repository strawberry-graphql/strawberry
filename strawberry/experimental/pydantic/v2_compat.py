import pydantic

if pydantic.VERSION[0] == "2":

    from pydantic._internal._utils import lenient_issubclass, smart_deepcopy

    def new_type_supertype(type_):
        return type_.__supertype__

else:
    from pydantic.utils import lenient_issubclass, smart_deepcopy

__all__ = ["smart_deepcopy", "lenient_issubclass"]
