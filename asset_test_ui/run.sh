#!/bin/bash

# Name of the Docker image
IMAGE_NAME="image_loader_app"

echo "Running the Docker container..."
docker run --rm \
 --network uba_network \
 -p 8550:8550 \
 -v $(pwd)/src:/app \
 $IMAGE_NAME
