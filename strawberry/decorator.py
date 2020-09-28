import functools

from .resolvers import get_resolver_arguments
from .utils.inspect import get_func_args


def make_strawberry_decorator(func):
    def decorator(resolver):
        if hasattr(resolver, "_field_definition"):
            raise Exception("Can't apply decorator after strawberry.field")  # TODO

        function_args = get_func_args(resolver)

        @functools.wraps(resolver)
        def wrapped_resolver(source, info, **kwargs):
            def wrapped(**kwargs):
                # If resolver is another strawberry decorator then pass all the
                # arguments to it
                if getattr(resolver, "_strawberry_decorator", False):
                    return resolver(source, info, **kwargs)

                args, extra_kwargs = get_resolver_arguments(function_args, source, info)
                return resolver(*args, **extra_kwargs, **kwargs)

            # Call the decorator body with the original set of kwargs so that it
            # has the opportunity to modify them
            return func(wrapped, source, info=info, **kwargs)

        wrapped_resolver._strawberry_decorator = True

        return wrapped_resolver

    return decorator
