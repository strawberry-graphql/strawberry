from typing import Any, Dict, List, Mapping


def replace_placeholders_with_files(
    operations: Dict[str, Any],
    files_map: Dict[str, List[str]],
    files: Mapping[str, Any],
) -> Dict[str, Any]:
    path_to_key_iter = (
        (value.split("."), key)
        for (key, values) in files_map.items()
        for value in values
    )

    output = operations

    for path, key in path_to_key_iter:
        file_obj = files[key]

        output = replace_placeholders(output, file_obj, path)

    return output


def replace_placeholders(operations: Dict[str, Any], file_obj: Any, path: List[str]):
    if not path:
        return file_obj

    key = path[0]

    sub_dict = replace_placeholders(operations[key], file_obj, path[1:])

    return {**operations, **{key: sub_dict}}
