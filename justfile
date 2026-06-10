# Default recipe to list all available commands
set export
UID := `id -u`
GID := `id -g`

default:
    @just -l

# Bring the entire stack up in detached mode
up:
    @docker compose up -d --build

# Bring the entire stack down
down:
    @docker compose down

# Enter the dev container with a bash shell
vibe:
    @docker compose exec dev bash

# Start the backend server as a background process routing to Docker stdout
start-backend:
    @docker compose exec dev bash -c """cd /backend && uv sync && uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload > /proc/1/fd/1 2>&1 &"""
    @echo "Backend server started with uv. Stream logs with 'just logs'"


# Start the frontend server as a background process routing to Docker stdout
start-frontend:
    @docker compose exec -d dev bash -c \
    'cd /workspace/frontend && npm run dev -- --host 0.0.0.0 --port 5173 > /proc/1/fd/1 2>&1 &'
    @echo "Frontend server started. Stream logs with 'just logs'"

# Start both backend and frontend servers
start:
    @just start-backend
    @just start-frontend

logs:
    @docker compose logs -f dev


# Alias for 'vibe' to get into the pi-dev container
pi: vibe
