from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING, Any, Optional, Union, cast

from sanic.request import File

if TYPE_CHECKING:
    from sanic.request import Request


def convert_request_to_files_dict(request: Request) -> dict[str, Any]:
    """Converts the request.files dictionary to a dictionary of BytesIO objects.

    `request.files` has the following format, even if only a single file is uploaded:

    ```python
    {
        "textFile": [
            sanic.request.File(type="text/plain", body=b"strawberry", name="textFile.txt")
        ]
    }
    ```

    Note that the dictionary entries are lists.
    """
    request_files = cast(Optional[dict[str, list[File]]], request.files)

    if not request_files:
        return {}

    files_dict: dict[str, Union[BytesIO, list[BytesIO]]] = {}

    for field_name, file_list in request_files.items():
        assert len(file_list) == 1

        files_dict[field_name] = BytesIO(file_list[0].body)

    return files_dict


__all__ = ["convert_request_to_files_dict"]
