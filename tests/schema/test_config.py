import pytest

import strawberry
from strawberry.schema.config import (
    StrawberryConfig,
    StrawberryConfigDict,
    normalize_config,
)
from strawberry.types.info import Info


def test_config_post_init_auto_camel_case():
    config = StrawberryConfig(auto_camel_case=True)

    assert config.name_converter.auto_camel_case is True


def test_config_post_init_no_auto_camel_case():
    config = StrawberryConfig(auto_camel_case=False)

    assert config.name_converter.auto_camel_case is False


def test_config_post_init_info_class():
    class CustomInfo(Info):
        test: str = "foo"

    config = StrawberryConfig(info_class=CustomInfo)

    assert config.info_class is CustomInfo
    assert config.info_class.test == "foo"


def test_config_post_init_info_class_is_default():
    config = StrawberryConfig()

    assert config.info_class is Info


def test_config_post_init_info_class_is_not_subclass():
    with pytest.raises(TypeError) as exc_info:
        StrawberryConfig(info_class=object)

    assert str(exc_info.value) == "`info_class` must be a subclass of strawberry.Info"


def test_normalize_config_none_uses_defaults():
    config = normalize_config(None)

    assert isinstance(config, StrawberryConfig)
    assert config.relay_max_results == 100


def test_normalize_config_dataclass_is_used_as_is():
    original = StrawberryConfig(relay_max_results=10)

    assert normalize_config(original) is original


def test_normalize_config_dict_is_converted():
    config = normalize_config({"auto_camel_case": False, "relay_max_results": 10})

    assert isinstance(config, StrawberryConfig)
    assert config.name_converter.auto_camel_case is False
    assert config.relay_max_results == 10


def test_normalize_config_dict_rejects_unknown_keys():
    with pytest.raises(TypeError, match="unexpected keyword argument"):
        normalize_config({"not_a_real_option": True})


def test_schema_accepts_config_dict():
    @strawberry.type
    class Query:
        example_field: str

    schema = strawberry.Schema(query=Query, config={"auto_camel_case": False})

    assert isinstance(schema.config, StrawberryConfig)
    assert "exampleField" not in str(schema)
    assert "example_field" in str(schema)


def test_schema_config_dict_matches_dataclass():
    @strawberry.type
    class Query:
        example_field: str

    from_dict = strawberry.Schema(query=Query, config={"auto_camel_case": False})
    from_dataclass = strawberry.Schema(
        query=Query, config=StrawberryConfig(auto_camel_case=False)
    )

    assert str(from_dict) == str(from_dataclass)


def test_schema_config_dict_validates_info_class():
    @strawberry.type
    class Query:
        name: str

    with pytest.raises(TypeError, match="must be a subclass of strawberry"):
        strawberry.Schema(query=Query, config={"info_class": object})


def test_config_dict_is_typed_dict():
    assert StrawberryConfigDict.__total__ is False
    assert "auto_camel_case" in StrawberryConfigDict.__annotations__


def test_config_dict_supports_all_dataclass_options():
    import typing

    hints = typing.get_type_hints(StrawberryConfigDict)
    assert hints["_unsafe_disable_same_type_validation"] is bool

    config = normalize_config({"_unsafe_disable_same_type_validation": True})

    assert isinstance(config, StrawberryConfig)
    assert config._unsafe_disable_same_type_validation is True
