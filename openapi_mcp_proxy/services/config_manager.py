"""Configuration management service."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import aiofiles
from pydantic import ValidationError

from openapi_mcp_proxy.models.api_config import ApiConfig, ApiConfigStorage

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages API configurations with JSON persistence"""

    def __init__(self, config_path: Path = Path("api_configs.json")):
        self.config_path = config_path
        self._storage: ApiConfigStorage = ApiConfigStorage()

    async def load_config(self) -> None:
        """Load configuration from file."""
        try:
            if self.config_path.exists():
                async with aiofiles.open(self.config_path, "r") as f:
                    content = await f.read()
                    data = json.loads(content)
                    self._storage = ApiConfigStorage(**data)
                    logger.info(f"Loaded {len(self._storage.apis)} API configurations")
            else:
                logger.info("No existing configuration file found, starting fresh")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self._storage = ApiConfigStorage()

    async def save_config(self) -> None:
        """Save configuration to file."""
        try:
            async with aiofiles.open(self.config_path, "w") as f:
                content = self._storage.model_dump_json(indent=2)
                await f.write(content)
                logger.info(f"Saved configuration with {len(self._storage.apis)} APIs")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise

    async def add_api(
        self,
        name: str,
        url: str,
        description: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> str:
        """Add a new API configuration."""
        try:
            api_config = ApiConfig(
                name=name, url=url, description=description, headers=headers or {}
            )
            self._storage.add_api(api_config)
            await self.save_config()
            logger.info(f"Added API configuration: {name}")
            return f"Added API '{name}' with URL {url}"
        except ValidationError as e:
            raise ValueError(f"Invalid URL or configuration: {e}")

    async def remove_api(self, name: str) -> str:
        """Remove an API configuration."""
        if not self._storage.remove_api(name):
            raise ValueError(f"API '{name}' not found")

        await self.save_config()
        logger.info(f"Removed API configuration: {name}")
        return f"Removed API '{name}'"

    def list_apis(self) -> List[Dict[str, str]]:
        """List all API configurations."""
        return [config.to_display_dict() for config in self._storage.list_apis()]

    def get_api_url(self, api_identifier: str) -> str:
        """Get the URL for an API identifier (name or direct URL)."""
        # Try to get from saved APIs first
        api_config = self._storage.get_api(api_identifier)
        if api_config:
            return str(api_config.url)

        # Try to parse as direct URL
        try:
            parsed = urlparse(api_identifier)
            if parsed.scheme and parsed.netloc:
                return api_identifier
        except Exception:
            pass

        raise ValueError(f"Invalid API identifier: {api_identifier}")

    def get_api_config(self, api_identifier: str) -> Tuple[str, Dict[str, str]]:
        """Get API URL and headers for the given identifier."""
        # Try to get from saved APIs first
        api_config = self._storage.get_api(api_identifier)
        if api_config:
            return str(api_config.url), api_config.headers

        # Try to parse as direct URL
        try:
            parsed = urlparse(api_identifier)
            if parsed.scheme and parsed.netloc:
                return api_identifier, {}
        except Exception:
            pass

        raise ValueError(f"Invalid API identifier: {api_identifier}")

    def has_api(self, name: str) -> bool:
        """Check if an API configuration exists."""
        return self._storage.get_api(name) is not None
