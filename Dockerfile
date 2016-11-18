FROM python:3.5-alpine
MAINTAINER Joir-dan Gumbs <jgumbs@us.ibm.com>

ARG DOCKER_HOST_URI

# If running in a docker container, put certs within a volume and mount from this point
ENV DOCKER_CERT_PATH /whisk_actor/docker/certs
ENV DOCKER_TLS_VERIFY 1
ENV DOCKER_HOST $DOCKER_HOST_URI

RUN apk update && apk add alpine-sdk

COPY . /whisk_actor

WORKDIR /whisk_actor

RUN pip install -r requirements.txt

EXPOSE 9090

CMD ["python", "app.py"]
