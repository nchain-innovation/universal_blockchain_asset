#!/bin/bash

# Uses buildx to build and publish multi-architecture images

IMAGE_NAME="nchain/rnd-prototyping-uba_service:v1.0"

# docker buildx build  --no-cache --platform linux/amd64,linux/arm64 --push -t $IMAGE_NAME .
docker buildx build  --builder cloud-nchain-rndprototyping --no-cache --platform linux/amd64,linux/arm64 --push -t $IMAGE_NAME .