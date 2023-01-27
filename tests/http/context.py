from typing import Dict


def get_context(context: object) -> Dict[str, object]:
    assert isinstance(context, dict)

    return {**context, "custom_value": "a value from context"}
