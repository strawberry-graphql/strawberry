def get_context(context: object) -> dict[str, object]:
    assert isinstance(context, dict)

    request = context.get("request")
    headers = getattr(request, "headers", {}) if request is not None else {}
    authorization = headers.get("authorization") or headers.get("Authorization")

    extra_context = {"custom_value": "a value from context"}
    if authorization is not None:
        extra_context["authorization"] = authorization

    return {**context, **extra_context}
