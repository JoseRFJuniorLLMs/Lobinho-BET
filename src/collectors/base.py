"""
Base collector class with common functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential


class BaseCollector(ABC):
    """Base class for all data collectors."""

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers=self._get_headers(),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    def _get_headers(self) -> dict:
        """Get default headers for requests."""
        headers = {
            "User-Agent": "LobinhoBet/1.0",
            "Accept": "application/json",
        }
        return headers

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
    ) -> dict:
        """Make HTTP request with retry logic."""
        if not self.client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        logger.debug(f"Requesting: {method} {url}")

        response = await self.client.request(
            method=method,
            url=url,
            params=params,
            json=data,
        )
        response.raise_for_status()
        return response.json()

    async def get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """GET request."""
        return await self._request("GET", endpoint, params=params)

    async def post(self, endpoint: str, data: Optional[dict] = None) -> dict:
        """POST request."""
        return await self._request("POST", endpoint, data=data)

    @abstractmethod
    async def get_matches(self, **kwargs) -> list[dict]:
        """Get matches data."""
        pass

    @abstractmethod
    async def get_team_stats(self, team_id: str) -> dict:
        """Get team statistics."""
        pass
