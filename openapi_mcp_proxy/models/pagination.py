"""Pagination and filtering models for MCP tools."""

from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field, validator

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters for list operations."""

    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(
        default=50, ge=1, le=100, description="Items per page (max 100)"
    )

    @validator("page_size")
    def validate_page_size(cls, v):
        if v > 100:
            raise ValueError("page_size cannot exceed 100")
        return v

    def get_offset(self) -> int:
        """Calculate offset for pagination."""
        return (self.page - 1) * self.page_size

    def get_limit(self) -> int:
        """Get the limit for pagination."""
        return self.page_size


class PaginationResult(BaseModel, Generic[T]):
    """Paginated result wrapper."""

    items: List[T]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool

    @classmethod
    def create(
        cls, items: List[T], total_count: int, params: PaginationParams
    ) -> "PaginationResult[T]":
        """Create a paginated result from items and parameters."""
        total_pages = (total_count + params.page_size - 1) // params.page_size
        has_next = params.page < total_pages
        has_previous = params.page > 1

        return cls(
            items=items,
            total_count=total_count,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous,
        )

    def format_navigation(self) -> str:
        """Format navigation information for display."""
        start_item = (self.page - 1) * self.page_size + 1
        end_item = min(self.page * self.page_size, self.total_count)

        result = f"Results: {start_item}-{end_item} of {self.total_count}"
        if self.total_pages > 1:
            result += f" (Page {self.page} of {self.total_pages})"

        if self.total_pages > 1:
            result += "\n\nNavigation:"
            if self.has_previous:
                result += f"\n- Previous: Page {self.page - 1}"
            if self.has_next:
                result += f"\n- Next: Page {self.page + 1}"
            result += "\n- Use 'page' parameter to navigate"

        return result


class FilterParams(BaseModel):
    """Base class for filter parameters."""

    pass


class EndpointFilterParams(FilterParams):
    """Filter parameters for endpoints."""

    methods: Optional[List[str]] = Field(
        default=None, description="Filter by HTTP methods (e.g., ['GET', 'POST'])"
    )
    tags_include: Optional[List[str]] = Field(
        default=None, description="Include endpoints with these tags"
    )
    tags_exclude: Optional[List[str]] = Field(
        default=None, description="Exclude endpoints with these tags"
    )
    has_authentication: Optional[bool] = Field(
        default=None, description="Filter by authentication requirement"
    )
    deprecated: Optional[bool] = Field(
        default=None, description="Filter by deprecation status"
    )

    @validator("methods")
    def validate_methods(cls, v):
        if v is not None:
            valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
            invalid_methods = [m for m in v if m.upper() not in valid_methods]
            if invalid_methods:
                raise ValueError(f"Invalid HTTP methods: {invalid_methods}")
            return [m.upper() for m in v]
        return v

    def format_display(self) -> str:
        """Format applied filters for display."""
        filters = []

        if self.methods:
            filters.append(f"Methods: {', '.join(self.methods)}")

        if self.tags_include:
            filters.append(f"Tags Include: [{', '.join(self.tags_include)}]")

        if self.tags_exclude:
            filters.append(f"Tags Exclude: [{', '.join(self.tags_exclude)}]")

        if self.has_authentication is not None:
            filters.append(f"Has Authentication: {self.has_authentication}")

        if self.deprecated is not None:
            filters.append(f"Deprecated: {self.deprecated}")

        if not filters:
            return ""

        return "Applied Filters:\n" + "\n".join(f"- {f}" for f in filters)


class ModelFilterParams(FilterParams):
    """Filter parameters for models."""

    types: Optional[List[str]] = Field(
        default=None,
        description="Filter by model types (e.g., ['object', 'array', 'string'])",
    )
    min_properties: Optional[int] = Field(
        default=None, ge=0, description="Minimum number of properties"
    )
    max_properties: Optional[int] = Field(
        default=None, ge=0, description="Maximum number of properties"
    )
    has_required_fields: Optional[bool] = Field(
        default=None, description="Filter by presence of required fields"
    )
    tags_include: Optional[List[str]] = Field(
        default=None, description="Include models with these tags"
    )
    tags_exclude: Optional[List[str]] = Field(
        default=None, description="Exclude models with these tags"
    )

    @validator("max_properties")
    def validate_max_properties(cls, v, values):
        if (
            v is not None
            and "min_properties" in values
            and values["min_properties"] is not None
        ):
            if v < values["min_properties"]:
                raise ValueError("max_properties cannot be less than min_properties")
        return v

    def format_display(self) -> str:
        """Format applied filters for display."""
        filters = []

        if self.types:
            filters.append(f"Types: {', '.join(self.types)}")

        if self.min_properties is not None:
            filters.append(f"Min Properties: {self.min_properties}")

        if self.max_properties is not None:
            filters.append(f"Max Properties: {self.max_properties}")

        if self.has_required_fields is not None:
            filters.append(f"Has Required Fields: {self.has_required_fields}")

        if self.tags_include:
            filters.append(f"Tags Include: [{', '.join(self.tags_include)}]")

        if self.tags_exclude:
            filters.append(f"Tags Exclude: [{', '.join(self.tags_exclude)}]")

        if not filters:
            return ""

        return "Applied Filters:\n" + "\n".join(f"- {f}" for f in filters)
