import pytest

from strawberry.exceptions import MissingOptionalDependenciesError


def test_missing_optional_dependencies_error():
    with pytest.raises(MissingOptionalDependenciesError) as exc_info:
        raise MissingOptionalDependenciesError()

    assert str(exc_info.value) == "Some optional dependencies are missing"


def test_missing_optional_dependencies_error_packages():
    with pytest.raises(MissingOptionalDependenciesError) as exc_info:
        raise MissingOptionalDependenciesError(packages=["a", "b"])

    assert (
        str(exc_info.value)
        == "Some optional dependencies are missing (hint: pip install a b)"
    )


def test_missing_optional_dependencies_error_extras():
    with pytest.raises(MissingOptionalDependenciesError) as exc_info:
        raise MissingOptionalDependenciesError(extras=["dev", "test"])

    assert (
        str(exc_info.value)
        == "Some optional dependencies are missing (hint: pip install 'strawberry-graphql[dev,test]')"
    )


def test_missing_optional_dependencies_error_packages_and_extras():
    with pytest.raises(MissingOptionalDependenciesError) as exc_info:
        raise MissingOptionalDependenciesError(
            packages=["a", "b"],
            extras=["dev", "test"],
        )

    assert (
        str(exc_info.value)
        == "Some optional dependencies are missing (hint: pip install a b 'strawberry-graphql[dev,test]')"
    )
