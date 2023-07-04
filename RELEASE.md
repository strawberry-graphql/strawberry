Release type: patch

This release adds a `set_cookie` method to the `TemporalResponse` class so that the integrations Sanic, Django Channels and Chalice have a method for setting cookies.

To support multiple cookies per response, the `headers` dict in the `TemporalResponse` class was also changed. The values of the dict can (optionally) be a list of strings.
