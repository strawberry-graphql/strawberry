Release type: minor

This release does some internal refactoring of the HTTP views, hopefully it
doesn't affect anyone. It mostly changes the status codes returned in case of
errors (e.g. bad JSON, missing queries and so on).

It also improves the testing, and adds an entirely new test suite for the HTTP
views, this means in future we'll be able to keep all the HTTP views in sync
feature-wise.
