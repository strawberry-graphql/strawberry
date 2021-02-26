FROM python:3.10-rc-buster

RUN useradd -ms /bin/bash vscode
USER vscode

ENV PATH="/home/vscode/.local/bin:/home/vscode/.poetry/bin:$PATH"

RUN pip install --upgrade pip
RUN pip install pre-commit

RUN pip install poetry
RUN poetry config virtualenvs.in-project true
