from email.message import Message
from typing import Dict, Tuple


def parse_content_type(content_type: str) -> Tuple[str, Dict[str, str]]:
    """Parse a content type header into a mime-type and a dictionary of parameters."""
    email = Message()
    email["content-type"] = content_type

    params = email.get_params()

    assert params

    mime_type, _ = params.pop(0)

    return mime_type, dict(params)
