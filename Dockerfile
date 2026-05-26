# Use Node 22 (LTS) or higher
FROM node:22

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for Python management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uv

# Install the correct pi coding agent
RUN npm install -g @earendil-works/pi-coding-agent

WORKDIR /workspace
CMD ["sleep", "infinity"]


