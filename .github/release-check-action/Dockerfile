FROM python:3.7-alpine

RUN pip install httpx==0.7.*

COPY . /action

ENTRYPOINT ["python", "/action/check.py"]
