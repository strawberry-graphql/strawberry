from email.message import Message


def parse_content_type(content_type: str) -> tuple[str, dict[str, str]]:
    """Parse a content type header into a mime-type and a dictionary of parameters."""
    email = Message()
    email["content-type"] = content_type

    params = email.get_params()

    assert params

    mime_type, _ = params.pop(0)

    return mime_type, dict(params)
