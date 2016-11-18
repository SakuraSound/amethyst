#!/bin/bash

docker run -itd \
           --name actor1 \
           -p 9090:9090 \
           -v cert-volume:/whisk_actor/docker/certs \
           serverless/actor
