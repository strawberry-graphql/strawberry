from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING, Any, Dict, List, Union

if TYPE_CHECKING:
    from sanic.request import Request


def convert_request_to_files_dict(request: Request) -> Dict[str, Any]:
    """
    request.files has the following format, even if only a single file is uploaded:

    {
        'textFile': [
            sanic.request.File(
                type='text/plain',
                body=b'strawberry',
                name='textFile.txt'
            )
        ]
    }

    Note that the dictionary entries are lists.
    """
    request_files = request.files
    files_dict: Dict[str, Union[BytesIO, List[BytesIO]]] = {}

    for field_name, file_list in request_files.items():
        assert len(file_list) == 1
        files_dict[field_name] = BytesIO(file_list[0].body)

    return files_dict
