"""Base classes for MCP tools."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from mcp.types import TextContent, Tool

from openapi_mcp_proxy.models.pagination import (
    EndpointFilterParams,
    ModelFilterParams,
    PaginationParams,
)
from openapi_mcp_proxy.services.config_manager import ConfigManager
from openapi_mcp_proxy.services.openapi_explorer import OpenAPIExplorer

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """Base class for all MCP tools."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def get_tool_definition(self) -> Tool:
        """Get the MCP tool definition."""
        pass

    @abstractmethod
    async def handle_call(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool call and return response."""
        pass

    def _create_text_response(self, text: str) -> List[TextContent]:
        """Create a text response."""
        return [TextContent(type="text", text=text)]

    def _create_error_response(self, error: Exception) -> List[TextContent]:
        """Create an error response."""
        error_msg = f"Error: {str(error)}"
        logger.error(f"Tool {self.name} error: {error}")
        return self._create_text_response(error_msg)


class ConfigTool(BaseTool):
    """Base class for configuration-related tools."""

    def __init__(self, name: str, description: str, config_manager: ConfigManager):
        super().__init__(name, description)
        self.config_manager = config_manager


class APITool(BaseTool):
    """Base class for API exploration tools."""

    def __init__(
        self,
        name: str,
        description: str,
        config_manager: ConfigManager,
        explorer: OpenAPIExplorer,
    ):
        super().__init__(name, description)
        self.config_manager = config_manager
        self.explorer = explorer

    def _validate_api_identifier(self, api_identifier: str) -> None:
        """Validate that the API identifier is valid."""
        try:
            self.config_manager.get_api_config(api_identifier)
        except ValueError as e:
            raise ValueError(f"Invalid API identifier '{api_identifier}': {e}")


class ToolDefinitionMixin:
    """Mixin to help create tool definitions with common patterns."""

    @staticmethod
    def create_api_input_schema() -> Dict[str, Any]:
        """Create input schema for API identifier parameter."""
        return {
            "type": "object",
            "properties": {
                "api": {"type": "string", "description": "API name or direct URL"}
            },
            "required": ["api"],
        }

    @staticmethod
    def create_name_input_schema() -> Dict[str, Any]:
        """Create input schema for name parameter."""
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name of the API to remove"}
            },
            "required": ["name"],
        }

    @staticmethod
    def create_add_api_input_schema() -> Dict[str, Any]:
        """Create input schema for adding API."""
        return {
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
        }

    @staticmethod
    def create_search_input_schema() -> Dict[str, Any]:
        """Create input schema for search operations."""
        return {
            "type": "object",
            "properties": {
                "api": {"type": "string", "description": "API name or direct URL"},
                "query": {"type": "string", "description": "Search query"},
            },
            "required": ["api", "query"],
        }

    @staticmethod
    def create_endpoint_details_input_schema() -> Dict[str, Any]:
        """Create input schema for endpoint details."""
        return {
            "type": "object",
            "properties": {
                "api": {"type": "string", "description": "API name or direct URL"},
                "path": {"type": "string", "description": "Endpoint path"},
                "method": {"type": "string", "description": "HTTP method"},
            },
            "required": ["api", "path", "method"],
        }

    @staticmethod
    def create_model_schema_input_schema() -> Dict[str, Any]:
        """Create input schema for model schema operations."""
        return {
            "type": "object",
            "properties": {
                "api": {"type": "string", "description": "API name or direct URL"},
                "model_name": {
                    "type": "string",
                    "description": "Name of the model",
                },
            },
            "required": ["api", "model_name"],
        }

    @staticmethod
    def create_pagination_properties() -> Dict[str, Any]:
        """Create pagination properties for input schemas."""
        return {
            "page": {
                "type": "integer",
                "description": "Page number (1-based)",
                "minimum": 1,
                "default": 1,
            },
            "page_size": {
                "type": "integer",
                "description": "Items per page (max 100)",
                "minimum": 1,
                "maximum": 100,
                "default": 50,
            },
        }

    @staticmethod
    def create_endpoint_filter_properties() -> Dict[str, Any]:
        """Create endpoint filter properties for input schemas."""
        return {
            "methods": {
                "type": "array",
                "description": "Filter by HTTP methods (e.g., ['GET', 'POST'])",
                "items": {"type": "string"},
            },
            "tags_include": {
                "type": "array",
                "description": "Include endpoints with these tags",
                "items": {"type": "string"},
            },
            "tags_exclude": {
                "type": "array",
                "description": "Exclude endpoints with these tags",
                "items": {"type": "string"},
            },
            "has_authentication": {
                "type": "boolean",
                "description": "Filter by authentication requirement",
            },
            "deprecated": {
                "type": "boolean",
                "description": "Filter by deprecation status",
            },
        }

    @staticmethod
    def create_model_filter_properties() -> Dict[str, Any]:
        """Create model filter properties for input schemas."""
        return {
            "types": {
                "type": "array",
                "description": "Filter by model types (e.g., ['object', 'array', 'string'])",
                "items": {"type": "string"},
            },
            "min_properties": {
                "type": "integer",
                "description": "Minimum number of properties",
                "minimum": 0,
            },
            "max_properties": {
                "type": "integer",
                "description": "Maximum number of properties",
                "minimum": 0,
            },
            "has_required_fields": {
                "type": "boolean",
                "description": "Filter by presence of required fields",
            },
            "tags_include": {
                "type": "array",
                "description": "Include models with these tags",
                "items": {"type": "string"},
            },
            "tags_exclude": {
                "type": "array",
                "description": "Exclude models with these tags",
                "items": {"type": "string"},
            },
        }

    @staticmethod
    def create_paginated_endpoint_input_schema() -> Dict[str, Any]:
        """Create input schema for paginated endpoint operations."""
        schema = ToolDefinitionMixin.create_api_input_schema()
        schema["properties"].update(ToolDefinitionMixin.create_pagination_properties())
        schema["properties"].update(
            ToolDefinitionMixin.create_endpoint_filter_properties()
        )
        return schema

    @staticmethod
    def create_paginated_model_input_schema() -> Dict[str, Any]:
        """Create input schema for paginated model operations."""
        schema = ToolDefinitionMixin.create_api_input_schema()
        schema["properties"].update(ToolDefinitionMixin.create_pagination_properties())
        schema["properties"].update(
            ToolDefinitionMixin.create_model_filter_properties()
        )
        schema["properties"]["include_details"] = {
            "type": "boolean",
            "description": "Include detailed information about models",
            "default": False,
        }
        return schema

    @staticmethod
    def create_paginated_search_input_schema() -> Dict[str, Any]:
        """Create input schema for paginated search operations."""
        schema = ToolDefinitionMixin.create_search_input_schema()
        schema["properties"].update(ToolDefinitionMixin.create_pagination_properties())
        schema["properties"].update(
            ToolDefinitionMixin.create_endpoint_filter_properties()
        )
        return schema

    @staticmethod
    def extract_pagination_params(arguments: Dict[str, Any]) -> PaginationParams:
        """Extract pagination parameters from tool arguments."""
        return PaginationParams(
            page=arguments.get("page", 1),
            page_size=arguments.get("page_size", 50),
        )

    @staticmethod
    def extract_endpoint_filter_params(
        arguments: Dict[str, Any],
    ) -> EndpointFilterParams:
        """Extract endpoint filter parameters from tool arguments."""
        return EndpointFilterParams(
            methods=arguments.get("methods"),
            tags_include=arguments.get("tags_include"),
            tags_exclude=arguments.get("tags_exclude"),
            has_authentication=arguments.get("has_authentication"),
            deprecated=arguments.get("deprecated"),
        )

    @staticmethod
    def extract_model_filter_params(arguments: Dict[str, Any]) -> ModelFilterParams:
        """Extract model filter parameters from tool arguments."""
        return ModelFilterParams(
            types=arguments.get("types"),
            min_properties=arguments.get("min_properties"),
            max_properties=arguments.get("max_properties"),
            has_required_fields=arguments.get("has_required_fields"),
            tags_include=arguments.get("tags_include"),
            tags_exclude=arguments.get("tags_exclude"),
        )
