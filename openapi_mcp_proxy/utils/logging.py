"""Logging utilities for OpenAPI MCP proxy."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional


def setup_logging(level: str = "INFO", log_file: Optional[Path] = None) -> None:
    """Setup application logging configuration."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Configure basic logging
    handlers = []

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(level=log_level, handlers=handlers, force=True)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name."""
    return logging.getLogger(name)


def log_api_operation(
    logger: logging.Logger, operation: str, api_name: str, **kwargs
) -> None:
    """Log an API operation with context."""
    context = " ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.info(f"API {operation}: {api_name} {context}".strip())


def log_tool_call(
    logger: logging.Logger, tool_name: str, arguments: Dict[str, Any]
) -> None:
    """Log a tool call with arguments."""
    args_str = ", ".join([f"{k}={v}" for k, v in arguments.items()])
    logger.info(f"Tool call: {tool_name}({args_str})")


def log_schema_operation(
    logger: logging.Logger, operation: str, url: str, **kwargs
) -> None:
    """Log a schema operation with context."""
    context = " ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.info(f"Schema {operation}: {url} {context}".strip())


def log_error_with_context(
    logger: logging.Logger, error: Exception, context: str, **kwargs
) -> None:
    """Log an error with additional context."""
    context_str = " ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.error(f"Error in {context}: {error} {context_str}".strip())
