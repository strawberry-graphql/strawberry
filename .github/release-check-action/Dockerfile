FROM docker.io/python:3.8-alpine

RUN pip install httpx==0.7.*

COPY . /action

ENTRYPOINT ["python", "/action/check.py"]
