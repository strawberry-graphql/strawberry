import copy
from typing import Any, Dict, Mapping


def replace_placeholders_with_files(
    operations_with_placeholders: Dict[str, Any],
    files_map: Mapping[str, Any],
    files: Mapping[str, Any],
) -> Dict[str, Any]:
    # TODO: test this with missing variables in operations_with_placeholders
    operations = copy.deepcopy(operations_with_placeholders)

    for multipart_form_field_name, operations_paths in files_map.items():
        file_object = files[multipart_form_field_name]

        for path in operations_paths:
            operations_path_keys = path.split(".")
            value_key = operations_path_keys.pop()

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

    return operations
