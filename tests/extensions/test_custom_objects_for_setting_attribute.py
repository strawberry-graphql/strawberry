import pytest

from strawberry.extensions.tracing.opentelemetry import OpenTelemetryExtension


@pytest.fixture
def otel_ext():
    return OpenTelemetryExtension()


class SimpleObject:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return f"SimpleObject({self.value})"


class ComplexObject:
    def __init__(self, simple_object, value):
        self.simple_object = simple_object
        self.value = value

    def __str__(self):
        return f"ComplexObject({self.simple_object!s}, {self.value})"


def test_convert_complex_number(otel_ext):
    value = 3 + 4j
    assert otel_ext.convert_to_allowed_types(value) == "(3+4j)"


def test_convert_range(otel_ext):
    value = range(3)
    assert otel_ext.convert_to_allowed_types(value) == "0, 1, 2"


def test_convert_bytearray(otel_ext):
    value = bytearray(b"hello world")
    assert otel_ext.convert_to_allowed_types(value) == b"hello world"


def test_convert_memoryview(otel_ext):
    value = memoryview(b"hello world")
    assert otel_ext.convert_to_allowed_types(value) == b"hello world"


def test_convert_set(otel_ext):
    value = {1, 2, 3, 4}
    converted_value = otel_ext.convert_to_allowed_types(value)
    assert set(converted_value.strip("{}").split(", ")) == {"1", "2", "3", "4"}


def test_convert_frozenset(otel_ext):
    value = frozenset([1, 2, 3, 4])
    converted_value = otel_ext.convert_to_allowed_types(value)
    assert set(converted_value.strip("{}").split(", ")) == {"1", "2", "3", "4"}


def test_convert_complex_object_with_simple_object(otel_ext):
    simple_obj = SimpleObject(42)
    complex_obj = ComplexObject(simple_obj, 99)
    assert (
        otel_ext.convert_to_allowed_types(complex_obj)
        == "ComplexObject(SimpleObject(42), 99)"
    )


def test_convert_dictionary(otel_ext):
    value = {
        "int": 1,
        "float": 3.14,
        "bool": True,
        "str": "hello",
        "list": [1, 2, 3],
        "tuple": (4, 5, 6),
        "simple_object": SimpleObject(42),
    }

    expected = (
        "{int: 1, "
        "float: 3.14, "
        "bool: True, "
        "str: hello, "
        "list: 1, 2, 3, "
        "tuple: 4, 5, 6, "
        "simple_object: SimpleObject(42)}"
    )

    assert otel_ext.convert_to_allowed_types(value) == expected


def test_convert_bool(otel_ext):
    assert otel_ext.convert_to_allowed_types(True) is True
    assert otel_ext.convert_to_allowed_types(False) is False


def test_convert_str(otel_ext):
    assert otel_ext.convert_to_allowed_types("hello") == "hello"


def test_convert_bytes(otel_ext):
    assert otel_ext.convert_to_allowed_types(b"hello") == b"hello"


def test_convert_int(otel_ext):
    assert otel_ext.convert_to_allowed_types(42) == 42


def test_convert_float(otel_ext):
    assert otel_ext.convert_to_allowed_types(3.14) == 3.14


def test_convert_simple_object(otel_ext):
    obj = SimpleObject(42)
    assert otel_ext.convert_to_allowed_types(obj) == "SimpleObject(42)"


def test_convert_list_of_basic_types(otel_ext):
    value = [1, "hello", 3.14, True, False]
    assert otel_ext.convert_to_allowed_types(value) == "1, hello, 3.14, True, False"


def test_convert_list_of_mixed_types(otel_ext):
    value = [1, "hello", 3.14, SimpleObject(42)]
    assert (
        otel_ext.convert_to_allowed_types(value) == "1, hello, 3.14, SimpleObject(42)"
    )


def test_convert_tuple_of_basic_types(otel_ext):
    value = (1, "hello", 3.14, True, False)
    assert otel_ext.convert_to_allowed_types(value) == "1, hello, 3.14, True, False"


def test_convert_tuple_of_mixed_types(otel_ext):
    value = (1, "hello", 3.14, SimpleObject(42))
    assert (
        otel_ext.convert_to_allowed_types(value) == "1, hello, 3.14, SimpleObject(42)"
    )
