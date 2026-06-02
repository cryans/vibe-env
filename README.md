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

## Connectivity Matrix

This table outlines how different components can connect to each other.

| Component           | Type                | Address/Port           | Notes                                     |
| :------------------ | :------------------ | :--------------------- | :---------------------------------------- |
| **Host (WSL2)**     | **Frontend**        | `http://localhost:5174`| Access the React frontend via your browser |
|                     | **Backend API**     | `http://localhost:8000`| Access the backend API directly           |
|                     | **MinIO Console**   | `http://localhost:9001`| Access the MinIO web console              |
|                     | **MinIO API**       | `http://localhost:9000`| For programmatic access                   |
| **Container**       | **Container-to-Container** |                        | Internal service communication            |
| `backend`           | `minio`             | `http://minio:9000`    | Backend connects to MinIO API             |
| `frontend`          | `minio`             | `http://minio:9000`    | Frontend connects to MinIO API            |

## Commands

The `justfile` at the root of this repository provides the following commands:

*   `just up`: Starts all services in detached mode (`docker compose up -d`).
*   `just down`: Stops and removes all services (`docker compose down`).
*   `just logs`: Follows the logs of all services (`docker compose logs -f`).
*   `just` or `just --list`: Lists all available commands.
