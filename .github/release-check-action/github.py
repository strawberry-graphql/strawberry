import typing
from urllib.parse import urljoin

import httpx
from config import GITHUB_TOKEN
from release import ReleaseInfo


SIGNATURE = "<!-- action-check: release-file -->"


def is_release_check_comment(comment: dict) -> bool:
    return (
        comment["user"]["login"] in ["github-actions[bot]", "botberry"]
        and SIGNATURE in comment["body"]
    )


def get_comments_link(github_event_data: dict) -> str:
    return github_event_data["pull_request"]["_links"]["comments"]["href"]


def get_labels_link(github_event_data: dict) -> str:
    return urljoin(github_event_data["pull_request"]["issue_url"] + "/", "labels")


def get_comments(github_event_data: dict) -> typing.List[dict]:
    comments_link = get_comments_link(github_event_data)

    comments_request = httpx.get(comments_link)

    return comments_request.json()


def add_or_edit_comment(github_event_data: dict, comment: str):
    current_comments = get_comments(github_event_data)

    previous_comment = next(
        (comment for comment in current_comments if is_release_check_comment(comment)),
        None,
    )

    method = httpx.patch if previous_comment else httpx.post
    url = (
        previous_comment["url"]
        if previous_comment
        else get_comments_link(github_event_data)
    )

    request = method(
        url,
        headers={"Authorization": f"token {GITHUB_TOKEN}"},
        json={"body": comment + SIGNATURE},
    )

    if request.status_code >= 400:
        print(request.text)
        print(request.status_code)


def update_labels(github_event_data: dict, release_info: typing.Optional[ReleaseInfo]):
    labels_to_add = {"bot:has-release-file"}
    labels_to_remove: typing.Set[str] = set()

    new_release_label = None

    if release_info is None:
        labels_to_remove = labels_to_add
        labels_to_add = set()
    else:
        new_release_label = f"bot:release-type-{release_info.change_type.value}"
        labels_to_add.add(new_release_label)

    labels_url = get_labels_link(github_event_data)

    current_labels_url_by_name = {
        label["name"]: label["url"]
        for label in github_event_data["pull_request"]["labels"]
    }

    current_labels = set(current_labels_url_by_name.keys())

    release_labels_to_remove = [
        label
        for label in current_labels
        if label.startswith("bot:release-type-") and label != new_release_label
    ]
    labels_to_remove.update(release_labels_to_remove)

    print("current_labels", current_labels, "labels_to_remove", labels_to_remove)

    if not current_labels.issuperset(labels_to_add):
        request = httpx.post(
            labels_url,
            headers={"Authorization": f"token {GITHUB_TOKEN}"},
            json={"labels": list(labels_to_add)},
        )

        if request.status_code >= 400:
            print(request.text)
            print(request.status_code)

    if current_labels.issuperset(labels_to_remove):
        for label in labels_to_remove:
            request = httpx.delete(
                current_labels_url_by_name[label],
                headers={"Authorization": f"token {GITHUB_TOKEN}"},
            )

            if request.status_code >= 400:
                print(request.text)
                print(request.status_code)
