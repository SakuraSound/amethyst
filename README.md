# Whisk Actor
#### Summary
The primary server for running actions and returning output to users. Supports both REST interface (GET, POST, PUT), and WebSockets. The action server pulls actions from the docker image repo (registry), using an image_id, and launches it on the docker host. For REST calls, stdout/stderr are aggregated until completion, and then sent out to the user. For Websockets, the action server will relay output as retrieved and send to those listening on that action.


#### Requirements
###### Python
Codebase runs using Python 3.5.1, and makes use of AsyncIO. The Python dependencies are listed in requirements.txt.

###### Docker
Considering that our actions are encapsulated as Docker images, this is necessary. Having access to TLS certs is needed for the action server to communicate with the Docker host. If docker-machine is installed, then you should have environment variables `DOCKER_CERT_PATH`, `DOCKER_HOST`, and `DOCKER_TLS_VERIFY`. Read more about how this is done [here](https://docker-py.readthedocs.org/en/stable/machine/).


#### How to Run
Make sure docker is running.

###### Actor running inside container
1. Create a cert volume in docker.

    `docker volume create --name cert-volume`

2. Inspect the volume, and get the mount point of that volume

    `docker volume inspect cert-volume`

3. Using the `DOCKER_CERT_PATH` for the cert location, copy the certs into the volume (need ca, cert, and key). If using docker-machine, you will need to ssh into the machine to do this.

4. Build the image using the Dockerfile.

    Either use the build_container script provided, or do it using docker.

5. Run container, mounting the cert-volume to the  directory given in Dockerfile.

    Use run_container script or do it using docker.




#### TODO:
* Create concept of user
* Communication between whisk_bouncer for authentication/authorizing access
* Create tests
