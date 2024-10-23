#!/bin/bash

# Name of the Docker image
IMAGE_NAME="image_loader_app"

# Step 1: Build the Docker image
echo "Building the Docker image..."
docker build -t $IMAGE_NAME .
