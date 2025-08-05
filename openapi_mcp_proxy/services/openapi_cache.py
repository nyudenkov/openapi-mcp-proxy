"""OpenAPI schema caching service."""

import hashlib
import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class OpenAPICache:
    """Cache for OpenAPI schemas to avoid repeated downloads"""

    def __init__(self, timeout: float = 30.0):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._client = httpx.AsyncClient(timeout=timeout)

    async def get_schema(
        self, url: str, headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Get OpenAPI schema, using cache if available"""
        cache_key = self._generate_cache_key(url, headers)

        if cache_key not in self._cache:
            schema = await self._fetch_schema(url, headers)
            self._cache[cache_key] = schema
            logger.info(f"Cached OpenAPI schema from {url}")

        return self._cache[cache_key]

    async def _fetch_schema(
        self, url: str, headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Fetch OpenAPI schema from URL."""
        try:
            response = await self._client.get(url, headers=headers)
            response.raise_for_status()
            schema = response.json()
            logger.info(f"Successfully fetched schema from {url}")
            return schema
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching schema from {url}: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error fetching schema from {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching schema from {url}: {e}")
            raise

    def _generate_cache_key(
        self, url: str, headers: Optional[Dict[str, str]] = None
    ) -> str:
        """Generate cache key for URL and headers combination."""
        cache_key = url
        if headers:
            headers_hash = hashlib.md5(
                str(sorted(headers.items())).encode()
            ).hexdigest()
            cache_key = f"{url}#{headers_hash}"
        return cache_key

    def clear_cache(self) -> None:
        """Clear all cached schemas."""
        self._cache.clear()
        logger.info("Cleared OpenAPI schema cache")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "cached_schemas": len(self._cache),
        }

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
        logger.info("Closed OpenAPI cache HTTP client")
