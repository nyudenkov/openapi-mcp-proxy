#!/usr/bin/env python3
"""
MCP Server for OpenAPI Schema Exploration

Clean, single entry point using the refactored modular architecture.
"""

import asyncio

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

from .config.settings import get_settings
from .services.config_manager import ConfigManager
from .services.openapi_cache import OpenAPICache
from .services.openapi_explorer import OpenAPIExplorer
from .services.tool_registry import ToolRegistry
from .utils.logging import get_logger, setup_logging


async def main():
    """Main entry point for the OpenAPI MCP server."""
    # Load settings
    settings = get_settings()

    # Setup logging
    setup_logging(settings.log_level, settings.log_file)
    logger = get_logger(__name__)

    logger.info(f"Starting {settings.server_name} v{settings.server_version}")

    # Initialize services with dependency injection
    config_manager = ConfigManager(settings.config_file_path)
    cache = OpenAPICache(settings.http_timeout)
    explorer = OpenAPIExplorer(config_manager, cache)

    # Load existing configuration
    await config_manager.load_config()

    # Create tool registry
    tool_registry = ToolRegistry(config_manager, explorer)
    logger.info(f"Registered {tool_registry.get_tool_count()} tools")

    # Create MCP server
    server = Server(settings.server_name)

    # Register handlers
    @server.list_tools()
    async def handle_list_tools():
        """List available MCP tools"""
        return tool_registry.get_tool_definitions()

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict):
        """Handle tool calls"""
        return await tool_registry.handle_tool_call(name, arguments)

    logger.info("MCP server ready")

    try:
        # Run the server
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name=settings.server_name,
                    server_version=settings.server_version,
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        # Cleanup
        await cache.close()
        logger.info("Server shutdown complete")


def run():
    """Synchronous entry point wrapper for scripts."""
    asyncio.run(main())


if __name__ == "__main__":
    run()