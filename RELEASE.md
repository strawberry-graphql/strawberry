Release type: patch

This release fixes an `InvalidStateError` crash in the DataLoader when a batch
load function raises an exception and some futures in the batch have already been
cancelled (e.g. due to client disconnection).

The error handler in `dispatch_batch` now skips cancelled futures before calling
`set_exception`, matching the guard that already exists in the success path
(added in #2339).
