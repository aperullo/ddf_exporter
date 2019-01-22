FROM python:3.6-alpine

RUN pip install prometheus_client requests

Env CA_CERT_PATH /cacerts
RUN mkdir /cacerts

ADD . /usr/src/app
WORKDIR /usr/src/app

CMD ["python", "ddf_exporter.py"]