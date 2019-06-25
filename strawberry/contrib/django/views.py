# from django.http import HttpResponse, HttpResponseNotAllowed
# from django.http.response import HttpResponseBadRequest
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import View

from graphql.type.schema import GraphQLSchema


class GraphQLPlaygroundView(View):
    def get(self, request, *args, **kwargs):
        return render(
            request,
            "graphql/playground.html",
            {"REQUEST_PATH": request.get_full_path()},
        )


class GraphQLView(View):
    def __init__(self, schema=None):
        assert schema, "You must pass in a schema to GraphQLView"
        assert isinstance(
            schema, GraphQLSchema
        ), "You must pass in a valid schema to GraphQLView"

        self.schema = schema

    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, request, *args, **kwargs):
        pass
