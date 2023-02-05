import pathlib

from .schema import schema


def test_schema():
    schema_output = str(schema).strip("\n").strip(" ")
    output = pathlib.Path(__file__).parent / "schema.gql"
    if not output.exists():
        with output.open("w") as f:
            f.write(schema_output + "\n")

    with output.open() as f:
        expected = f.read().strip("\n").strip(" ")

    assert schema_output == expected
