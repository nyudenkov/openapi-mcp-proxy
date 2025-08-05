"""Endpoint information models."""

from typing import List, Optional

from pydantic import BaseModel

from openapi_mcp_proxy.models.pagination import EndpointFilterParams


class EndpointInfo(BaseModel):
    """Information about an API endpoint"""

    path: str
    method: str
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    operation_id: Optional[str] = None
    deprecated: bool = False
    has_authentication: bool = False

    def matches_query(self, query: str) -> bool:
        """Check if this endpoint matches a search query."""
        query_lower = query.lower()
        search_text = " ".join(
            [
                self.path,
                self.summary or "",
                self.description or "",
                " ".join(self.tags),
            ]
        ).lower()

        return query_lower in search_text

    def matches_filters(self, filters: EndpointFilterParams) -> bool:
        """Check if this endpoint matches the provided filters."""
        if filters.methods and self.method not in filters.methods:
            return False

        if filters.tags_include:
            if not any(tag in self.tags for tag in filters.tags_include):
                return False

        if filters.tags_exclude:
            if any(tag in self.tags for tag in filters.tags_exclude):
                return False

        if filters.has_authentication is not None:
            if self.has_authentication != filters.has_authentication:
                return False

        if filters.deprecated is not None:
            if self.deprecated != filters.deprecated:
                return False

        return True

    def format_display(self) -> str:
        """Format endpoint for display."""
        result = f"{self.method} {self.path}"
        if self.summary:
            result += f" - {self.summary}"
        if self.tags:
            result += f" [Tags: {', '.join(self.tags)}]"
        if self.deprecated:
            result += " [DEPRECATED]"
        if self.has_authentication:
            result += " [AUTH]"
        return result
