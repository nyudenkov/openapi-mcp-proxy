"""Application settings for OpenAPI MCP proxy."""

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application settings configuration."""

    # Server settings
    server_name: str = Field(default="openapi-mcp-proxy", description="MCP server name")
    server_version: str = Field(default="0.1.0", description="MCP server version")

    # Configuration paths
    config_file_path: Path = Field(
        default=Path("api_configs.json"), description="Path to API configurations file"
    )

    # HTTP client settings
    http_timeout: float = Field(
        default=30.0, description="HTTP client timeout in seconds"
    )

    # Logging settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[Path] = Field(default=None, description="Optional log file path")

    # Cache settings
    enable_schema_cache: bool = Field(
        default=True, description="Enable OpenAPI schema caching"
    )

    class Config:
        env_prefix = "OPENAPI_MCP_"
        case_sensitive = False


def get_settings() -> Settings:
    """Get application settings with environment variable overrides."""
    return Settings(
        # Allow environment variable overrides
        server_name=os.getenv("OPENAPI_MCP_SERVER_NAME", "openapi-mcp-proxy"),
        server_version=os.getenv("OPENAPI_MCP_SERVER_VERSION", "0.1.0"),
        config_file_path=Path(
            os.getenv("OPENAPI_MCP_CONFIG_FILE_PATH", "api_configs.json")
        ),
        http_timeout=float(os.getenv("OPENAPI_MCP_HTTP_TIMEOUT", "30.0")),
        log_level=os.getenv("OPENAPI_MCP_LOG_LEVEL", "INFO"),
        log_file=Path(os.getenv("OPENAPI_MCP_LOG_FILE"))
        if os.getenv("OPENAPI_MCP_LOG_FILE")
        else None,
        enable_schema_cache=os.getenv("OPENAPI_MCP_ENABLE_SCHEMA_CACHE", "true").lower()
        == "true",
    )
