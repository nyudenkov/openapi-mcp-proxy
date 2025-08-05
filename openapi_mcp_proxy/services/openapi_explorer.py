"""OpenAPI schema exploration service."""

import json
import logging
from typing import Any, Dict, List

from openapi_mcp_proxy.models.endpoint import EndpointInfo
from openapi_mcp_proxy.models.schema import ApiInfo, ModelInfo
from openapi_mcp_proxy.services.config_manager import ConfigManager
from openapi_mcp_proxy.services.openapi_cache import OpenAPICache

logger = logging.getLogger(__name__)


class OpenAPIExplorer:
    """Main service for exploring OpenAPI schemas"""

    def __init__(self, config_manager: ConfigManager, cache: OpenAPICache):
        self.config_manager = config_manager
        self.cache = cache

    async def get_api_info(self, api_identifier: str) -> ApiInfo:
        """Get general information about an API."""
        url, headers = self.config_manager.get_api_config(api_identifier)
        schema = await self.cache.get_schema(url, headers)

        info = schema.get("info", {})
        return ApiInfo(
            title=info.get("title", "Unknown"),
            version=info.get("version", "Unknown"),
            description=info.get("description", ""),
            base_url=url.replace("/openapi.json", ""),
            tags=[tag.get("name") for tag in schema.get("tags", [])],
        )

    async def list_endpoints(self, api_identifier: str) -> List[EndpointInfo]:
        """List all endpoints in an API."""
        url, headers = self.config_manager.get_api_config(api_identifier)
        schema = await self.cache.get_schema(url, headers)

        endpoints = []
        paths = schema.get("paths", {})

        for path, path_info in paths.items():
            for method, operation in path_info.items():
                if self._is_valid_http_method(method):
                    endpoint = EndpointInfo(
                        path=path,
                        method=method.upper(),
                        summary=operation.get("summary"),
                        description=operation.get("description"),
                        tags=operation.get("tags", []),
                        operation_id=operation.get("operationId"),
                    )
                    endpoints.append(endpoint)

        logger.info(f"Found {len(endpoints)} endpoints for API {api_identifier}")
        return endpoints

    async def search_endpoints(
        self, api_identifier: str, query: str
    ) -> List[EndpointInfo]:
        """Search endpoints by query in path, description, or tags."""
        endpoints = await self.list_endpoints(api_identifier)
        filtered = [endpoint for endpoint in endpoints if endpoint.matches_query(query)]

        logger.info(
            f"Found {len(filtered)} endpoints matching '{query}' for API {api_identifier}"
        )
        return filtered

    async def get_endpoint_details(
        self, api_identifier: str, path: str, method: str
    ) -> Dict[str, Any]:
        """Get detailed information about a specific endpoint."""
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

        logger.info(f"Retrieved details for {method.upper()} {path}")
        return details

    async def list_models(self, api_identifier: str) -> List[ModelInfo]:
        """List all data models in an API."""
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

        logger.info(f"Found {len(models)} models for API {api_identifier}")
        return models

    async def get_model_schema(
        self, api_identifier: str, model_name: str
    ) -> Dict[str, Any]:
        """Get detailed schema for a specific model."""
        url, headers = self.config_manager.get_api_config(api_identifier)
        schema = await self.cache.get_schema(url, headers)

        components = schema.get("components", {})
        schemas = components.get("schemas", {})

        if model_name not in schemas:
            raise ValueError(f"Model '{model_name}' not found")

        logger.info(f"Retrieved schema for model {model_name}")
        return {"name": model_name, "schema": schemas[model_name]}

    def format_endpoint_list(self, endpoints: List[EndpointInfo]) -> str:
        """Format a list of endpoints for display."""
        if not endpoints:
            return "No endpoints found"

        result = f"Found {len(endpoints)} endpoints:\n\n"
        for endpoint in endpoints:
            result += endpoint.format_display() + "\n"

        return result

    def format_model_list(self, models: List[ModelInfo], detailed: bool = False) -> str:
        """Format a list of models for display."""
        if not models:
            return "No models found"

        result = f"Found {len(models)} models:\n\n"
        for model in models:
            result += model.format_display(detailed) + "\n"

        return result

    def format_endpoint_details(self, details: Dict[str, Any]) -> str:
        """Format endpoint details for display."""
        result = f"{details['method']} {details['path']}\n"
        if details["summary"]:
            result += f"Summary: {details['summary']}\n"
        if details["description"]:
            result += f"Description: {details['description']}\n"
        if details["tags"]:
            result += f"Tags: {', '.join(details['tags'])}\n"

        result += f"\nFull schema:\n{json.dumps(details, indent=2)}"
        return result

    def format_model_schema(self, schema_data: Dict[str, Any]) -> str:
        """Format model schema for display."""
        result = f"Model: {schema_data['name']}\n\n"
        result += f"Schema:\n{json.dumps(schema_data['schema'], indent=2)}"
        return result

    @staticmethod
    def _is_valid_http_method(method: str) -> bool:
        """Check if a method is a valid HTTP method."""
        valid_methods = {"get", "post", "put", "delete", "patch", "head", "options"}
        return method.lower() in valid_methods
