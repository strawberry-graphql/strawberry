Release type: patch

This release improves the performance of rich exceptions on custom scalars
by changing how frames are fetched from the call stack.
Before the change, custom scalars were using a CPU intensive call to the
`inspect` module to fetch frame info which could lead to serious CPU spikes.
