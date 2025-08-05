"""OpenAPI schema exploration service."""

import json
import logging
from typing import Any, Dict, List, Optional

from openapi_mcp_proxy.models.endpoint import EndpointInfo
from openapi_mcp_proxy.models.pagination import (
    EndpointFilterParams,
    ModelFilterParams,
    PaginationParams,
    PaginationResult,
)
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
        base_url = self._get_base_url_from_schema(schema)

        return ApiInfo(
            title=info.get("title", "Unknown"),
            version=info.get("version", "Unknown"),
            description=info.get("description", ""),
            base_url=base_url,
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
                    deprecated = operation.get("deprecated", False)

                    has_auth = bool(operation.get("security", [])) or bool(
                        schema.get("security", [])
                    )

                    endpoint = EndpointInfo(
                        path=path,
                        method=method.upper(),
                        summary=operation.get("summary"),
                        description=operation.get("description"),
                        tags=operation.get("tags", []),
                        operation_id=operation.get("operationId"),
                        deprecated=deprecated,
                        has_authentication=has_auth,
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
        self,
        api_identifier: str,
        path: str,
        method: str,
        include_responses: bool = True,
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
            "security": operation.get("security", []),
        }

        if include_responses:
            details["responses"] = operation.get("responses", {})

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
            tags = []
            if "x-tags" in model_schema:
                tags = model_schema["x-tags"]
            elif "tags" in model_schema:
                tags = model_schema["tags"]

            model = ModelInfo(
                name=name,
                type=model_schema.get("type", "object"),
                properties=model_schema.get("properties", {}),
                required=model_schema.get("required", []),
                description=model_schema.get("description"),
                tags=tags,
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

    async def list_endpoints_paginated(
        self,
        api_identifier: str,
        pagination: PaginationParams,
        filters: Optional[EndpointFilterParams] = None,
    ) -> PaginationResult[EndpointInfo]:
        """List endpoints with pagination and filtering."""
        all_endpoints = await self.list_endpoints(api_identifier)

        if filters:
            filtered_endpoints = [
                ep for ep in all_endpoints if ep.matches_filters(filters)
            ]
        else:
            filtered_endpoints = all_endpoints

        total_count = len(filtered_endpoints)
        start_idx = pagination.get_offset()
        end_idx = start_idx + pagination.get_limit()
        paginated_endpoints = filtered_endpoints[start_idx:end_idx]

        logger.info(
            f"Paginated endpoints for API {api_identifier}: "
            f"page {pagination.page}, showing {len(paginated_endpoints)} of {total_count}"
        )

        return PaginationResult.create(paginated_endpoints, total_count, pagination)

    async def search_endpoints_paginated(
        self,
        api_identifier: str,
        query: str,
        pagination: PaginationParams,
        filters: Optional[EndpointFilterParams] = None,
    ) -> PaginationResult[EndpointInfo]:
        """Search endpoints with pagination and filtering."""
        all_endpoints = await self.list_endpoints(api_identifier)

        query_filtered = [ep for ep in all_endpoints if ep.matches_query(query)]

        if filters:
            filtered_endpoints = [
                ep for ep in query_filtered if ep.matches_filters(filters)
            ]
        else:
            filtered_endpoints = query_filtered

        total_count = len(filtered_endpoints)
        start_idx = pagination.get_offset()
        end_idx = start_idx + pagination.get_limit()
        paginated_endpoints = filtered_endpoints[start_idx:end_idx]

        logger.info(
            f"Paginated search for '{query}' in API {api_identifier}: "
            f"page {pagination.page}, showing {len(paginated_endpoints)} of {total_count}"
        )

        return PaginationResult.create(paginated_endpoints, total_count, pagination)

    async def list_models_paginated(
        self,
        api_identifier: str,
        pagination: PaginationParams,
        filters: Optional[ModelFilterParams] = None,
    ) -> PaginationResult[ModelInfo]:
        """List models with pagination and filtering."""
        all_models = await self.list_models(api_identifier)

        if filters:
            filtered_models = [
                model for model in all_models if model.matches_filters(filters)
            ]
        else:
            filtered_models = all_models

        total_count = len(filtered_models)
        start_idx = pagination.get_offset()
        end_idx = start_idx + pagination.get_limit()
        paginated_models = filtered_models[start_idx:end_idx]

        logger.info(
            f"Paginated models for API {api_identifier}: "
            f"page {pagination.page}, showing {len(paginated_models)} of {total_count}"
        )

        return PaginationResult.create(paginated_models, total_count, pagination)

    def paginate_results(
        self, items: List, pagination: PaginationParams
    ) -> PaginationResult:
        """Generic pagination utility method."""
        total_count = len(items)
        start_idx = pagination.get_offset()
        end_idx = start_idx + pagination.get_limit()
        paginated_items = items[start_idx:end_idx]

        return PaginationResult.create(paginated_items, total_count, pagination)

    def filter_endpoints(
        self, endpoints: List[EndpointInfo], filters: EndpointFilterParams
    ) -> List[EndpointInfo]:
        """Filter endpoints based on provided criteria."""
        return [ep for ep in endpoints if ep.matches_filters(filters)]

    def filter_models(
        self, models: List[ModelInfo], filters: ModelFilterParams
    ) -> List[ModelInfo]:
        """Filter models based on provided criteria."""
        return [model for model in models if model.matches_filters(filters)]

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

    @staticmethod
    def _get_base_url_from_schema(schema: Dict[str, Any]) -> str:
        """Extract base URL from OpenAPI schema's servers field."""
        servers = schema.get("servers", [])
        if servers and isinstance(servers, list) and len(servers) > 0:
            first_server = servers[0]
            if isinstance(first_server, dict) and "url" in first_server:
                return first_server["url"]

        # Try Swagger 2.0 style (host + basePath)
        host = schema.get("host")
        if host:
            schemes = schema.get("schemes", ["https"])
            scheme = schemes[0] if schemes else "https"
            base_path = schema.get("basePath", "")
            return f"{scheme}://{host}{base_path}"

        # Fallback - no reliable base URL available
        return ""
