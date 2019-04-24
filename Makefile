prepare-release:
	python scripts/prepare_release.py

create-github-release:
	python scripts/create_github_release.py

publish-changes:
	python scripts/publish_changes.py

check-has-release:
	python scripts/has_release.py

install-deploy-deps:
	pip install --user githubrelease
