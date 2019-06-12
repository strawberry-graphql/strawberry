from django.shortcuts import render
from django.views.generic import View


class GraphQLPlaygroundView(View):
    def get(self, request, *args, **kwargs):
        return render(
            request,
            "graphql/playground.html",
            {"REQUEST_PATH": request.get_full_path()},
        )
