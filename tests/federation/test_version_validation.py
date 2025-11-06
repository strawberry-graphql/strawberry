import pytest

import strawberry
from strawberry.federation.schema_directives import Context, Cost, ListSize, Policy


def test_directive_version_validation_policy():
    """Test that @policy directive requires federation v2.6+"""

    @strawberry.federation.type
    class Product:
        upc: str
        name: str = strawberry.federation.field(
            directives=[Policy(policies=[["admin"]])]
        )

    @strawberry.type
    class Query:
        product: Product

    # Should work with v2.6+
    schema = strawberry.federation.Schema(query=Query, federation_version="2.6")
    assert schema is not None

    # Should work with v2.7
    schema = strawberry.federation.Schema(query=Query, federation_version="2.7")
    assert schema is not None

    # Should fail with v2.5 (policy requires v2.6+)
    with pytest.raises(
        ValueError,
        match=r"Directive @policy requires federation version v2\.6 or higher",
    ):
        strawberry.federation.Schema(query=Query, federation_version="2.5")


def test_directive_version_validation_context():
    """Test that @context directive requires federation v2.8+"""

    @strawberry.federation.type(directives=[Context(name="userContext")])
    class User:
        id: strawberry.ID
        name: str

    @strawberry.type
    class Query:
        user: User

    # Should work with v2.8+
    schema = strawberry.federation.Schema(query=Query, federation_version="2.8")
    assert schema is not None

    # Should work with v2.9
    schema = strawberry.federation.Schema(query=Query, federation_version="2.9")
    assert schema is not None

    # Should fail with v2.7 (context requires v2.8+)
    with pytest.raises(
        ValueError,
        match=r"Directive @context requires federation version v2\.8 or higher",
    ):
        strawberry.federation.Schema(query=Query, federation_version="2.7")


def test_directive_version_validation_cost():
    """Test that @cost directive requires federation v2.9+"""

    @strawberry.federation.type
    class Product:
        upc: str
        name: str = strawberry.federation.field(directives=[Cost(weight=10)])

    @strawberry.type
    class Query:
        product: Product

    # Should work with v2.9+
    schema = strawberry.federation.Schema(query=Query, federation_version="2.9")
    assert schema is not None

    # Should work with v2.10
    schema = strawberry.federation.Schema(query=Query, federation_version="2.10")
    assert schema is not None

    # Should fail with v2.8 (cost requires v2.9+)
    with pytest.raises(
        ValueError, match=r"Directive @cost requires federation version v2\.9 or higher"
    ):
        strawberry.federation.Schema(query=Query, federation_version="2.8")


def test_directive_version_validation_list_size():
    """Test that @listSize directive requires federation v2.9+"""

    @strawberry.federation.type
    class Product:
        upc: str
        friends: list[str] = strawberry.federation.field(
            directives=[ListSize(assumed_size=100)]
        )

    @strawberry.type
    class Query:
        product: Product

    # Should work with v2.9+
    schema = strawberry.federation.Schema(query=Query, federation_version="2.9")
    assert schema is not None

    # Should fail with v2.8 (listSize requires v2.9+)
    with pytest.raises(
        ValueError,
        match=r"Directive @listSize requires federation version v2\.9 or higher",
    ):
        strawberry.federation.Schema(query=Query, federation_version="2.8")


def test_directive_version_validation_multiple_directives():
    """Test validation with multiple directives having different version requirements"""

    @strawberry.federation.type(directives=[Context(name="ctx")])
    class Product:
        upc: str
        name: str = strawberry.federation.field(
            directives=[Policy(policies=[["admin"]]), Cost(weight=5)]
        )

    @strawberry.type
    class Query:
        product: Product

    # Should work with v2.9+ (highest requirement among @context v2.8, @policy v2.6, @cost v2.9)
    schema = strawberry.federation.Schema(query=Query, federation_version="2.9")
    assert schema is not None

    # Should fail with v2.8 (cost requires v2.9)
    with pytest.raises(
        ValueError, match=r"Directive @cost requires federation version v2\.9 or higher"
    ):
        strawberry.federation.Schema(query=Query, federation_version="2.8")

    # Should fail with v2.7 (context requires v2.8)
    with pytest.raises(
        ValueError,
        match=r"Directive @context requires federation version v2\.8 or higher",
    ):
        strawberry.federation.Schema(query=Query, federation_version="2.7")


def test_older_directives_work_with_any_version():
    """Test that older directives work with any federation version"""

    @strawberry.federation.type(keys=["id"])
    class Product:
        id: strawberry.ID
        name: str = strawberry.federation.field(external=True)

    @strawberry.type
    class Query:
        product: Product

    # Should work with any version since @key and @external are from v2.0
    for version in ["2.0", "2.5", "2.7", "2.9", "2.11"]:
        schema = strawberry.federation.Schema(query=Query, federation_version=version)
        assert schema is not None


def test_default_version_uses_latest():
    """Test that default federation version uses latest"""

    @strawberry.federation.type
    class Product:
        upc: str

    @strawberry.type
    class Query:
        product: Product

    # Default should use latest version
    schema = strawberry.federation.Schema(query=Query)
    assert schema.federation_version == (2, 11)  # Latest version
