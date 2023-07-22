import pydantic

if pydantic.VERSION[0] == '2':
    from pydantic._internal._utils import smart_deepcopy
    from pydantic._internal._utils import lenient_issubclass
    from typing_extensions import get_args, get_origin
    from pydantic._internal._typing_extra import is_new_type
    from pydantic.v1.fields import ModelField as ModelField
    def new_type_supertype(type_):
        return type_.__supertype__
else:
    from pydantic.utils import smart_deepcopy
    from pydantic.utils import lenient_issubclass
    from pydantic.typing import get_args, get_origin, is_new_type, new_type_supertype
    from pydantic.fields import ModelField as ModelField

__all__ = ["smart_deepcopy", "lenient_issubclass"]
