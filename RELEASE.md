Release type: minor

This release unifies the format of HTTP error response bodies across all HTTP
view integrations. Previously, the Chalice integration used a custom JSON body
response different from the plain string used by other integrations. Now, all
integrations will return a plain string for HTTP error responses.
