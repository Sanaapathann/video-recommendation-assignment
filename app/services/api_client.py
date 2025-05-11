import httpx
from fastapi import HTTPException
from typing import Dict, Any, Optional
from app.core.config import settings
import logging

# Configure logging
logger = logging.getLogger(__name__)

class ApiClient:
    """
    A simplified API client for making requests to the external API
    """
    def __init__(self):
        self.base_url = settings.API_BASE_URL
        self.headers = settings.get_auth_headers()
        
    async def fetch_data(self, endpoint: str, params: dict) -> Dict[str, Any]:
        """
        Fetch data from the API with error handling
        """
        url = f"{self.base_url}{endpoint}"
        logger.info(f"Making GET request to {url} with params={params}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, params=params, headers=self.headers)
                logger.debug(f"Response status: {response.status_code}")
                
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                error_detail = f"API error: {e.response.status_code} - {e.response.text}"
                logger.error(error_detail)
                raise HTTPException(status_code=e.response.status_code, detail=error_detail)
            except httpx.ReadTimeout as e:
                error_detail = f"API request timed out: {str(e)}"
                logger.error(error_detail)
                raise HTTPException(status_code=504, detail=error_detail)
            except Exception as e:
                error_detail = f"Failed to fetch data: {str(e)}"
                logger.error(error_detail, exc_info=True)
                raise HTTPException(status_code=500, detail=error_detail)
                
    async def get_users(self, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        """Get all users from the API"""
        endpoint = "/users/get_all"
        params = {
            "page": page,
            "page_size": page_size
        }
        return await self.fetch_data(endpoint, params)
        
    async def get_posts(self, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        """Get all posts from the API"""
        endpoint = "/posts/summary/get"
        params = {
            "page": page,
            "page_size": page_size
        }
        return await self.fetch_data(endpoint, params)
        
    async def get_post_interactions(self, interaction_type: str, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        """Get post interactions (views, likes, inspires, ratings)"""
        endpoint = f"/posts/{interaction_type}"
        params = {
            "page": page,
            "page_size": page_size,
            "resonance_algorithm": settings.RESONANCE_ALGORITHM
        }
        return await self.fetch_data(endpoint, params) 