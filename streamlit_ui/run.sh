#!/bin/bash

# Start container
docker run -it \
    --name uba_ui  \
    --network uba_network \
    -v ./src:/app/src \
    -p 8501:8501  \
    --rm \
    streamlit_ui \
    $1

