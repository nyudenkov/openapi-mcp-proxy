"""Schema and model information."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from openapi_mcp_proxy.models.pagination import ModelFilterParams


class ModelInfo(BaseModel):
    """Information about a data model"""

    name: str
    type: str = "object"
    properties: Dict[str, Any] = {}
    required: List[str] = []
    description: Optional[str] = None
    tags: List[str] = []

    def matches_filters(self, filters: ModelFilterParams) -> bool:
        """Check if this model matches the provided filters."""
        if filters.types and self.type not in filters.types:
            return False

        prop_count = len(self.properties)
        if filters.min_properties is not None and prop_count < filters.min_properties:
            return False
        if filters.max_properties is not None and prop_count > filters.max_properties:
            return False

        if filters.has_required_fields is not None:
            has_required = len(self.required) > 0
            if has_required != filters.has_required_fields:
                return False

        if filters.tags_include:
            if not any(tag in self.tags for tag in filters.tags_include):
                return False

        if filters.tags_exclude:
            if any(tag in self.tags for tag in filters.tags_exclude):
                return False

        return True

    def format_display(self, detailed: bool = False) -> str:
        """Format model for display."""
        result = f"- {self.name} ({self.type})"

        if detailed:
            if self.description:
                result += f" - {self.description}"
            result += f" [{len(self.properties)} properties"
            if self.required:
                result += f", {len(self.required)} required"
            result += "]"
            if self.tags:
                result += f" [Tags: {', '.join(self.tags)}]"

        return result

    def get_property_count(self) -> int:
        """Get the number of properties in this model."""
        return len(self.properties)

    def get_required_count(self) -> int:
        """Get the number of required properties."""
        return len(self.required)


class ApiInfo(BaseModel):
    """General information about an API."""

    title: str
    version: str
    description: str = ""
    base_url: str
    tags: List[str] = []

    def format_display(self) -> str:
        """Format API info for display."""
        result = f"API: {self.title} (v{self.version})\n"
        result += f"Description: {self.description}\n"
        result += f"Base URL: {self.base_url}\n"
        if self.tags:
            result += f"Tags: {', '.join(self.tags)}\n"

        return result
