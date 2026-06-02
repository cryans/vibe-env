"I am setting up a nested infrastructure subproject within my current repository at dev-infra/. Please generate the following:

Infrastructure Configuration (dev-infra/docker-compose.yml):

Service: minio (using minio/minio:latest).

Port mapping: 9000:9000 (API) and 9001:9001 (Console).

Volume: C:/projects/data:/data (Ensure it handles the Windows host path correctly for WSL2).

Environment: Reference an .env file for MINIO_ROOT_USER and MINIO_ROOT_PASSWORD.

Network: Attach to an external network named dev-network.

Environment File (dev-infra/.env):

Create a template file containing MINIO_ROOT_USER and MINIO_ROOT_PASSWORD.

Automation (dev-infra/justfile):

setup-network: Runs docker network create dev-network || true.

up: Runs docker compose up -d.

down: Runs docker compose down.

logs: Runs docker compose logs -f.

default: Lists these commands using just --list.

Infrastructure Manual (dev-infra/README.md):

Explain the workflow: run just setup-network then just up.

Document console access at http://localhost:9001.

Include a 'Verify Connectivity' section with this curl command for a public/read-only health check:
curl -I http://localhost:9000/minio/health/live"

