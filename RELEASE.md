Release type: patch

This release fixes an issue in the previous release where requests using query params did not support passing variable values. Variables passed by query params are now parsed from a string to a dictionary.
