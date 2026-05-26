default:
    @just --list

# Start the development environment
up:
    docker compose up -d

# Stop the development environment
down:
    docker compose down

# Enter the vibe
vibe:
    docker exec -it pi-vibe-env /bin/bash

# Build the project (includes fresh Docker build)
build:
    docker compose build
