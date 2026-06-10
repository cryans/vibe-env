# Use an official Node.js 22 image as a base
FROM node:22-slim

# Set environment variables
ENV PYTHON_VERSION=3.11
ENV PATH="/root/.local/bin:${PATH}"

# Install system dependencies, including python, pip, sqlite3, and other tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python${PYTHON_VERSION} \
    python3-pip \
    sqlite3 \
    curl \
    vim \
    tree \
    ripgrep \
    fd-find \
    procps \
    sudo

#\
#    && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/python3 /usr/bin/python

# Install uv by downloading the binary directly to /usr/local/bin
# RUN curl -LsSf https://astral.sh/uv/install.sh | env BIN_DIR=/usr/local/bin sh
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/usr/local/bin" sh

# Install just
RUN curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/local/bin

# Fix: Ensure the path is explicitly set for the shell
#ENV PATH="/usr/local/bin:${PATH}"

RUN npm install -g @earendil-works/pi-coding-agent

ARG USER_ID=1000
ARG GROUP_ID=1000

#RUN if ! getent group ${GROUP_ID}; then groupadd -g ${GROUP_ID} devuser; fi && \
#    if ! getent passwd ${USER_ID}; then useradd -u ${USER_ID} -g devuser -m devuser; fi

RUN if getent passwd ${USER_ID}; then \
        usermod -l devuser -d /home/devuser -m node && \
        groupmod -n devuser node; \
    else \
        groupadd -g ${GROUP_ID} devuser && \
        useradd -u ${USER_ID} -g devuser -m -s /bin/bash devuser; \
    fi && \
    usermod -aG sudo devuser && \
    echo "devuser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Change ownership of the directories so devuser has full access
#RUN chown -R ${USER_ID}:${GROUP_ID} /root/.local/bin /usr/local/bin

# Ensure devuser's PATH includes the location where you installed the tools
ENV PATH="/root/.local/bin:/usr/local/bin:${PATH}"

# Add devuser as a sudo-er
##RUN usermod -aG sudo devuser
##RUN echo "devuser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER devuser

# Set up the workspace
WORKDIR /workspace

# Keep the container running
CMD ["sleep", "infinity"]
