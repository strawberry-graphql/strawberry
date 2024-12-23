import json
from inspect import isawaitable
from typing import Any

import strawberry
from strawberry.extensions import DisableValidation, ParserCache
from strawberry.extensions.base_extension import SchemaExtension


@strawberry.type
class User:
    id: strawberry.ID
    name: str

    @strawberry.field
    @staticmethod
    async def articles(root, info) -> list["Article"]:
        return list(
            Article(id=strawberry.ID(str(i)), title=f"Article {i}") for i in range(10)
        )


@strawberry.type
class Article:
    id: strawberry.ID
    title: str


@strawberry.type
class Query:
    @strawberry.field
    @staticmethod
    async def users(root, info) -> list[User]:
        return list(
            User(id=strawberry.ID(str(i)), name=f"User {i}") for i in range(5_000)
        )

    @strawberry.field
    @staticmethod
    async def articles(root, info) -> list[Article]:
        return list(
            Article(id=strawberry.ID(str(i)), title=f"Article {i}")
            for i in range(5_000)
        )


class TestExtension(SchemaExtension):
    async def resolve(
        self,
        _next: Any,
        root: Any,
        info: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        result = _next(root, info, *args, **kwargs)

        if isawaitable(result):
            result = await result

        return result


class NoResolveExtension(SchemaExtension):
    pass


async def _original_execution(schema) -> Any:
    query = """
        {
            users {
                id
                name
                articles { id title }
            }
            articles { id title }
        }
    """

    result = await schema.execute(query)

    return result.data


async def _jitted_execution() -> Any:
    extension = TestExtension()

    users = await extension.resolve(Query.users, None, None)

    results = {"users": [], "articles": []}

    for user in users:
        next_id = lambda *args: user.id
        next_name = lambda *args: user.name

        name = await extension.resolve(next_name, user, None)
        id = await extension.resolve(next_id, user, None)

        articles = await extension.resolve(user.articles, user, None)

        user = {"id": id, "name": name, "articles": []}

        for article in articles:
            next_id = lambda *args: article.id
            next_title = lambda *args: article.title

            id = await extension.resolve(next_id, article, None)
            title = await extension.resolve(next_title, article, None)

            user["articles"].append({"id": id, "title": title})

        results["users"].append(user)

    articles = await extension.resolve(Query.articles, None, None)

    for article in articles:
        next_id = lambda *args: article.id
        next_title = lambda *args: article.title

        id = await extension.resolve(next_id, article, None)
        title = await extension.resolve(next_title, article, None)

        results["articles"].append({"id": id, "title": title})

    return results


schema = strawberry.Schema(
    query=Query, extensions=[DisableValidation(), TestExtension(), ParserCache()]
)
schema_with_extension_and_parser_cache = strawberry.Schema(
    query=Query, extensions=[DisableValidation(), TestExtension()]
)
schema_without_extension = strawberry.Schema(
    query=Query, extensions=[DisableValidation(), ParserCache()]
)
schema_with_no_resolve_extension = strawberry.Schema(
    query=Query, extensions=[NoResolveExtension(), DisableValidation(), ParserCache()]
)

extensions_combinations = [
    # [DisableValidation(), ParserCache(), NoResolveExtension()],
    [DisableValidation(), ParserCache(), TestExtension()],
    # [DisableValidation(), TestExtension()],
    # [DisableValidation(), ParserCache()],
    # [DisableValidation()],
    # [ParserCache()],
]


async def bench():
    import time

    from tabulate import tabulate

    def _get_title(schema):
        return " + ".join(
            extension.__class__.__name__ for extension in schema.extensions
        )

    schemas = [
        strawberry.Schema(query=Query, extensions=extensions)
        for extensions in extensions_combinations
    ]

    # Warmup

    for schema in schemas:
        print(
            "Warming up...",
            _get_title(schema),
        )

        await _original_execution(schema)

    await _jitted_execution()

    print()

    results = []

    for schema in schemas:
        print("Benchmarking...", _get_title(schema))

        start = time.time()
        result = await _original_execution(schema)
        original_time = time.time() - start

        title = _get_title(schema)
        results.append((title, original_time))

    # jitted

    print("Benchmarking...", "JIT")

    start = time.time()
    jit_result = await _jitted_execution()
    jit_time = time.time() - start

    results.append(("JIT", jit_time))

    if result != jit_result:
        import pathlib

        pathlib.Path("a.json").write_text(json.dumps(result, indent=4))
        pathlib.Path("b.json").write_text(json.dumps(jit_result, indent=4))
        raise ValueError("Results do not match!")

    table_data = []

    results = sorted(results, key=lambda x: -x[1])
    baseline_time = results[0][1]

    for title, duration in results:
        table_data.append(
            (
                title,
                f"{duration:.4f}s",
                f"{baseline_time/duration:.2f}x",
            )
        )

    # Print formatted table
    print()
    print("Performance Comparison:")
    print(
        tabulate(
            table_data,
            headers=["Version", "Time", "Speed Ratio"],
            tablefmt="fancy_grid",
        )
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(bench())
