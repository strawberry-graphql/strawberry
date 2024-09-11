from graphql.version import version_info, VersionInfo

IS_GQL_33 = version_info >= VersionInfo.from_str("3.3.0a0")
IS_GQL_32 = not IS_GQL_33
