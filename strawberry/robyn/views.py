import json

import strawberry
from robyn import jsonify


def BaseGraphQLView(schema):
    def GraphQlView(schema):
        async def get():
            return strawberry.utils.graphiql.get_graphiql_html()

        async def post(request):
            body = json.loads(bytearray(request["body"]).decode("utf-8"))
            query = body["query"]
            variables = body.get("variables", None)
            context_value = {"request": request}
            root_value = body.get("root_value", None)
            operation_name = body.get("operation_name", None)

            data = await schema.execute(
                query,
                variables,
                context_value,
                root_value,
                operation_name,
            )

            return jsonify(
                {
                    "data": (data.data),
                    **({"errors": data.errors} if data.errors else {}),
                    **({"extensions": data.extensions} if data.extensions else {}),
                }
            )

    return GraphQlView
