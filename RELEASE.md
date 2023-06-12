Release type: minor

This release improves the ﻿`relay.NodeID` annotation check by delaying it until after class initialization. This resolves issues with evaluating type annotations before they are fully defined and enables integrations to inject code for it in the type.
