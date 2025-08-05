"""API configuration models."""

from typing import Dict, Optional

from pydantic import BaseModel, HttpUrl


class ApiConfig(BaseModel):
    """Configuration for a saved API"""

    name: str
    url: HttpUrl
    description: Optional[str] = None
    headers: Dict[str, str] = {}

    def to_display_dict(self) -> Dict[str, str]:
        """Convert to dictionary for display purposes."""
        return {
            "name": self.name,
            "url": str(self.url),
            "description": self.description or "",
        }


class ApiConfigStorage(BaseModel):
    """Storage model for API configurations"""

    apis: Dict[str, ApiConfig] = {}

    def add_api(self, config: ApiConfig) -> None:
        """Add an API configuration."""
        self.apis[config.name] = config

    def remove_api(self, name: str) -> bool:
        """Remove an API configuration. Returns True if removed, False if not found."""
        if name in self.apis:
            del self.apis[name]
            return True
        return False

    def get_api(self, name: str) -> Optional[ApiConfig]:
        """Get an API configuration by name."""
        return self.apis.get(name)

    def list_apis(self) -> list[ApiConfig]:
        """Get all API configurations."""
        return list(self.apis.values())
