FROM python:3.7-alpine

RUN pip install httpx

COPY . /action

ENTRYPOINT ["python", "/action/check.py"]