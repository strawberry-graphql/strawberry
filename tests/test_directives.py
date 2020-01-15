import strawberry
from graphql import DirectiveLocation, GraphQLDirective


def test_declaring_executable_directive():
    @strawberry.directive(
        locations=[DirectiveLocation.FIELD], description="Sample description"
    )
    def uppercase(value: str) -> str:
        return value.upper()

    assert uppercase.directive.__class__ == GraphQLDirective
    assert uppercase.directive.name == "uppercase"
    assert uppercase.directive.description == "Sample description"
    assert uppercase.directive.args == {}
