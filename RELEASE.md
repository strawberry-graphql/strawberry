Release type: patch

Fix template rendering for the GraphQLView, so that variables are not consumed
too early if one overrides the template using the well-known path. The symptom
is that nothing loads because `JSON.parse("")` is a syntax error.
