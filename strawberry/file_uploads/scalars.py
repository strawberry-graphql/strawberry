from typing import Any, NewType

from graphql import GraphQLError
from graphql.pyutils import inspect

from strawberry.types.scalar import scalar

Upload = NewType("Upload", bytes)

# Values reach the `Upload` scalar from one of two places: the JSON body of the
# request (variables and inline literals), or the multipart request handling,
# which replaces file placeholders with the file objects provided by the web
# framework. Only the latter is a valid upload, so rejecting the types a JSON
# decoder can produce keeps this framework agnostic: every file object is
# accepted (Django's `UploadedFile`, Starlette's `UploadFile`, Sanic's `File`
# named tuple, a plain `BytesIO`, ...) without knowing about any of them.
_JSON_TYPES = (bool, int, float, str, list, dict)


def parse_upload_value(value: Any) -> Any:
    if isinstance(value, _JSON_TYPES):
        raise GraphQLError(
            f"Upload cannot represent a non-file value: {inspect(value)}"
        )

    return value


UploadDefinition = scalar(
    name="Upload",
    description="Represents a file upload.",
    serialize=lambda v: v,
    parse_value=parse_upload_value,
)

__all__ = ["Upload", "UploadDefinition"]
