from graphql.version import VersionInfo, version_info

IS_GQL_33 = version_info >= VersionInfo.from_str("3.3.0a0")
IS_GQL_32 = not IS_GQL_33

if IS_GQL_33 and version_info < VersionInfo.from_str("3.3.0a12"):
    raise ImportError(
        f"graphql-core {version_info} is not supported. "
        "Please upgrade to graphql-core >= 3.3.0a12."
    )
