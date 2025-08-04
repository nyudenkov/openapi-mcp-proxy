#!/usr/bin/env python3
"""
MCP Server for OpenAPI Schema Exploration

This server provides tools for exploring large OpenAPI schemas without loading
the entire schema into the LLM context. It offers endpoint discovery, search,
and detailed schema information retrieval.
"""

import asyncio
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import aiofiles
import httpx
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from pydantic import BaseModel, HttpUrl, ValidationError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ApiConfig(BaseModel):
    """Configuration for a saved API"""

    name: str
    url: HttpUrl
    description: Optional[str] = None
    headers: Dict[str, str] = {}


class ApiConfigStorage(BaseModel):
    """Storage model for API configurations"""

    apis: Dict[str, ApiConfig] = {}


class EndpointInfo(BaseModel):
    """Information about an API endpoint"""

    path: str
    method: str
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    operation_id: Optional[str] = None


class ModelInfo(BaseModel):
    """Information about a data model"""

    name: str
    type: str = "object"
    properties: Dict[str, Any] = {}
    required: List[str] = []
    description: Optional[str] = None


class OpenAPICache:
    """Cache for OpenAPI schemas to avoid repeated downloads"""

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._client = httpx.AsyncClient(timeout=30.0)

    async def get_schema(
        self, url: str, headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Get OpenAPI schema, using cache if available"""
        cache_key = url
        if headers:
            headers_hash = hashlib.md5(
                str(sorted(headers.items())).encode()
            ).hexdigest()
            cache_key = f"{url}#{headers_hash}"

        if cache_key not in self._cache:
            try:
                response = await self._client.get(url, headers=headers)
                response.raise_for_status()
                schema = response.json()
                self._cache[cache_key] = schema
                logger.info(f"Cached OpenAPI schema from {url}")
            except Exception as e:
                logger.error(f"Failed to fetch OpenAPI schema from {url}: {e}")
                raise

        return self._cache[cache_key]

    async def close(self):
        await self._client.aclose()


class ConfigManager:
    """Manages API configurations with JSON persistence"""

    def __init__(self, config_path: Path = Path("api_configs.json")):
        self.config_path = config_path
        self._storage: ApiConfigStorage = ApiConfigStorage()

    async def load_config(self):
        try:
            if self.config_path.exists():
                async with aiofiles.open(self.config_path, "r") as f:
                    content = await f.read()
                    data = json.loads(content)
                    self._storage = ApiConfigStorage(**data)
                    logger.info(f"Loaded {len(self._storage.apis)} API configurations")
            else:
                logger.info("No existing configuration file found, starting fresh")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self._storage = ApiConfigStorage()

    async def save_config(self):
        try:
            async with aiofiles.open(self.config_path, "w") as f:
                content = self._storage.model_dump_json(indent=2)
                await f.write(content)
                logger.info(f"Saved configuration with {len(self._storage.apis)} APIs")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise

    async def add_api(
        self,
        name: str,
        url: str,
        description: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        try:
            api_config = ApiConfig(
                name=name, url=url, description=description, headers=headers or {}
            )
            self._storage.apis[name] = api_config
            await self.save_config()
            return f"Added API '{name}' with URL {url}"
        except ValidationError as e:
            raise ValueError(f"Invalid URL or configuration: {e}")

    async def remove_api(self, name: str):
        if name not in self._storage.apis:
            raise ValueError(f"API '{name}' not found")

        del self._storage.apis[name]
        await self.save_config()
        return f"Removed API '{name}'"

    def list_apis(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": config.name,
                "url": str(config.url),
                "description": config.description,
            }
            for config in self._storage.apis.values()
        ]

    def get_api_url(self, api_identifier: str) -> str:
        if api_identifier in self._storage.apis:
            return str(self._storage.apis[api_identifier].url)

        try:
            parsed = urlparse(api_identifier)
            if parsed.scheme and parsed.netloc:
                return api_identifier
        except Exception:
            pass

        raise ValueError(f"Invalid API identifier: {api_identifier}")

    def get_api_config(self, api_identifier: str) -> tuple[str, Dict[str, str]]:
        """Get API URL and headers for the given identifier"""
        if api_identifier in self._storage.apis:
            config = self._storage.apis[api_identifier]
            return str(config.url), config.headers

        try:
            parsed = urlparse(api_identifier)
            if parsed.scheme and parsed.netloc:
                return api_identifier, {}
        except Exception:
            pass

        raise ValueError(f"Invalid API identifier: {api_identifier}")


class OpenAPIExplorer:
    """Main class for exploring OpenAPI schemas"""

    def __init__(self, config_manager: ConfigManager, cache: OpenAPICache):
        self.config_manager = config_manager
        self.cache = cache

    async def get_api_info(self, api_identifier: str) -> Dict[str, Any]:
        url, headers = self.config_manager.get_api_config(api_identifier)
        schema = await self.cache.get_schema(url, headers)

        info = schema.get("info", {})
        return {
            "title": info.get("title", "Unknown"),
            "version": info.get("version", "Unknown"),
            "description": info.get("description", ""),
            "base_url": url.replace("/openapi.json", ""),
            "tags": [tag.get("name") for tag in schema.get("tags", [])],
        }

    async def list_endpoints(self, api_identifier: str) -> List[EndpointInfo]:
        url, headers = self.config_manager.get_api_config(api_identifier)
        schema = await self.cache.get_schema(url, headers)

        endpoints = []
        paths = schema.get("paths", {})

        for path, path_info in paths.items():
            for method, operation in path_info.items():
                if method.lower() in [
                    "get",
                    "post",
                    "put",
                    "delete",
                    "patch",
                    "head",
                    "options",
                ]:
                    endpoint = EndpointInfo(
                        path=path,
                        method=method.upper(),
                        summary=operation.get("summary"),
                        description=operation.get("description"),
                        tags=operation.get("tags", []),
                        operation_id=operation.get("operationId"),
                    )
                    endpoints.append(endpoint)

        return endpoints

    async def search_endpoints(
        self, api_identifier: str, query: str
    ) -> List[EndpointInfo]:
        endpoints = await self.list_endpoints(api_identifier)
        query_lower = query.lower()

        filtered = []
        for endpoint in endpoints:
            search_text = " ".join(
                [
                    endpoint.path,
                    endpoint.summary or "",
                    endpoint.description or "",
                    " ".join(endpoint.tags),
                ]
            ).lower()

            if query_lower in search_text:
                filtered.append(endpoint)

        return filtered

    async def get_endpoint_details(
        self, api_identifier: str, path: str, method: str
    ) -> Dict[str, Any]:
        url, headers = self.config_manager.get_api_config(api_identifier)
        schema = await self.cache.get_schema(url, headers)

        paths = schema.get("paths", {})
        if path not in paths:
            raise ValueError(f"Path '{path}' not found")

        path_info = paths[path]
        method_lower = method.lower()

        if method_lower not in path_info:
            raise ValueError(f"Method '{method}' not found for path '{path}'")

        operation = path_info[method_lower]

        details = {
            "path": path,
            "method": method.upper(),
            "summary": operation.get("summary"),
            "description": operation.get("description"),
            "tags": operation.get("tags", []),
            "operation_id": operation.get("operationId"),
            "parameters": operation.get("parameters", []),
            "request_body": operation.get("requestBody"),
            "responses": operation.get("responses", {}),
            "security": operation.get("security", []),
        }

        return details

    async def list_models(self, api_identifier: str) -> List[ModelInfo]:
        url, headers = self.config_manager.get_api_config(api_identifier)
        schema = await self.cache.get_schema(url, headers)

        models = []
        components = schema.get("components", {})
        schemas = components.get("schemas", {})

        for name, model_schema in schemas.items():
            model = ModelInfo(
                name=name,
                type=model_schema.get("type", "object"),
                properties=model_schema.get("properties", {}),
                required=model_schema.get("required", []),
                description=model_schema.get("description"),
            )
            models.append(model)

        return models

    async def get_model_schema(
        self, api_identifier: str, model_name: str
    ) -> Dict[str, Any]:
        url, headers = self.config_manager.get_api_config(api_identifier)
        schema = await self.cache.get_schema(url, headers)

        components = schema.get("components", {})
        schemas = components.get("schemas", {})

        if model_name not in schemas:
            raise ValueError(f"Model '{model_name}' not found")

        return {"name": model_name, "schema": schemas[model_name]}


# Initialize global instances
cache = OpenAPICache()
config_manager = ConfigManager()
explorer = OpenAPIExplorer(config_manager, cache)

# Create MCP server
server = Server("openapi-mcp-proxy")


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available MCP tools"""
    return [
        Tool(
            name="add_api",
            description="Add a new API configuration with name, URL and optional description",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Short name for the API"},
                    "url": {
                        "type": "string",
                        "description": "Base URL of the FastAPI service",
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional description",
                    },
                    "headers": {
                        "type": "object",
                        "description": "Optional HTTP headers for authentication (e.g., {'Authorization': 'Bearer token', 'X-API-Key': 'key'})",
                        "additionalProperties": {"type": "string"},
                    },
                },
                "required": ["name", "url"],
            },
        ),
        Tool(
            name="list_saved_apis",
            description="List all saved API configurations",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="remove_api",
            description="Remove a saved API configuration",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the API to remove",
                    }
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="get_api_info",
            description="Get general information about an API",
            inputSchema={
                "type": "object",
                "properties": {
                    "api": {"type": "string", "description": "API name or direct URL"}
                },
                "required": ["api"],
            },
        ),
        Tool(
            name="list_endpoints",
            description="List all endpoints in an API",
            inputSchema={
                "type": "object",
                "properties": {
                    "api": {"type": "string", "description": "API name or direct URL"}
                },
                "required": ["api"],
            },
        ),
        Tool(
            name="search_endpoints",
            description="Search endpoints by query in path, description, or tags",
            inputSchema={
                "type": "object",
                "properties": {
                    "api": {"type": "string", "description": "API name or direct URL"},
                    "query": {"type": "string", "description": "Search query"},
                },
                "required": ["api", "query"],
            },
        ),
        Tool(
            name="get_endpoint_details",
            description="Get detailed information about a specific endpoint",
            inputSchema={
                "type": "object",
                "properties": {
                    "api": {"type": "string", "description": "API name or direct URL"},
                    "path": {"type": "string", "description": "Endpoint path"},
                    "method": {"type": "string", "description": "HTTP method"},
                },
                "required": ["api", "path", "method"],
            },
        ),
        Tool(
            name="list_models",
            description="List all data models in an API (short format)",
            inputSchema={
                "type": "object",
                "properties": {
                    "api": {"type": "string", "description": "API name or direct URL"}
                },
                "required": ["api"],
            },
        ),
        Tool(
            name="list_models_detailed",
            description="List all data models in an API with detailed information",
            inputSchema={
                "type": "object",
                "properties": {
                    "api": {"type": "string", "description": "API name or direct URL"}
                },
                "required": ["api"],
            },
        ),
        Tool(
            name="get_model_schema",
            description="Get detailed schema for a specific model",
            inputSchema={
                "type": "object",
                "properties": {
                    "api": {"type": "string", "description": "API name or direct URL"},
                    "model_name": {
                        "type": "string",
                        "description": "Name of the model",
                    },
                },
                "required": ["api", "model_name"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""
    try:
        if name == "add_api":
            result = await config_manager.add_api(
                arguments["name"],
                arguments["url"],
                arguments.get("description"),
                arguments.get("headers"),
            )
            return [TextContent(type="text", text=result)]

        elif name == "list_saved_apis":
            apis = config_manager.list_apis()
            if not apis:
                return [TextContent(type="text", text="No saved APIs found")]

            result = "Saved APIs:\n"
            for api in apis:
                result += f"- {api['name']}: {api['url']}"
                if api["description"]:
                    result += f" - {api['description']}"
                result += "\n"

            return [TextContent(type="text", text=result)]

        elif name == "remove_api":
            result = await config_manager.remove_api(arguments["name"])
            return [TextContent(type="text", text=result)]

        elif name == "get_api_info":
            info = await explorer.get_api_info(arguments["api"])
            result = f"API: {info['title']} (v{info['version']})\n"
            result += f"Description: {info['description']}\n"
            result += f"Base URL: {info['base_url']}\n"
            if info["tags"]:
                result += f"Tags: {', '.join(info['tags'])}\n"

            return [TextContent(type="text", text=result)]

        elif name == "list_endpoints":
            endpoints = await explorer.list_endpoints(arguments["api"])
            if not endpoints:
                return [TextContent(type="text", text="No endpoints found")]

            result = f"Found {len(endpoints)} endpoints:\n\n"
            for endpoint in endpoints:
                result += f"{endpoint.method} {endpoint.path}"
                if endpoint.summary:
                    result += f" - {endpoint.summary}"
                if endpoint.tags:
                    result += f" [Tags: {', '.join(endpoint.tags)}]"
                result += "\n"

            return [TextContent(type="text", text=result)]

        elif name == "search_endpoints":
            endpoints = await explorer.search_endpoints(
                arguments["api"], arguments["query"]
            )
            if not endpoints:
                return [
                    TextContent(
                        type="text",
                        text=f"No endpoints found matching '{arguments['query']}'",
                    )
                ]

            result = (
                f"Found {len(endpoints)} endpoints matching '{arguments['query']}':\n\n"
            )
            for endpoint in endpoints:
                result += f"{endpoint.method} {endpoint.path}"
                if endpoint.summary:
                    result += f" - {endpoint.summary}"
                if endpoint.tags:
                    result += f" [Tags: {', '.join(endpoint.tags)}]"
                result += "\n"

            return [TextContent(type="text", text=result)]

        elif name == "get_endpoint_details":
            details = await explorer.get_endpoint_details(
                arguments["api"], arguments["path"], arguments["method"]
            )

            result = f"{details['method']} {details['path']}\n"
            if details["summary"]:
                result += f"Summary: {details['summary']}\n"
            if details["description"]:
                result += f"Description: {details['description']}\n"
            if details["tags"]:
                result += f"Tags: {', '.join(details['tags'])}\n"

            result += f"\nFull schema:\n{json.dumps(details, indent=2)}"

            return [TextContent(type="text", text=result)]

        elif name == "list_models":
            models = await explorer.list_models(arguments["api"])
            if not models:
                return [TextContent(type="text", text="No models found")]

            result = f"Found {len(models)} models:\n\n"
            for model in models:
                result += f"- {model.name} ({model.type})\n"

            return [TextContent(type="text", text=result)]

        elif name == "list_models_detailed":
            models = await explorer.list_models(arguments["api"])
            if not models:
                return [TextContent(type="text", text="No models found")]

            result = f"Found {len(models)} models:\n\n"
            for model in models:
                result += f"- {model.name} ({model.type})"
                if model.description:
                    result += f" - {model.description}"
                result += f" [{len(model.properties)} properties"
                if model.required:
                    result += f", {len(model.required)} required"
                result += "]\n"

            return [TextContent(type="text", text=result)]

        elif name == "get_model_schema":
            schema = await explorer.get_model_schema(
                arguments["api"], arguments["model_name"]
            )
            result = f"Model: {schema['name']}\n\n"
            result += f"Schema:\n{json.dumps(schema['schema'], indent=2)}"

            return [TextContent(type="text", text=result)]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    await config_manager.load_config()

    try:
        # Run the server
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="openapi-mcp-proxy",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    finally:
        await cache.close()


if __name__ == "__main__":
    asyncio.run(main())
