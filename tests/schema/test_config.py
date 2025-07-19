import pytest

from strawberry.schema.config import StrawberryConfig
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
