# AgentsTeam CLI Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY cli/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy CLI source code
COPY cli/ /app/cli/
COPY setup.py /app/

# Install the package
RUN pip install -e .

# Create directories for projects and config
RUN mkdir -p /app/projects /app/config /app/models

# Set environment variables
ENV PYTHONPATH=/app
ENV PATH="/app:$PATH"

# Default command
CMD ["agentsteam", "shell"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import cli; print('CLI is healthy')" || exit 1