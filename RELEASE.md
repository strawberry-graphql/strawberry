Release type: minor

In this release, all types of the legacy graphql-ws protocol were refactored.
The types are now much stricter and precisely model the difference between null and undefined fields.
As a result, our protocol implementation and related tests are now more robust and easier to maintain.
