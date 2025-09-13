"""
API client for communicating with echo-mcp-server.
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config.settings import settings


logger = logging.getLogger(__name__)


class ServerAPIClient:
    """Client for interacting with the echo-mcp-server API."""

    def __init__(self):
        self.base_url = f"{settings.server_host}{settings.server_api_prefix}"
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.request_timeout),
            headers={"Content-Type": "application/json"}
        )
        # Authentication removed for hackathon demo
        # self._auth_token = settings.jwt_token

    # Authentication removed for hackathon demo
    # def set_auth_token(self, token: str):
    #     """Set the authentication token."""
    #     self._auth_token = token
    #     self.client.headers.update({"Authorization": f"Bearer {token}"})

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request with retry logic."""
        url = f"{self.base_url}{endpoint}"

        @retry(
            stop=stop_after_attempt(settings.retry_attempts),
            wait=wait_exponential(multiplier=1, min=4, max=10)
        )
        async def _request():
            try:
                if method.upper() == "GET":
                    response = await self.client.get(url, params=params)
                elif method.upper() == "POST":
                    response = await self.client.post(url, json=data)
                elif method.upper() == "PUT":
                    response = await self.client.put(url, json=data)
                elif method.upper() == "DELETE":
                    response = await self.client.delete(url)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Request failed: {e}")
                raise

        return await _request()

    # Authentication endpoints
    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """Login user and get JWT token."""
        data = {"username": username, "password": password}
        response = await self._make_request("POST", "/auth/login", data)
        if response.get("status") == "success":
            token = response["data"]["access_token"]
            self.set_auth_token(token)
        return response

    async def register(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """Register a new user."""
        data = {"username": username, "email": email, "password": password}
        return await self._make_request("POST", "/auth/register", data)

    # Service endpoints
    async def get_services(self) -> List[Dict[str, Any]]:
        """Get all available services."""
        response = await self._make_request("GET", "/services/")
        if response.get("status") == "success":
            return response["data"]
        return []

    async def get_service_details(self, service_id: int) -> Dict[str, Any]:
        """Get details of a specific service."""
        response = await self._make_request("GET", f"/services/{service_id}")
        return response

    async def add_service_to_agent(self, service_id: int) -> Dict[str, Any]:
        """Add a service to the user's agent."""
        data = {"service_id": service_id}
        return await self._make_request("POST", "/services/user/agent/services", data)

    async def remove_service_from_agent(self, service_id: int) -> Dict[str, Any]:
        """Remove a service from the user's agent."""
        return await self._make_request("DELETE", f"/services/user/agent/services/{service_id}")

    async def get_user_agent_services(self) -> List[Dict[str, Any]]:
        """Get all services added to the user's agent."""
        response = await self._make_request("GET", "/services/user/agent/services")
        if response.get("status") == "success":
            return response["data"]["services"]
        return []

    # Chat endpoints
    async def send_message(self, receiver_id: int, content: str) -> Dict[str, Any]:
        """Send a chat message."""
        data = {"receiver_id": receiver_id, "content": content}
        return await self._make_request("POST", "/chat/send", data)

    async def get_chat_history(self, other_user_id: int) -> List[Dict[str, Any]]:
        """Get chat history with another user."""
        response = await self._make_request("GET", f"/chat/history/{other_user_id}")
        if response.get("status") == "success":
            return response["data"]
        return []

    # Authentication removed for hackathon demo
    # User endpoints
    # async def get_current_user(self) -> Dict[str, Any]:
    #     """Get current user information."""
    #     return await self._make_request("GET", "/auth/me")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Global client instance
api_client = ServerAPIClient()
