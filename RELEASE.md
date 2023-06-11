Release type: minor

This release changes the way we check for `relay.NodeID` annotations to be done
later instead of in class initialization. This solves problems with trying to
evaluate type annotations before they are totally defined, and also allows
integrations to inject code for it in the type.
