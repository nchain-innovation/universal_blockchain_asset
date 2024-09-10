#!/bin/bash

DATA_DIR=$(realpath ../data)
SRC_DIR=$(realpath ./src)

# Start container
docker run -it \
    --mount type=bind,source=$SRC_DIR,target=/app/python \
    --mount type=bind,source=$DATA_DIR,target=/app/data \
    --rm commitment_service \
    bash -c "cd tests && python3 -m unittest discover"
