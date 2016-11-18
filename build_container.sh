#!/bin/bash

# Make sure that DOCKER_HOST_URI is set in your environment, or
# you change this to the URI of the HOST you are using.
docker build -t serverless/actor --build-arg DOCKER_HOST_URI=${DOCKER_HOST} .
