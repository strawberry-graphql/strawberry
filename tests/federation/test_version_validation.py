import pytest

import strawberry
from strawberry.federation.schema_directives import Context, Cost, ListSize, Policy


@pytest.mark.parametrize(
    ("directive_name", "minimum_version", "valid_version", "invalid_version"),
    [
        ("policy", "2.6", "2.6", "2.5"),
        ("context", "2.8", "2.8", "2.7"),
        ("cost", "2.9", "2.9", "2.8"),
        ("listSize", "2.9", "2.9", "2.8"),
    ],
)
def test_directive_version_validation(
    directive_name: str,
    minimum_version: str,
    valid_version: str,
    invalid_version: str,
):
    """Test that directives validate their minimum federation version requirement"""

    # Create type with directive based on directive name
    if directive_name == "policy":

        @strawberry.federation.type
        class ProductPolicy:
            upc: str
            name: str = strawberry.federation.field(
                directives=[Policy(policies=[["admin"]])]
            )

        @strawberry.type
        class QueryPolicy:
            product: ProductPolicy

        query_type = QueryPolicy

    elif directive_name == "context":

        @strawberry.federation.type(directives=[Context(name="userContext")])
        class UserContext:
            id: strawberry.ID
            name: str

        @strawberry.type
        class QueryContext:
            user: UserContext

        query_type = QueryContext

    elif directive_name == "cost":

        @strawberry.federation.type
        class ProductCost:
            upc: str
            name: str = strawberry.federation.field(directives=[Cost(weight=10)])

        @strawberry.type
        class QueryCost:
            product: ProductCost

        query_type = QueryCost

    else:  # listSize

        @strawberry.federation.type
        class ProductListSize:
            upc: str
            friends: list[str] = strawberry.federation.field(
                directives=[
                    ListSize(
                        assumed_size=100,
                        slicing_arguments=None,
                        sized_fields=None,
                    )
                ]
            )

        @strawberry.type
        class QueryListSize:
            product: ProductListSize

        query_type = QueryListSize

    # Should work with valid version
    schema = strawberry.federation.Schema(
        query=query_type,
        federation_version=valid_version,  # type: ignore
    )
    assert schema is not None

    # Should fail with invalid version
    escaped_version = minimum_version.replace(".", r"\.")
    expected_error = (
        f"Directive @{directive_name} requires federation version "
        f"v{escaped_version} or higher"
    )
    with pytest.raises(ValueError, match=expected_error):
        strawberry.federation.Schema(
            query=query_type,
            federation_version=invalid_version,  # type: ignore
        )


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
        schema = strawberry.federation.Schema(query=Query, federation_version=version)  # type: ignore
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
