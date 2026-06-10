# Project Setup

This project uses Docker Compose for a unified, flattened project structure. All services are orchestrated using a single `docker-compose.yml` file.

## Setup Guide

This guide assumes you are using a WSL2 environment.

### Prerequisites

*   Docker and Docker Compose installed.
*   `just` installed (for running commands).
*   A `.env` file at the root of the repository with the following variables:
    ```
    MINIO_ROOT_USER=minioadmin
    MINIO_ROOT_PASSWORD=minioadmin
    ```

### Running the Project

To start all services, run the following command in your terminal from the root of the repository:

```bash
just up
```

This command will build and start the MinIO, backend, and frontend services in detached mode.

 1. Build and Start: Run just up. This will build the new Docker image and start the dev and minio containers.
 2. Enter the Dev Shell: Run just vibe (or just pi). This will drop you into a bash shell inside the running dev container.
 3. Start Services: From inside the container (or from your host machine), run just start to kick off the backend and frontend servers.
 4. Check Logs: Use just logs-backend or just logs-frontend to tail the logs for each service without cluttering your main shell.
 5. Start Coding: Launch pi inside the dev container (just vibe then pi). It will now operate in a stable environment, use the correct model, and have all the tools it needs.

