Release type: patch

This release addresses an issue in Django's GraphQLView. Previously, variables were consumed too early when overriding the template, leading to a syntax error in the JavaScript code.
