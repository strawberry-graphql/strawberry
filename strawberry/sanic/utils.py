from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union, cast

if TYPE_CHECKING:
    from sanic.request import File, Request


def convert_request_to_files_dict(request: Request) -> dict[str, Any]:
    """Converts the request.files dictionary to a dictionary of sanic Request objects.

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
    request_files = cast("Optional[dict[str, list[File]]]", request.files)

    if not request_files:
        return {}

    files_dict: dict[str, Union[File, list[File]]] = {}

    for field_name, file_list in request_files.items():
        assert len(file_list) == 1

        files_dict[field_name] = file_list[0]

    return files_dict


__all__ = ["convert_request_to_files_dict"]
