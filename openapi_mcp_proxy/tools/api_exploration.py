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
            inputSchema=self.create_paginated_endpoint_input_schema(),
        )

    async def handle_call(self, arguments: Dict[str, Any]) -> List[TextContent]:
        try:
            self._validate_api_identifier(arguments["api"])

            pagination = self.extract_pagination_params(arguments)
            filters = self.extract_endpoint_filter_params(arguments)

            paginated_result = await self.explorer.list_endpoints_paginated(
                arguments["api"], pagination, filters
            )

            result = self._format_paginated_endpoint_response(paginated_result, filters)
            return self._create_text_response(result)
        except Exception as e:
            return self._create_error_response(e)

    def _format_paginated_endpoint_response(self, paginated_result, filters) -> str:
        """Format paginated endpoint response."""
        result = ""

        filter_display = filters.format_display()
        if filter_display:
            result += filter_display + "\n\n"

        if filters and any(
            [
                filters.methods,
                filters.tags_include,
                filters.tags_exclude,
                filters.has_authentication is not None,
                filters.deprecated is not None,
            ]
        ):
            result += f"Total Results: {paginated_result.total_count} endpoints (filtered)\n\n"
        else:
            result += f"Total Results: {paginated_result.total_count} endpoints\n\n"

        if paginated_result.items:
            for endpoint in paginated_result.items:
                result += endpoint.format_display() + "\n"
        else:
            result += "No endpoints found\n"

        result += "\n" + paginated_result.format_navigation()

        return result


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
            inputSchema=self.create_paginated_search_input_schema(),
        )

    async def handle_call(self, arguments: Dict[str, Any]) -> List[TextContent]:
        try:
            self._validate_api_identifier(arguments["api"])

            pagination = self.extract_pagination_params(arguments)
            filters = self.extract_endpoint_filter_params(arguments)

            paginated_result = await self.explorer.search_endpoints_paginated(
                arguments["api"], arguments["query"], pagination, filters
            )

            result = self._format_paginated_search_response(
                paginated_result, arguments["query"], filters
            )
            return self._create_text_response(result)
        except Exception as e:
            return self._create_error_response(e)

    def _format_paginated_search_response(
        self, paginated_result, query, filters
    ) -> str:
        """Format paginated search response."""
        result = f"Search Query: '{query}'\n\n"

        filter_display = filters.format_display()
        if filter_display:
            result += filter_display + "\n\n"

        result += (
            f"Total Results: {paginated_result.total_count} endpoints matching query"
        )
        if filters and any(
            [
                filters.methods,
                filters.tags_include,
                filters.tags_exclude,
                filters.has_authentication is not None,
                filters.deprecated is not None,
            ]
        ):
            result += " (with filters applied)"
        result += "\n\n"

        # Show endpoints
        if paginated_result.items:
            for endpoint in paginated_result.items:
                result += endpoint.format_display() + "\n"
        else:
            result += "No endpoints found\n"

        result += "\n" + paginated_result.format_navigation()

        return result


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
                arguments["api"],
                arguments["path"],
                arguments["method"],
                arguments.get("include_responses", True),
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
            inputSchema=self.create_paginated_model_input_schema(),
        )

    async def handle_call(self, arguments: Dict[str, Any]) -> List[TextContent]:
        try:
            self._validate_api_identifier(arguments["api"])

            pagination = self.extract_pagination_params(arguments)
            filters = self.extract_model_filter_params(arguments)
            include_details = arguments.get("include_details", False)

            paginated_result = await self.explorer.list_models_paginated(
                arguments["api"], pagination, filters
            )

            result = self._format_paginated_model_response(
                paginated_result, filters, include_details
            )
            return self._create_text_response(result)
        except Exception as e:
            return self._create_error_response(e)

    def _format_paginated_model_response(
        self, paginated_result, filters, include_details
    ) -> str:
        """Format paginated model response."""
        result = ""

        filter_display = filters.format_display()
        if filter_display:
            result += filter_display + "\n\n"

        if filters and any(
            [
                filters.types,
                filters.min_properties is not None,
                filters.max_properties is not None,
                filters.has_required_fields is not None,
                filters.tags_include,
                filters.tags_exclude,
            ]
        ):
            result += (
                f"Total Results: {paginated_result.total_count} models (filtered)\n\n"
            )
        else:
            result += f"Total Results: {paginated_result.total_count} models\n\n"

        if paginated_result.items:
            for model in paginated_result.items:
                result += model.format_display(detailed=include_details) + "\n"
        else:
            result += "No models found\n"

        result += "\n" + paginated_result.format_navigation()

        return result


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
