import functools
from strawberry.types.fields.resolver import StrawberryResolver

from .resolvers import get_arguments
from .utils.inspect import get_func_args


def make_strawberry_decorator(func):
    def decorator(resolver):
        ##################################################################
        ### aaaaaaaaaaaaaaaaaaaa
        return StrawberryResolver(resolver, decorators=[func])

    return decorator

    ...

    # def decorator(resolver):
    #     if hasattr(resolver, "_field_definition"):
    #         raise Exception("Can't apply decorator after strawberry.field")  # TODO

    #     function_args = get_func_args(resolver)

    #     @functools.wraps(resolver)
    #     def wrapped_resolver(root, info, **kwargs):
    #         def wrapped(**kwargs):
    #             # If resolver is another strawberry decorator then pass all the
    #             # arguments to it
    #             if getattr(resolver, "_strawberry_decorator", False):
    #                 return resolver(root, info, **kwargs)

    #             breakpoint()

    #             args, kwargs = get_arguments(
    #                 function_args, kwargs=kwargs, source=root, info=info
    #             )
    #             return resolver(*args, **kwargs)

    #         # Call the decorator body with the original set of kwargs so that it
    #         # has the opportunity to modify them
    #         return func(wrapped, root, info=info, **kwargs)

    #     wrapped_resolver._strawberry_decorator = True

    #     return wrapped_resolver

    # return decorator
