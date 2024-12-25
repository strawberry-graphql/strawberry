import pytest


def test_can_import(mocker):
    # mocking sys.modules.ddtrace so we don't get an ImportError
    mocker.patch.dict("sys.modules", ddtrace=mocker.MagicMock())


def test_fails_if_import_is_not_found():
    with pytest.raises(ImportError):
        from strawberry.extensions.tracing import Blueberry  # noqa: F401
