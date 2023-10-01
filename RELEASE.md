Release type: patch

This release adds a new private hook in our HTTP views, it is called
`_handle_errors` and it is meant to be used by Sentry (or other integrations)
to handle errors without having to patch methods that could be overridden
by the users
