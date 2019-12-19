Release type: minor

This release improves support for django and asgi integration.

It allows to use async resolvers when using django. It also
changes the status code from 400 to 200 even if there are errors
this makes it possible to still use other fields even if one 
raised an error.

