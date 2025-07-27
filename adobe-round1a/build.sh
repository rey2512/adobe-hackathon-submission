#!/bin/bash

IMAGE_NAME="mysolutionname:latest"

echo "Building Docker image: $IMAGE_NAME"


docker build -t "$IMAGE_NAME" .

echo "Docker image built successfully!"
echo ""
echo "To run the solution using the official evaluation command format:"
echo "docker run --rm -v \$(pwd)/input:/app/input -v \$(pwd)/output:/app/output --network none $IMAGE_NAME"
echo ""
echo "Make sure to place your PDF files in the ./input directory before running."