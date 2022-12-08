Release type: minor

This release updates all the HTTP integration and adds a new method called
`encode_json` that allows to customize the encoding of the JSON response. By
default we use `json.dumps` but you can override this method to use a different
encoder.

It also deprecates `json_encoder` and `json_dumps_params` in the Django and
Sanic views, `encode_json` should be used instead.
