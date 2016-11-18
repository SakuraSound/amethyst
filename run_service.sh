#!/bin/bash

docker service create \
                      --name action_servers \
                      --mount type=volume,src=cert-volume,dst=/whisk_actor/docker/certs \
                      -p 9090:9090 \
                      --replicas 3 \
                      serverless/actor
