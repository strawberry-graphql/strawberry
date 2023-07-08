Release type: minor

Restore evaled type access in `StrawberryAnnotation`

Prior to Strawberry 192.2 the `annotation` attribute of `StrawberryAnnotation`
would return an evaluated type when possible due reserved argument parsing.
192.2 moved the responsibility of evaluating and caching results to the
`evaluate` method of `StrawberryAnnotation`. This introduced a regression when
using future annotations for any code implicitely relying on the `annotation`
attribute being an evaluated type.

To fix this regression and mimick pre-192.2 behavior, this release adds an
`annotation` property to `StrawberryAnnotation` that internally calls the
`evaluate` method. On success the evaluated type is returned. If a `NameError`
is raised due to an unresolvable annotation, the raw annotation is returned.
