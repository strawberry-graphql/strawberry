from .directive import DIRECTIVE_REGISTRY


SPECIFIED_DIRECTIVES = {"include", "skip"}


class DirectivesMiddleware:
    def resolve(self, next_, root, info, **kwargs):
        result = next_(root, info, **kwargs)

        for directive in info.field_nodes[0].directives:
            directive_name = directive.name.value

            if directive_name in SPECIFIED_DIRECTIVES:
                continue

            func = DIRECTIVE_REGISTRY.get(directive_name)

            arguments = {
                argument.name.value: argument.value.value
                for argument in directive.arguments
            }

            result = func(result, **arguments)

        return result
