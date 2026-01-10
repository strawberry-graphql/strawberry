FROM python:3.14-alpine

RUN pip install httpx==0.18.2


COPY . /action

ENTRYPOINT ["python", "/action/main.py"]
