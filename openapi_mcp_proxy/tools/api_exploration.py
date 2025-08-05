"""API exploration tools."""

from typing import Any, Dict, List

from mcp.types import TextContent, Tool

from openapi_mcp_proxy.tools.base import APITool, ToolDefinitionMixin


class GetApiInfoTool(APITool, ToolDefinitionMixin):
    """Tool for getting general API information."""

    def __init__(self, config_manager, explorer):
        super().__init__(
            name="get_api_info",
            description="Get general information about an API",
            config_manager=config_manager,
            explorer=explorer,
        )

    def get_tool_definition(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema=self.create_api_input_schema(),
        )

    async def handle_call(self, arguments: Dict[str, Any]) -> List[TextContent]:
        try:
            self._validate_api_identifier(arguments["api"])
            info = await self.explorer.get_api_info(arguments["api"])
            result = info.format_display()
            return self._create_text_response(result)
        except Exception as e:
            return self._create_error_response(e)


class ListEndpointsTool(APITool, ToolDefinitionMixin):
    """Tool for listing API endpoints."""

    def __init__(self, config_manager, explorer):
        super().__init__(
            name="list_endpoints",
            description="List all endpoints in an API",
            config_manager=config_manager,
            explorer=explorer,
        )

    def get_tool_definition(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema=self.create_api_input_schema(),
        )

    async def handle_call(self, arguments: Dict[str, Any]) -> List[TextContent]:
        try:
            self._validate_api_identifier(arguments["api"])
            endpoints = await self.explorer.list_endpoints(arguments["api"])
            result = self.explorer.format_endpoint_list(endpoints)
            return self._create_text_response(result)
        except Exception as e:
            return self._create_error_response(e)


class SearchEndpointsTool(APITool, ToolDefinitionMixin):
    """Tool for searching API endpoints."""

    def __init__(self, config_manager, explorer):
        super().__init__(
            name="search_endpoints",
            description="Search endpoints by query in path, description, or tags",
            config_manager=config_manager,
            explorer=explorer,
        )

    def get_tool_definition(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema=self.create_search_input_schema(),
        )

    async def handle_call(self, arguments: Dict[str, Any]) -> List[TextContent]:
        try:
            self._validate_api_identifier(arguments["api"])
            endpoints = await self.explorer.search_endpoints(
                arguments["api"], arguments["query"]
            )
            if not endpoints:
                result = f"No endpoints found matching '{arguments['query']}'"
            else:
                result = f"Found {len(endpoints)} endpoints matching '{arguments['query']}':\n\n"
                result += self.explorer.format_endpoint_list(endpoints)
            return self._create_text_response(result)
        except Exception as e:
            return self._create_error_response(e)


class GetEndpointDetailsTool(APITool, ToolDefinitionMixin):
    """Tool for getting detailed endpoint information."""

    def __init__(self, config_manager, explorer):
        super().__init__(
            name="get_endpoint_details",
            description="Get detailed information about a specific endpoint",
            config_manager=config_manager,
            explorer=explorer,
        )

    def get_tool_definition(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema=self.create_endpoint_details_input_schema(),
        )

    async def handle_call(self, arguments: Dict[str, Any]) -> List[TextContent]:
        try:
            self._validate_api_identifier(arguments["api"])
            details = await self.explorer.get_endpoint_details(
                arguments["api"], arguments["path"], arguments["method"]
            )
            result = self.explorer.format_endpoint_details(details)
            return self._create_text_response(result)
        except Exception as e:
            return self._create_error_response(e)


class ListModelsTool(APITool, ToolDefinitionMixin):
    """Tool for listing API data models."""

    def __init__(self, config_manager, explorer):
        super().__init__(
            name="list_models",
            description="List all data models in an API",
            config_manager=config_manager,
            explorer=explorer,
        )

    def get_tool_definition(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema=self.create_api_input_schema(),
        )

    async def handle_call(self, arguments: Dict[str, Any]) -> List[TextContent]:
        try:
            self._validate_api_identifier(arguments["api"])
            models = await self.explorer.list_models(arguments["api"])
            result = self.explorer.format_model_list(models, detailed=False)
            return self._create_text_response(result)
        except Exception as e:
            return self._create_error_response(e)


class ListModelsDetailedTool(APITool, ToolDefinitionMixin):
    """Tool for listing API data models with detailed information."""

    def __init__(self, config_manager, explorer):
        super().__init__(
            name="list_models_detailed",
            description="List all data models in an API with detailed information",
            config_manager=config_manager,
            explorer=explorer,
        )

    def get_tool_definition(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema=self.create_api_input_schema(),
        )

    async def handle_call(self, arguments: Dict[str, Any]) -> List[TextContent]:
        try:
            self._validate_api_identifier(arguments["api"])
            models = await self.explorer.list_models(arguments["api"])
            result = self.explorer.format_model_list(models, detailed=True)
            return self._create_text_response(result)
        except Exception as e:
            return self._create_error_response(e)


class GetModelSchemaTool(APITool, ToolDefinitionMixin):
    """Tool for getting detailed model schema."""

    def __init__(self, config_manager, explorer):
        super().__init__(
            name="get_model_schema",
            description="Get detailed schema for a specific model",
            config_manager=config_manager,
            explorer=explorer,
        )

    def get_tool_definition(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema=self.create_model_schema_input_schema(),
        )

    async def handle_call(self, arguments: Dict[str, Any]) -> List[TextContent]:
        try:
            self._validate_api_identifier(arguments["api"])
            schema = await self.explorer.get_model_schema(
                arguments["api"], arguments["model_name"]
            )
            result = self.explorer.format_model_schema(schema)
            return self._create_text_response(result)
        except Exception as e:
            return self._create_error_response(e)
