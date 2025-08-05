# OpenAPI MCP Server

An MCP server that provides tools for exploring large OpenAPI schemas without loading entire schemas into LLM context. Perfect for discovering and analyzing endpoints, data models, and API structure efficiently.

## Features

- **API Configuration Management**: Save and manage multiple API configurations with authentication headers if needed
- **Schema Caching**: Automatic caching of OpenAPI schemas to avoid repeated downloads
- **Endpoint Discovery**: List and search through API endpoints
- **Pagination Support**: Handle large APIs efficiently with configurable page sizes
- **Detailed Schema Exploration**: Get comprehensive information about endpoints and data models
- **Efficient Context Usage**: Explore large APIs without overwhelming LLM context windows

<div align="center">

![Demo](demonstration.gif)

</div>

## Prerequisites

- **Python 3.12+**: The server requires Python 3.12 or later
- **uv**: Fast Python package installer and resolver ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- **MCP-compatible client**: Claude Desktop, Claude Code CLI, Cursor, or other MCP clients

### Installing uv

**macOS/Linux:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Using pip:**

```bash
pip install uv
```

## Installation

The OpenAPI MCP Proxy can be installed in several ways for maximum convenience:

### 🐳 Docker (Recommended for Quick Start)

**Using Docker directly:**

```bash
# Run directly from Docker Hub (when published)
docker run -it --rm -v $(pwd)/data:/app/data ghcr.io/nyudenkov/openapi-mcp-proxy:latest

# Or build locally
git clone https://github.com/nyudenkov/openapi-mcp-proxy.git
cd openapi-mcp-proxy
docker build -t openapi-mcp-proxy .
docker run -it --rm -v $(pwd)/data:/app/data openapi-mcp-proxy
```

**Using Docker Compose:**

```bash
git clone https://github.com/nyudenkov/openapi-mcp-proxy.git
cd openapi-mcp-proxy
docker-compose up
```

The Docker setup automatically creates a persistent volume for your API configurations.

### ⚡ uvx (Recommended for Python Users)

**Install and run with uvx (requires Python 3.12+):**

```bash
# Install uvx if you haven't already
pip install uvx

# Run directly without installing
uvx --from git+https://github.com/nyudenkov/openapi-mcp-proxy.git openapi-mcp-proxy

# Or install as a tool for repeated use
uvx install git+https://github.com/nyudenkov/openapi-mcp-proxy.git
openapi-mcp-proxy
```

### 🎯 Desktop Extension (DXT)

**For Claude Desktop and other MCP-compatible applications:**

This project includes a Desktop Extension (DXT) package for single-click installation in MCP-compatible applications:

1. **Download the DXT package** (when available) or create it from source:
   ```bash
   # Install the DXT CLI tool
   npm install -g @anthropic-ai/dxt
   
   # Clone this repository
   git clone https://github.com/nyudenkov/openapi-mcp-proxy.git
   cd openapi-mcp-proxy
   
   # Create the DXT package
   dxt pack
   ```

2. **Install in Claude Desktop**: Open the generated `.dxt` file with Claude Desktop for automatic installation

3. **Manual configuration**: Alternatively, configure manually in Claude Desktop's settings:
   ```json
   {
     "mcpServers": {
       "openapi-mcp-proxy": {
         "command": "openapi-mcp-proxy"
       }
     }
   }
   ```

The `manifest.json` file in this repository contains the complete DXT specification for this MCP server.

### 🔧 Development Installation

**For contributors and advanced users:**

1. **Clone the repository:**

```bash
git clone https://github.com/nyudenkov/openapi-mcp-proxy.git
cd openapi-mcp-proxy
```

2. **Install dependencies:**

```bash
uv sync
```

3. **Run in development mode:**

```bash
# Using uv
uv run python main.py

# Or install in development mode
uv pip install -e .
openapi-mcp-proxy
```

### 📦 pip Installation

**Traditional pip installation:**

```bash
# From source
pip install git+https://github.com/nyudenkov/openapi-mcp-proxy.git

# Run after installation
openapi-mcp-proxy
```

## Usage

### Running the Server

The server can be run in multiple ways depending on your installation method:

**If installed via uvx or pip:**
```bash
openapi-mcp-proxy
```

**If using Docker:**
```bash
docker run -it --rm -v $(pwd)/data:/app/data openapi-mcp-proxy
```

**If running from source:**
```bash
uv run python main.py
```

The server runs using stdio and integrates with MCP-compatible LLM clients like Claude Desktop.

### Available Tools

#### API Management

- **`add_api`**: Add a new API configuration with name, URL and optional description
  - `name` (required): Short name for the API
  - `url` (required): URL to the OpenAPI scheme (yaml/json)
  - `description` (optional): Optional description
  - `headers` (optional): Optional HTTP headers for authentication (e.g., {'Authorization': 'Bearer token', 'X-API-Key': 'key'})

- **`list_saved_apis`**: List all saved API configurations

- **`remove_api`**: Remove a saved API configuration

#### API Exploration

- **`get_api_info`**: Get general information about an API

- **`list_endpoints`**: List all endpoints in an API with pagination and filtering

- **`search_endpoints`**: Search endpoints by query with pagination and filtering

- **`get_endpoint_details`**: Get detailed information about a specific endpoint

- **`list_models`**: List all data models in an API with pagination and filtering

- **`get_model_schema`**: Get detailed schema for a specific model

### Tools Capabilities

#### Pagination

All listing tools (`list_endpoints`, `search_endpoints`, `list_models`) support pagination to handle large APIs efficiently:

- Default page size: 50 items
- Responses include navigation information (current page, total pages, has next/previous)

#### Advanced Filtering

Tools are capable to filter results to find exactly what you need:

**Endpoint Filtering:**

- HTTP methods (GET, POST, PUT, DELETE, etc.)
- Tags (include/exclude specific tags)
- Authentication requirements
- Deprecation status

**Model Filtering:**

- Model types (object, array, string, etc.)
- Property count (min/max number of properties)
- Required fields presence
- Tags (include/exclude specific tags)

## Configuration

API configurations are automatically saved to `api_configs.json` in the working directory. The file structure:

```json
{
  "apis": {
    "api-name": {
      "name": "some-project-local-backend",
      "url": "http://127.0.0.1:8000/openapi.json",
      "description": "Optional description for some cool project local backend scheme"
    },
    "api-name": {
      "name": "stripe-yaml",
      "url": "https://raw.githubusercontent.com/stripe/openapi/refs/heads/master/openapi/spec3.yaml",
      "description": "Stripe YAML OpenAPI scheme"
    }
  }
}
```
