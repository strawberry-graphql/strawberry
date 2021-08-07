from typing import List

import httpx


def get_changed_files(base: str, head: str) -> List[str]:
    url = (
        "https://api.github.com/repos/strawberry-graphql/strawberry/compare/"
        f"{base}...{head}"
    )

    response = httpx.get(
        url,
        timeout=120,
    )
    response.raise_for_status()

    response_data = response.json()
    changed_files = []
    for changed_file in response_data["files"]:
        changed_files.append(changed_file["filename"])

    return changed_files
