import strawberry


def test_base_context():
    from strawberry.litestar import BaseContext

    base_context = BaseContext()
    assert base_context.request is None


def test_with_class_context_getter():
    from litestar import Litestar
    from litestar.di import Provide
    from litestar.testing import TestClient
    from strawberry.litestar import BaseContext, make_graphql_controller

    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self, info: strawberry.Info) -> str:
            assert isinstance(info.context, CustomContext)
            assert info.context.request is not None
            assert info.context.strawberry == "rocks"
            return "abc"

    class CustomContext(BaseContext):
        strawberry: str

    def custom_context_dependency() -> CustomContext:
        return CustomContext(strawberry="rocks")

    async def get_context(custom_context_dependency: CustomContext):
        return custom_context_dependency

    schema = strawberry.Schema(query=Query)
    graphql_controller = make_graphql_controller(
        path="/graphql", schema=schema, context_getter=get_context
    )
    app = Litestar(
        route_handlers=[graphql_controller],
        dependencies={
            "custom_context_dependency": Provide(
                custom_context_dependency, sync_to_thread=True
            )
        },
    )

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}


def test_with_dict_context_getter():
    from litestar import Litestar
    from litestar.di import Provide
    from litestar.testing import TestClient
    from strawberry.litestar import make_graphql_controller

    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self, info: strawberry.Info) -> str:
            assert isinstance(info.context, dict)
            assert info.context.get("request") is not None
            assert info.context.get("strawberry") == "rocks"
            return "abc"

    def custom_context_dependency() -> str:
        return "rocks"

    async def get_context(custom_context_dependency: str) -> dict[str, str]:
        return {"strawberry": custom_context_dependency}

    schema = strawberry.Schema(query=Query)
    graphql_controller = make_graphql_controller(
        path="/graphql", schema=schema, context_getter=get_context
    )
    app = Litestar(
        route_handlers=[graphql_controller],
        dependencies={
            "custom_context_dependency": Provide(
                custom_context_dependency, sync_to_thread=True
            )
        },
    )
    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}


def test_without_context_getter():
    from litestar import Litestar
    from litestar.testing import TestClient
    from strawberry.litestar import make_graphql_controller

    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self, info: strawberry.Info) -> str:
            assert isinstance(info.context, dict)
            assert info.context.get("request") is not None
            assert info.context.get("strawberry") is None
            return "abc"

    schema = strawberry.Schema(query=Query)
    graphql_controller = make_graphql_controller(
        path="/graphql", schema=schema, context_getter=None
    )
    app = Litestar(route_handlers=[graphql_controller])
    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}


def test_with_invalid_context_getter():
    from litestar import Litestar
    from litestar.di import Provide
    from litestar.testing import TestClient
    from strawberry.litestar import make_graphql_controller

    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self, info: strawberry.Info) -> str:
            assert info.context.get("request") is not None
            assert info.context.get("strawberry") is None
            return "abc"

    def custom_context_dependency() -> str:
        return "rocks"

    async def get_context(custom_context_dependency: str) -> str:
        return custom_context_dependency

    schema = strawberry.Schema(query=Query)
    graphql_controller = make_graphql_controller(
        path="/graphql", schema=schema, context_getter=get_context
    )
    app = Litestar(
        route_handlers=[graphql_controller],
        dependencies={
            "custom_context_dependency": Provide(
                custom_context_dependency, sync_to_thread=True
            )
        },
    )
    test_client = TestClient(app, raise_server_exceptions=True)
    # TODO: test exception message
    # assert starlite.exceptions.http_exceptions.InternalServerException is raised
    # with pytest.raises(
    #     InternalServerException,
    #     r"A dependency failed validation for POST .*"
    # ),
    # ):
    response = test_client.post("/graphql", json={"query": "{ abc }"})
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal Server Error"


def test_custom_context():
    from litestar.testing import TestClient
    from tests.litestar.app import create_app

    @strawberry.type
    class Query:
        @strawberry.field
        def custom_context_value(self, info: strawberry.Info) -> str:
            return info.context["custom_value"]

    schema = strawberry.Schema(query=Query)
    app = create_app(schema=schema)

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ customContextValue }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"customContextValue": "Hi!"}}


def test_can_set_background_task():
    from litestar.testing import TestClient
    from tests.litestar.app import create_app

    task_complete = False

    async def task():
        nonlocal task_complete
        task_complete = True

    @strawberry.type
    class Query:
        @strawberry.field
        def something(self, info: strawberry.Info) -> str:
            response = info.context["response"]
            response.background.tasks.append(task)
            return "foo"

    schema = strawberry.Schema(query=Query)
    app = create_app(schema=schema)

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ something }"})

    assert response.json() == {"data": {"something": "foo"}}
    assert task_complete
