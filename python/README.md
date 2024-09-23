# Python 

## Docker
Encapsulating the service in Docker removes the need to install the project dependencies on the host machine.
Only Docker is required to build and run the service and web interface.
### 1) Build The Docker Image
To build the docker image associated with the service run the following comand in the project directory.
```bash
$ ./build.sh
```
This builds the Docker image `uba_service`.
### 2) To Run the Image
To start the Docker container:
```bash
$ ./run.sh
```
Note that if you are on a Windows platform you may need to use the following command:
```bash
$ winpty ./run.sh
```

## Swagger API
The Swagger API should be visible at 

http://127.0.0.1:8040/docs


