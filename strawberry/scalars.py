from typing import Any, Dict, NewType, Union

from .custom_scalar import ScalarDefinition, ScalarWrapper


ID = NewType("ID", str)


def is_scalar(
    annotation: Any,
    scalar_registry: Dict[object, Union[ScalarWrapper, ScalarDefinition]],
) -> bool:
    if annotation in scalar_registry:
        return True

    return hasattr(annotation, "_scalar_definition")
