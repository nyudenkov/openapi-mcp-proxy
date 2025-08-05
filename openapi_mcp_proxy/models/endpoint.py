"""Endpoint information models."""

from typing import List, Optional

from pydantic import BaseModel


class EndpointInfo(BaseModel):
    """Information about an API endpoint"""

    path: str
    method: str
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    operation_id: Optional[str] = None

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

    def format_display(self) -> str:
        """Format endpoint for display."""
        result = f"{self.method} {self.path}"
        if self.summary:
            result += f" - {self.summary}"
        if self.tags:
            result += f" [Tags: {', '.join(self.tags)}]"
        return result
