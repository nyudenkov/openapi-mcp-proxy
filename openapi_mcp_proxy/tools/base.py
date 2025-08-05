"""Base classes for MCP tools."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from mcp.types import TextContent, Tool

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
