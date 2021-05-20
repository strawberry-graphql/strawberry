from io import BytesIO
from typing import Dict, List, Union

from sanic.request import Request


def convert_request_to_files_dict(request: Request) -> dict:
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
    request_files: dict = request.files
    files_dict: Dict[str, Union[BytesIO, List[BytesIO]]] = {}

    for field_name, file_list in request_files.items():
        if len(file_list) == 1:
            # Turn single item file lists into a single file object
            files_dict[field_name] = BytesIO(file_list[0].body)
        else:  # pragma: no cover
            # TODO: Test this branch once file list uploads are supported (see #766).
            # https://github.com/strawberry-graphql/strawberry/issues/766

            # Preserve actual file lists for file list upload support
            file_object_list = [BytesIO(file_item.body) for file_item in file_list]
            files_dict[field_name] = file_object_list

    return files_dict
