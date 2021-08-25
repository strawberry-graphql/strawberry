from graphql import ASTValidationRule

from strawberry.extensions.base_extension import Extension


def AddValidationRule(validation_rule: ASTValidationRule):
    class _AddValidationRule(Extension):
        def on_request_start(self):
            self.execution_context.validation_rules = (
                self.execution_context.validation_rules + (validation_rule,)
            )

    return _AddValidationRule
