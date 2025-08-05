"""Tool registration system for MCP server."""

import logging
from typing import Any, Dict, List

from mcp.types import TextContent, Tool

from openapi_mcp_proxy.services.config_manager import ConfigManager
from openapi_mcp_proxy.services.openapi_explorer import OpenAPIExplorer
from openapi_mcp_proxy.tools.api_exploration import (
    GetApiInfoTool,
    GetEndpointDetailsTool,
    GetModelSchemaTool,
    ListEndpointsTool,
    ListModelsDetailedTool,
    ListModelsTool,
    SearchEndpointsTool,
)
from openapi_mcp_proxy.tools.api_management import (
    AddApiTool,
    ListSavedApisTool,
    RemoveApiTool,
)
from openapi_mcp_proxy.tools.base import BaseTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing MCP tools."""

    def __init__(self, config_manager: ConfigManager, explorer: OpenAPIExplorer):
        self.config_manager = config_manager
        self.explorer = explorer
        self._tools: Dict[str, BaseTool] = {}
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all available tools."""
        tools = [
            # API Management Tools
            AddApiTool(self.config_manager),
            ListSavedApisTool(self.config_manager),
            RemoveApiTool(self.config_manager),
            # API Exploration Tools
            GetApiInfoTool(self.config_manager, self.explorer),
            ListEndpointsTool(self.config_manager, self.explorer),
            SearchEndpointsTool(self.config_manager, self.explorer),
            GetEndpointDetailsTool(self.config_manager, self.explorer),
            ListModelsTool(self.config_manager, self.explorer),
            ListModelsDetailedTool(self.config_manager, self.explorer),
            GetModelSchemaTool(self.config_manager, self.explorer),
        ]

        for tool in tools:
            self._tools[tool.name] = tool
            logger.debug(f"Registered tool: {tool.name}")

        logger.info(f"Registered {len(self._tools)} tools")

    def get_tool_definitions(self) -> List[Tool]:
        """Get all tool definitions for MCP server."""
        return [tool.get_tool_definition() for tool in self._tools.values()]

    async def handle_tool_call(
        self, name: str, arguments: Dict[str, Any]
    ) -> List[TextContent]:
        """Handle a tool call by dispatching to the appropriate tool."""
        if name not in self._tools:
            error_msg = f"Unknown tool: {name}"
            logger.error(error_msg)
            return [TextContent(type="text", text=error_msg)]

        tool = self._tools[name]
        logger.info(f"Handling tool call: {name}")

        try:
            return await tool.handle_call(arguments)
        except Exception as e:
            logger.error(f"Error handling tool call {name}: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    def get_tool_names(self) -> List[str]:
        """Get list of all registered tool names."""
        return list(self._tools.keys())

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools

    def get_tool_count(self) -> int:
        """Get the number of registered tools."""
        return len(self._tools)
