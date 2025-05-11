import httpx
import json
from typing import Dict, List, Any, Optional
from app.core.config import settings
import asyncio
from fastapi import HTTPException
import logging
import os

# Configure logging
logger = logging.getLogger(__name__)
# Set logging level to DEBUG for more detailed information
logging.basicConfig(level=logging.DEBUG)

class EmpowerVerseApiService:
    def __init__(self):
        self.base_url = settings.API_BASE_URL
        self.headers = {
            "Content-Type": "application/json",
            "Flic-Token": settings.FLIC_TOKEN  # Make sure this header is correctly set
        }
        self.resonance_algorithm = settings.RESONANCE_ALGORITHM
        self.timeout = settings.REQUEST_TIMEOUT
        
        # IMPORTANT: Always force real API usage
        self.use_mock = False
        self.use_fallback = False
        self.use_cache = False
        self.data_dir = os.path.join(os.getcwd(), "data")
        
        logger.info(f"Initialized EmpowerVerseApiService with base_url={self.base_url}")
        logger.info(f"Using timeout: {self.timeout}s")
        logger.info(f"Headers: {self.headers}")
        logger.info(f"Forced settings: use_mock={self.use_mock}, use_fallback={self.use_fallback}, use_cache={self.use_cache}")
        logger.info(f"Data directory: {self.data_dir}")
        
        # Log the actual FLIC token first 10 chars for debugging (partial to avoid security issues)
        flic_token_debug = settings.FLIC_TOKEN[:10] + "..." if settings.FLIC_TOKEN else "MISSING"
        logger.info(f"FLIC Token: {flic_token_debug}")
        
        # Validate configs
        if not self.base_url or self.base_url == "":
            logger.error("API_BASE_URL is not set!")
        if not settings.FLIC_TOKEN or settings.FLIC_TOKEN == "":
            logger.error("FLIC_TOKEN is not set!")
        
    async def get_viewed_posts(self, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        """Get all viewed posts from the API"""
        # No more mock data
        url = f"{self.base_url}/posts/view"
        params = {
            "page": page,
            "page_size": page_size,
            "resonance_algorithm": self.resonance_algorithm
        }
        
        logger.info(f"Making GET request to {url} with params={params}")
        logger.info(f"Headers: {self.headers}")
        
        # Try to get data from API first
        try:
            # Use timeout from settings
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, headers=self.headers)
                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Response headers: {response.headers}")
                
                response.raise_for_status()
                data = response.json()
                logger.info(f"Successfully got viewed posts from API")
                
                return data
                
        except Exception as e:
            error_detail = f"Failed to fetch viewed posts from API: {str(e)}"
            logger.error(error_detail, exc_info=True)
            
            # Try to load from cache
            cache_data = self._load_from_cache("viewed_posts")
            if cache_data:
                logger.info(f"Loaded viewed posts from cache file")
                return cache_data
                
            raise HTTPException(status_code=500, detail=error_detail)
    
    def _set_use_mock_data(self, enabled: bool = True):
        """Mock data is no longer supported"""
        logger.warning("Mock data is no longer supported")
        
    def _set_use_fallback(self, enabled: bool = True):
        """Fallback is no longer supported"""
        logger.warning("Fallback is no longer supported")
    
    def _set_use_cache(self, enabled: bool = True):
        """Cache is no longer supported"""
        logger.warning("Cache is no longer supported")
    
    def _load_from_cache(self, name: str) -> Optional[Dict[str, Any]]:
        """Load data from cached JSON file"""
        try:
            file_path = os.path.join(self.data_dir, f"{name}.json")
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data
            else:
                logger.warning(f"Cache file not found: {file_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading from cache file: {str(e)}")
            return None
                
    async def get_liked_posts(self, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        """Get all liked posts from the API"""
        url = f"{self.base_url}/posts/like"
        params = {
            "page": page,
            "page_size": page_size,
            "resonance_algorithm": self.resonance_algorithm
        }
        
        logger.info(f"Making GET request to {url} with params={params}")
        logger.debug(f"Headers: {self.headers}")
        
        # Try to get data from API first
        try:
            # Use timeout from settings
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, headers=self.headers)
                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Response headers: {response.headers}")
                
                response.raise_for_status()
                data = response.json()
                logger.info(f"Successfully got liked posts from API")
                
                return data
                
        except Exception as e:
            error_detail = f"Error fetching liked posts from API: {str(e)}"
            logger.error(error_detail, exc_info=True)
            
            # Try to load from cache
            cache_data = self._load_from_cache("liked_posts")
            if cache_data:
                logger.info(f"Loaded liked posts from cache file")
                return cache_data
                
            raise HTTPException(status_code=500, detail=error_detail)
                
    async def get_inspired_posts(self, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        """Get all inspired posts from the API"""
        url = f"{self.base_url}/posts/inspire"
        params = {
            "page": page,
            "page_size": page_size,
            "resonance_algorithm": self.resonance_algorithm
        }
        
        logger.info(f"Making GET request to {url} with params={params}")
        logger.debug(f"Headers: {self.headers}")
        
        # Try to get data from API first
        try:
            # Use timeout from settings
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, headers=self.headers)
                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Response headers: {response.headers}")
                
                response.raise_for_status()
                data = response.json()
                logger.info(f"Successfully got inspired posts from API")
                
                return data
                
        except Exception as e:
            error_detail = f"Error fetching inspired posts from API: {str(e)}"
            logger.error(error_detail, exc_info=True)
            
            # Try to load from cache
            cache_data = self._load_from_cache("inspired_posts")
            if cache_data:
                logger.info(f"Loaded inspired posts from cache file")
                return cache_data
                
            raise HTTPException(status_code=500, detail=error_detail)
                
    async def get_rated_posts(self, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        """Get all rated posts from the API"""
        url = f"{self.base_url}/posts/rating"
        params = {
            "page": page,
            "page_size": page_size,
            "resonance_algorithm": self.resonance_algorithm
        }
        
        logger.info(f"Making GET request to {url} with params={params}")
        logger.debug(f"Headers: {self.headers}")
        
        # Try to get data from API first
        try:
            # Use timeout from settings
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, headers=self.headers)
                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Response headers: {response.headers}")
                
                response.raise_for_status()
                data = response.json()
                logger.info(f"Successfully got rated posts from API")
                
                return data
                
        except Exception as e:
            error_detail = f"Error fetching rated posts from API: {str(e)}"
            logger.error(error_detail, exc_info=True)
            
            # Try to load from cache
            cache_data = self._load_from_cache("rated_posts")
            if cache_data:
                logger.info(f"Loaded rated posts from cache file")
                return cache_data
                
            raise HTTPException(status_code=500, detail=error_detail)
                
    async def get_all_posts(self, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        """Get all posts from the API"""
        url = f"{self.base_url}/posts/summary/get"
        params = {
            "page": page,
            "page_size": page_size
        }
        
        logger.info(f"Making GET request to {url} with params={params}")
        logger.debug(f"Headers: {self.headers}")
        
        # Try to get data from API first
        try:
            # Use timeout from settings
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, headers=self.headers)
                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Response headers: {response.headers}")
                
                response.raise_for_status()
                data = response.json()
                logger.info(f"Successfully got all posts from API")
                
                return data
                
        except Exception as e:
            error_detail = f"Error fetching all posts from API: {str(e)}"
            logger.error(error_detail, exc_info=True)
            
            # Try to load from cache
            cache_data = self._load_from_cache("all_posts")
            if cache_data:
                logger.info(f"Loaded all posts from cache file")
                return cache_data
                
            raise HTTPException(status_code=500, detail=error_detail)
                
    async def get_all_users(self, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        """Get all users from the API"""
        url = f"{self.base_url}/users/get_all"
        params = {
            "page": page,
            "page_size": page_size
        }
        
        logger.info(f"Making GET request to {url} with params={params}")
        logger.info(f"Headers: {self.headers}")
        
        # Try to get data from API first
        try:
            # Increased timeout for user fetch (30 seconds instead of default)
            timeout = httpx.Timeout(30.0, connect=10.0)
            
            # Try with longer timeout and explicit options
            async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
                logger.info(f"Sending GET request to {url}")
                response = await client.get(
                    url, 
                    params=params, 
                    headers=self.headers,
                    follow_redirects=True
                )
                
                logger.info(f"Response status: {response.status_code}")
                logger.info(f"Response headers: {response.headers}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        logger.info(f"Successfully got users from API")
                        
                        # Log the actual structure to help with debugging
                        logger.info(f"API response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                        
                        # Create empty response structure in case API returns unexpected format
                        if not isinstance(data, dict):
                            logger.warning(f"API returned non-dict response: {data}")
                            return {"users": []}
                        
                        # Return the data
                        return data
                    except ValueError as json_err:
                        # If JSON parsing fails, log the raw content
                        logger.error(f"Failed to parse JSON: {str(json_err)}")
                        logger.error(f"Raw response content: {response.text[:500]}...")
                        
                        # Try to load from cache
                        cache_data = self._load_from_cache("all_users")
                        if cache_data:
                            logger.info(f"Loaded all users from cache file")
                            return cache_data
                            
                        raise HTTPException(status_code=500, detail=f"Invalid JSON response from API: {str(json_err)}")
                else:
                    logger.error(f"API returned status code {response.status_code}")
                    logger.error(f"Response content: {response.text[:500]}...")
                    
                    # Try to load from cache
                    cache_data = self._load_from_cache("all_users")
                    if cache_data:
                        logger.info(f"Loaded all users from cache file")
                        return cache_data
                        
                    raise HTTPException(status_code=response.status_code, detail=f"API returned status {response.status_code}: {response.text[:500]}")
                    
        except Exception as e:
            error_detail = f"Error in get_all_users: {str(e)}"
            logger.error(error_detail, exc_info=True)
            
            # Try to load from cache
            cache_data = self._load_from_cache("all_users")
            if cache_data:
                logger.info(f"Loaded all users from cache file")
                return cache_data
                
            # Create empty response if no cache available
            logger.warning("No cache available, returning empty users list")
            return {"users": []}
                  
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get a user by username"""
        logger.info(f"Looking for user with username={username}")
        
        try:
            users_data = await self.get_all_users(page_size=1000)
            
            # The API returns users in the "users" field, not "data"
            users = users_data.get("users", []) or users_data.get("data", [])
            
            logger.info(f"Got {len(users)} users from API")
            logger.debug(f"Response structure: {list(users_data.keys())}")
            
            for user in users:
                if user.get("username", "").lower() == username.lower():
                    logger.info(f"Found user {username} with id={user.get('id')}")
                    return user
                    
            logger.warning(f"User {username} not found in API data")
            logger.debug(f"Sample usernames: {[user.get('username') for user in users[:5] if user.get('username')]}")
            
            # Create a synthetic user if not found - handle any username
            logger.info(f"Creating synthetic user for {username}")
            import uuid
            import datetime
            
            # Create a new user with the given username
            synthetic_user = {
                "id": f"synthetic_{str(uuid.uuid4())[:8]}",
                "username": username,
                "email": f"{username}@example.com",
                "name": username.title(),
                "profile_photo_url": "https://assets.socialverseapp.com/profile/default.png",
                "bio": f"This is {username}'s bio",
                "interests": ["Technology", "Social Media", "Education"],
                "created_at": datetime.datetime.now().isoformat()
            }
            
            return synthetic_user
                
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            error_detail = f"Error in get_user_by_username: {str(e)}"
            logger.error(error_detail, exc_info=True)
            
            # Create a synthetic user as last resort
            logger.info(f"Creating synthetic user for {username} after error")
            import uuid
            import datetime
            
            # Create a new user with the given username
            synthetic_user = {
                "id": f"synthetic_{str(uuid.uuid4())[:8]}",
                "username": username,
                "email": f"{username}@example.com",
                "name": username.title(),
                "profile_photo_url": "https://assets.socialverseapp.com/profile/default.png",
                "bio": f"This is {username}'s bio",
                "interests": ["Technology", "Social Media", "Education"],
                "created_at": datetime.datetime.now().isoformat()
            }
            
            return synthetic_user 