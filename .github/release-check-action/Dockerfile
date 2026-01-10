FROM docker.io/python:3.14-alpine

RUN pip install httpx

COPY . /action

ENTRYPOINT ["python", "/action/check.py"]
