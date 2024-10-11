# Running the UBA Service

NB: The preferred way to run the UBA Service is via the provided Docker Compose file at the top level as this starts all dependencies. 

### 1) Build The Docker Image
To build the docker image associated with the service run the following comand in the project directory.
```bash
$ ./build.sh
```
This builds the Docker image `uba_service`.
### 2) Add the Configuration
Follow the steps in the [Getting_started.md](docs/Getting_started.md) to keys to the config files.

### 3) Run the Financing Service 
The UBA service requires the Financing Service to fund BSV transactions. 

This can be run via Docker.  NB: a client key is required in the financing data config file (see [Getting_started.md](docs/Getting_started.md) for more details)

Run the service from the top level directory using this command:
```
docker run --name financing_service \
  -p 8070:8070 \
  -v $(pwd)/data/financing-service.toml:/app/bin/data/financing-service.toml \
  --network uba_network \
  nchain/rnd-prototyping-financing-service:v1.2 \
  /app/bin/financing-service-rust
  ```


### 3) To Run the Image
To start the Docker container:
```bash
$ ./run.sh
```

At the prompt, run
```python3 main.py```

Note that if you are on a Windows platform you may need to use the following command:
```bash
$ winpty ./run.sh
```

## Swagger API
The Swagger API should be visible at 

http://127.0.0.1:8040/docs


