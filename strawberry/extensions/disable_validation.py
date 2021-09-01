from strawberry.extensions.base_extension import Extension


def DisableValidation():
    class _DisableValidation(Extension):
        def on_request_start(self):
            self.execution_context.validation_rules = ()  # remove all validation_rules

    return _DisableValidation
