"""Custom exceptions for OpenAPI MCP proxy."""


class OpenAPIMCPError(Exception):
    """Base exception for OpenAPI MCP proxy errors."""

    pass


class ConfigurationError(OpenAPIMCPError):
    """Error in configuration management."""

    pass


class APINotFoundError(OpenAPIMCPError):
    """API configuration not found."""

    pass


class SchemaFetchError(OpenAPIMCPError):
    """Error fetching OpenAPI schema."""

    pass


class EndpointNotFoundError(OpenAPIMCPError):
    """Endpoint not found in schema."""

    pass


class ModelNotFoundError(OpenAPIMCPError):
    """Model not found in schema."""

    pass


class ValidationError(OpenAPIMCPError):
    """Data validation error."""

    pass


class ToolExecutionError(OpenAPIMCPError):
    """Error during tool execution."""

    pass
