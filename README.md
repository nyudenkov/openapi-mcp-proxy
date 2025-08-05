# OpenAPI MCP Server

An MCP server that provides tools for exploring large OpenAPI schemas without loading entire schemas into LLM context. Perfect for discovering and analyzing endpoints, data models, and API structure efficiently.

## Features

- **API Configuration Management**: Save and manage multiple API configurations
- **Schema Caching**: Automatic caching of OpenAPI schemas to avoid repeated downloads
- **Endpoint Discovery**: List and search through API endpoints
- **Detailed Schema Exploration**: Get comprehensive information about endpoints and data models
- **Efficient Context Usage**: Explore large APIs without overwhelming LLM context windows

## Installation

1. Clone the repository:

```bash
git clone git@github.com:nyudenkov/openapi-mcp-proxy.git
cd openapi-mcp-server
```

2. Install dependencies:

```bash
uv sync
```

## Usage

### Running the Server

```bash
uv run python main.py
```

The server runs using stdio and integrates with MCP-compatible LLM clients.

### Available Tools

#### API Management

- **`add_api`**: Add a new API configuration
- **`list_saved_apis`**: List all saved API configurations
- **`remove_api`**: Remove a saved API configuration

#### API Exploration

- **`get_api_info`**: Get general information about an API
- **`list_endpoints`**: List all endpoints in an API
- **`search_endpoints`**: Search endpoints by query
- **`get_endpoint_details`**: Get detailed endpoint information
- **`list_models`**: List all data models in an API
- **`get_model_schema`**: Get detailed schema for a specific model

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
