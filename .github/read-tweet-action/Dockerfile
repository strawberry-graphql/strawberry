FROM python:3.9-alpine

RUN pip install markdown==3.3.4 beautifulsoup4==4.9.3

COPY . /action

ENTRYPOINT ["python", "/action/read.py"]
