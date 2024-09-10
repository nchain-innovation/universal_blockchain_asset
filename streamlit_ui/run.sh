#!/bin/bash

# Start container
docker run -it \
    --name commitment_ui  \
    --network commitment_network \
    -v ./src:/app/src \
    -p 8501:8501  \
    --rm \
    streamlit_ui \
    $1

