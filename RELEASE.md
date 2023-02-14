release type: minor

Throw proper exceptions when Unions are created with invalid types

Previously, using Lazy types inside of Unions would raise unexpected, unhelpful errors.
