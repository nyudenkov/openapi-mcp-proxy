"""API management tools."""

from typing import Any, Dict, List

from mcp.types import TextContent, Tool

from openapi_mcp_proxy.tools.base import ConfigTool, ToolDefinitionMixin


class AddApiTool(ConfigTool, ToolDefinitionMixin):
    """Tool for adding API configurations."""

    def __init__(self, config_manager):
        super().__init__(
            name="add_api",
            description="Add a new API configuration with name, URL and optional description",
            config_manager=config_manager,
        )

    def get_tool_definition(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema=self.create_add_api_input_schema(),
        )

    async def handle_call(self, arguments: Dict[str, Any]) -> List[TextContent]:
        try:
            result = await self.config_manager.add_api(
                arguments["name"],
                arguments["url"],
                arguments.get("description"),
                arguments.get("headers"),
            )
            return self._create_text_response(result)
        except Exception as e:
            return self._create_error_response(e)


class ListSavedApisTool(ConfigTool, ToolDefinitionMixin):
    """Tool for listing saved API configurations."""

    def __init__(self, config_manager):
        super().__init__(
            name="list_saved_apis",
            description="List all saved API configurations",
            config_manager=config_manager,
        )

    def get_tool_definition(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        )

    async def handle_call(self, arguments: Dict[str, Any]) -> List[TextContent]:
        try:
            apis = self.config_manager.list_apis()
            result = self._format_api_list(apis)
            return self._create_text_response(result)
        except Exception as e:
            return self._create_error_response(e)

    def _format_api_list(self, apis: List[Dict[str, str]]) -> str:
        """Format API list for display."""
        if not apis:
            return "No saved APIs found"

        result = f"Saved APIs ({len(apis)}):\n\n"
        for api in apis:
            result += f"- {api['name']}: {api['url']}"
            if api.get("description"):
                result += f" - {api['description']}"
            result += "\n"

        return result


class RemoveApiTool(ConfigTool, ToolDefinitionMixin):
    """Tool for removing API configurations."""

    def __init__(self, config_manager):
        super().__init__(
            name="remove_api",
            description="Remove a saved API configuration",
            config_manager=config_manager,
        )

    def get_tool_definition(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema=self.create_name_input_schema(),
        )

    async def handle_call(self, arguments: Dict[str, Any]) -> List[TextContent]:
        try:
            result = await self.config_manager.remove_api(arguments["name"])
            return self._create_text_response(result)
        except Exception as e:
            return self._create_error_response(e)
