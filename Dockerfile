# Use Python 3.12 slim image for better compatibility
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_TRUSTED_HOST="pypi.org pypi.python.org files.pythonhosted.org"

# Create non-root user for security
RUN groupadd -r mcp && useradd -r -g mcp mcp

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Install the package and its dependencies
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -e .

# Change ownership to non-root user
RUN chown -R mcp:mcp /app

# Switch to non-root user
USER mcp

# Create directory for configuration files
RUN mkdir -p /app/data

# Set the default command
CMD ["openapi-mcp-proxy"]

# Expose any necessary information
LABEL name="openapi-mcp-proxy" \
      version="0.1.0" \
      description="MCP Server for OpenAPI Schema Exploration" \
      maintainer="OpenAPI MCP Proxy Contributors"