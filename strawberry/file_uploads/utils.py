import copy
from collections.abc import Mapping
from typing import Any


class InvalidMultipartRequestError(Exception):
    """The `operations` or `map` field of a multipart request is malformed."""


def _list_index(key: str) -> int:
    # Only non-negative integers are valid list indexes, `int()` would also
    # accept negative numbers, which index from the end of the list
    if not (key.isascii() and key.isdigit()):
        raise ValueError(f"Invalid list index: {key}")

    return int(key)


def replace_placeholders_with_files(
    operations_with_placeholders: dict[str, Any],
    files_map: Mapping[str, Any],
    files: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(operations_with_placeholders, Mapping) and not (
        isinstance(operations_with_placeholders, list)
        and all(isinstance(item, Mapping) for item in operations_with_placeholders)
    ):
        raise InvalidMultipartRequestError(
            "The `operations` field must be a JSON object or an array of objects"
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
                        target_object = target_object[_list_index(key)]
                    else:
                        target_object = target_object[key]

                if isinstance(target_object, list):
                    target_object[_list_index(value_key)] = file_object
                else:
                    target_object[value_key] = file_object
            except (IndexError, KeyError, TypeError, ValueError) as e:
                raise InvalidMultipartRequestError(
                    f"Invalid path in the `map` field: {path}"
                ) from e

    return operations


__all__ = ["InvalidMultipartRequestError", "replace_placeholders_with_files"]
