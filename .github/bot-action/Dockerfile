FROM python:3.14-alpine

RUN pip install httpx==0.27.2


COPY . /action

ENTRYPOINT ["python", "/action/main.py"]
