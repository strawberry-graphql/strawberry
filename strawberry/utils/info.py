from typing import List

from graphql import GraphQLResolveInfo


def get_path_from_info(info: GraphQLResolveInfo) -> List[str]:
    path = info.path
    elements = []

    while path:
        elements.append(path.key)
        path = path.prev

    return elements[::-1]
