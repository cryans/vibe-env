# Master Orchestration
# Run the entire stack (MinIO + Backend + Frontend)
up:
    docker compose up -d

# Open your persistent dev shell
# This drops you into the pi-dev container as a sibling to your services
vibe:
    docker compose exec pi-dev bash

# View logs for all running services
logs:
    docker compose logs -f

# Bring the entire stack down
down:
    docker compose down

# Default: List all available commands
default:
    just --list

