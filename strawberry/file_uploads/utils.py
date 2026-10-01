import copy
from collections.abc import Mapping
from typing import Any


class InvalidMultipartRequestError(Exception):
    """The `operations` or `map` field of a multipart request is malformed."""


def replace_placeholders_with_files(
    operations_with_placeholders: dict[str, Any],
    files_map: Mapping[str, Any],
    files: Mapping[str, Any],
) -> dict[str, Any]:
    # TODO: test this with missing variables in operations_with_placeholders
    if not isinstance(operations_with_placeholders, (dict, list)):
        raise InvalidMultipartRequestError(
            "The `operations` field must be a JSON object or array"
        )

    if not isinstance(files_map, Mapping):
        raise InvalidMultipartRequestError("The `map` field must be a JSON object")

    operations = copy.deepcopy(operations_with_placeholders)

    for multipart_form_field_name, operations_paths in files_map.items():
        if not isinstance(operations_paths, list) or not all(
            isinstance(path, str) for path in operations_paths
        ):
            raise InvalidMultipartRequestError(
                "The `map` field values must be arrays of strings"
            )

        file_object = files[multipart_form_field_name]

        for path in operations_paths:
            operations_path_keys = path.split(".")
            value_key = operations_path_keys.pop()

            try:
                target_object = operations
                for key in operations_path_keys:
                    if isinstance(target_object, list):
                        target_object = target_object[int(key)]
                    else:
                        target_object = target_object[key]

                if isinstance(target_object, list):
                    target_object[int(value_key)] = file_object
                else:
                    target_object[value_key] = file_object
            except (IndexError, TypeError, ValueError) as e:
                raise InvalidMultipartRequestError(
                    f"Invalid path in the `map` field: {path}"
                ) from e

    return operations


__all__ = ["InvalidMultipartRequestError", "replace_placeholders_with_files"]
