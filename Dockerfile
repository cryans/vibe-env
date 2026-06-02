FROM node:22

# Install system dependencies
# vim-tiny is a lightweight version of vi, use 'vim' if you prefer full features
RUN apt-get update && apt-get install -y \
    git \
    curl \
    vim \
    tree \
    && rm -rf /var/lib/apt/lists/*

# Install uv (using the official installer script for global access)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
# Ensure uv is in the path for future RUN commands
ENV PATH="/root/.local/bin:${PATH}"

RUN curl --proto '=https' --tlsv1.2 -sSf 'https://just.systems/install.sh' | bash -s -- --to /usr/local/bin

# Install the correct pi coding agent
RUN npm install -g @earendil-works/pi-coding-agent

WORKDIR /workspace
CMD ["sleep", "infinity"]
