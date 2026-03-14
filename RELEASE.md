Release type: patch

Fixes an issue where schema extensions (like `MaskErrors`) were bypassed during WebSocket subscriptions. The extensions' `_process_result` hooks are now properly triggered for each yielded result in both `graphql-transport-ws` and `graphql-ws` protocols, ensuring errors are correctly formatted before being sent to the client.

### Description
Fixes an issue where schema extensions (such as `MaskErrors`) were being bypassed when streaming data over WebSockets.

Previously, standard Queries and Mutations would pass their results through the extension pipeline, but Subscriptions would send raw `ExecutionResult` objects directly over the WebSocket. This caused internal/unmasked errors to leak to the client. This PR manually triggers `_process_result` on active extensions right before `send_next` and `send_data_message` dispatch the payload.

### Migration guide
No migration required.

### Types of Changes
- [ ] Core
- [x] Bugfix
- [ ] New feature
- [ ] Enhancement/optimization
- [ ] Documentation

### Checklist
- [x] My code follows the code style of this project.
- [ ] My change requires a change to the documentation.
- [x] I have read the CONTRIBUTING document.
- [x] I have added tests to cover my changes.
- [x] I have tested the changes and verified that they work and don't break anything (as well as I can manage).
