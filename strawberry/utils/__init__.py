import graphql
from packaging.version import Version

IS_GQL_33 = Version(graphql.__version__) >= Version("3.3.0a")
IS_GQL_32 = not IS_GQL_33
