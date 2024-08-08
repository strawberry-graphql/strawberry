import graphql
from packaging.version import Version

IS_GQL_32 = Version("3.3") >= Version(graphql.__version__)
