from io import BytesIO

import pytest

from strawberry.file_uploads.utils import (
    InvalidMultipartRequestError,
    replace_placeholders_with_files,
)


def test_does_deep_copy():
    operations = {
        "query": "mutation($file: Upload!) { upload_file(file: $file) { id } }",
        "variables": {"file": None},
    }
    files_map = {}
    files = {}

    result = replace_placeholders_with_files(operations, files_map, files)
    assert result == operations
    assert result is not operations


def test_empty_files_map():
    operations = {
        "query": "mutation($files: [Upload!]!) { upload_files(files: $files) { id } }",
        "variables": {"files": [None, None]},
    }
    files_map = {}
    files = {"0": BytesIO(), "1": BytesIO()}

    result = replace_placeholders_with_files(operations, files_map, files)
    assert result == operations


def test_empty_operations_paths():
    operations = {
        "query": "mutation($files: [Upload!]!) { upload_files(files: $files) { id } }",
        "variables": {"files": [None, None]},
    }
    files_map = {"0": [], "1": []}
    files = {"0": BytesIO(), "1": BytesIO()}

    result = replace_placeholders_with_files(operations, files_map, files)
    assert result == operations


def test_single_file_in_single_location():
    operations = {
        "query": "mutation($file: Upload!) { upload_file(file: $file) { id } }",
        "variables": {"file": None},
    }
    files_map = {"0": ["variables.file"]}
    file0 = BytesIO()
    files = {"0": file0}

    result = replace_placeholders_with_files(operations, files_map, files)
    assert result["query"] == operations["query"]
    assert result["variables"]["file"] == file0


def test_single_file_in_multiple_locations():
    operations = {
        "query": "mutation($a: Upload!, $b: Upload!) { pair(a: $a, b: $a) { id } }",
        "variables": {"a": None, "b": None},
    }
    files_map = {"0": ["variables.a", "variables.b"]}
    file0 = BytesIO()
    files = {"0": file0}

    result = replace_placeholders_with_files(operations, files_map, files)
    assert result["query"] == operations["query"]
    assert result["variables"]["a"] == file0
    assert result["variables"]["b"] == file0


def test_file_list():
    operations = {
        "query": "mutation($files: [Upload!]!) { upload_files(files: $files) { id } }",
        "variables": {"files": [None, None]},
    }
    files_map = {"0": ["variables.files.0"], "1": ["variables.files.1"]}
    file0 = BytesIO()
    file1 = BytesIO()
    files = {"0": file0, "1": file1}

    result = replace_placeholders_with_files(operations, files_map, files)
    assert result["query"] == operations["query"]
    assert result["variables"]["files"][0] == file0
    assert result["variables"]["files"][1] == file1


def test_single_file_reuse_in_list():
    operations = {
        "query": "mutation($a: [Upload!]!, $b: Upload!) { mixed(a: $a, b: $b) { id } }",
        "variables": {"a": [None, None], "b": None},
    }
    files_map = {"0": ["variables.a.0"], "1": ["variables.a.1", "variables.b"]}
    file0 = BytesIO()
    file1 = BytesIO()
    files = {"0": file0, "1": file1}

    result = replace_placeholders_with_files(operations, files_map, files)
    assert result["query"] == operations["query"]
    assert result["variables"]["a"][0] == file0
    assert result["variables"]["a"][1] == file1
    assert result["variables"]["b"] == file1


def test_using_single_file_multiple_times_in_same_list():
    operations = {
        "query": "mutation($files: [Upload!]!) { upload_files(files: $files) { id } }",
        "variables": {"files": [None, None]},
    }
    files_map = {"0": ["variables.files.0", "variables.files.1"]}
    file0 = BytesIO()
    files = {"0": file0}

    result = replace_placeholders_with_files(operations, files_map, files)
    assert result["query"] == operations["query"]
    assert result["variables"]["files"][0] == file0
    assert result["variables"]["files"][1] == file0


def test_deep_nesting():
    operations = {
        "query": "mutation($list: [ComplexInput!]!) { mutate(list: $list) { id } }",
        "variables": {"a": [{"files": [None, None]}]},
    }
    files_map = {"0": ["variables.a.0.files.0"], "1": ["variables.a.0.files.1"]}
    file0 = BytesIO()
    file1 = BytesIO()
    files = {"0": file0, "1": file1}

    result = replace_placeholders_with_files(operations, files_map, files)
    assert result["query"] == operations["query"]
    assert result["variables"]["a"][0]["files"][0] == file0
    assert result["variables"]["a"][0]["files"][1] == file1


@pytest.mark.parametrize(
    "operations", [None, 1, "string", True, [None], [1], [{"query": "{ a }"}, "b"]]
)
def test_operations_must_be_an_object_or_array_of_objects(operations: object):
    with pytest.raises(
        InvalidMultipartRequestError,
        match="The `operations` field must be a JSON object or an array of objects",
    ):
        replace_placeholders_with_files(operations, {}, {})  # type: ignore[arg-type]


@pytest.mark.parametrize("files_map", [None, ["0"], "string", 1])
def test_files_map_must_be_an_object(files_map: object):
    with pytest.raises(
        InvalidMultipartRequestError, match="The `map` field must be a JSON object"
    ):
        replace_placeholders_with_files({}, files_map, {})  # type: ignore[arg-type]


@pytest.mark.parametrize("operations_paths", ["variables.file", [1], [None], None])
def test_files_map_values_must_be_arrays_of_strings(operations_paths: object):
    with pytest.raises(
        InvalidMultipartRequestError,
        match="The `map` field values must be arrays of strings",
    ):
        replace_placeholders_with_files(
            {"variables": {"file": None}}, {"0": operations_paths}, {"0": BytesIO()}
        )


@pytest.mark.parametrize(
    "path",
    [
        "variables.files.abc",
        "variables.files.5",
        "variables.files.-1",
        "variables.name.first",
        "variables.missing.file",
    ],
)
def test_invalid_operations_path(path: str):
    operations = {"variables": {"files": [None], "name": "strawberry"}}

    with pytest.raises(
        InvalidMultipartRequestError, match="Invalid path in the `map` field"
    ):
        replace_placeholders_with_files(operations, {"0": [path]}, {"0": BytesIO()})


def test_operations_can_be_any_mapping():
    class CustomDict(dict):
        pass

    operations = CustomDict(variables={"file": None})
    file = BytesIO()

    result = replace_placeholders_with_files(
        operations, {"0": ["variables.file"]}, {"0": file}
    )
    assert result["variables"]["file"] is file


def test_batch_operations():
    operations = [{"variables": {"file": None}}, {"variables": {"file": None}}]
    file = BytesIO()

    result = replace_placeholders_with_files(
        operations, {"0": ["1.variables.file"]}, {"0": file}
    )
    assert result[0]["variables"]["file"] is None
    assert result[1]["variables"]["file"] is file
