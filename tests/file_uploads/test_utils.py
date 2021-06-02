from io import BytesIO

from strawberry.file_uploads.utils import replace_placeholders_with_files


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
