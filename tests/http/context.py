def get_context(context: object) -> dict[str, object]:
    assert isinstance(context, dict)

    return {**context, "custom_value": "a value from context"}
