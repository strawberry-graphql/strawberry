Release type: patch

This release fixes an issue when trying to use `Annotated[strawberry.auto, ...]`
on python 3.10 or older, which got evident after the fix from 0.196.1.

Previously we were throwing the type away, since it usually is `Any`, but python
3.10 and older will validate that the first argument passed for `Annotated`
is callable (3.11+ does not do that anymore), and `StrawberryAuto` is not.

This changes it to keep that `Any`, which is also what someone would expect
when resolving the annotation using our custom `eval_type` function.
