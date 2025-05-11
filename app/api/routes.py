from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Dict, Any
from app.services.recommendation_service import RecommendationService
from app.services.empowerverse_api import EmpowerVerseApiService
from app.schemas.post import RecommendationResponse, FeedRequest
from app.db.database import get_db
from sqlalchemy.orm import Session
import logging
import uuid
from datetime import datetime
import httpx
import os
import csv
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG for more detailed logs
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/feed", response_model=RecommendationResponse, tags=["Recommendations"])
async def get_personalized_feed(
    username: str = Query(..., description="Username to get recommendations for"),
    project_code: Optional[str] = Query(None, description="Filter recommendations by project category"),
    page: int = Query(1, description="Page number for pagination"),
    page_size: int = Query(20, description="Number of items per page"),
    db: Session = Depends(get_db)
):
    """
    Get personalized video recommendations for a specific user.
    
    - **username**: Required. The username to get recommendations for
    - **project_code**: Optional. Filter recommendations by a specific project category
    - **page**: Page number for pagination (default: 1)
    - **page_size**: Number of items per page (default: 20)
    """
    try:
        logger.info(f"Getting recommendations for username={username}, project_code={project_code}")
        
        # Use real API with no fallback to mock data
        api_service = EmpowerVerseApiService()
        api_service.use_mock = False
        api_service.use_fallback = False
        api_service.use_cache = False
        
        logger.info(f"Using real API only (mock={api_service.use_mock}, fallback={api_service.use_fallback}, cache={api_service.use_cache})")
        
        recommendation_service = RecommendationService(db)
        recommendation_service.api_service = api_service
        
        logger.info(f"Calling recommendation service for username={username}")
        
        try:
            # Create data directory if it doesn't exist
            data_dir = os.path.join(os.getcwd(), "data")
            os.makedirs(data_dir, exist_ok=True)
            
            # Try to fetch and cache API data
            await cache_api_data(api_service, data_dir)
            
            # First try to get real recommendations from the API
            recommendations = await recommendation_service.get_personalized_feed(
                username=username,
                project_code=project_code,
                page=page,
                page_size=page_size,
                db=db
            )
            
            if recommendations and recommendations.get("post") and len(recommendations["post"]) > 0:
                logger.info(f"Successfully generated {len(recommendations['post'])} recommendations with real API")
                return recommendations
            
            logger.warning(f"Real API returned empty recommendations, generating cold start recommendations")
            
            # If no recommendations but no error, try one more time with empty response handling
            recommendations = await recommendation_service.get_personalized_feed(
                username=username,
                project_code=project_code,
                page=page,
                page_size=page_size,
                db=db
            )
            
            if recommendations and recommendations.get("post") and len(recommendations["post"]) > 0:
                logger.info(f"Successfully generated {len(recommendations['post'])} cold start recommendations")
                return recommendations
            else:
                logger.error("No recommendations could be generated even with cold start")
                return {
                    "status": "success",
                    "post": []
                }
        
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}", exc_info=True)
            
            # Return empty results rather than mock data
            return {
                "status": "success",
                "post": []
            }
            
    except Exception as e:
        logger.error(f"Unexpected error in get_personalized_feed: {str(e)}", exc_info=True)
        
        # Return empty but valid response
        return {
            "status": "success",
            "post": []
        }

async def cache_api_data(api_service: EmpowerVerseApiService, data_dir: str):
    """Cache API data to JSON files for backup purposes"""
    try:
        logger.info(f"Starting API data caching to {data_dir}")
        
        # Create the directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Define API endpoints to cache
        endpoints = {
            "viewed_posts": api_service.get_viewed_posts,
            "liked_posts": api_service.get_liked_posts,
            "inspired_posts": api_service.get_inspired_posts,
            "rated_posts": api_service.get_rated_posts,
            "all_posts": api_service.get_all_posts,
            "all_users": api_service.get_all_users
        }
        
        # Track failures
        failures = []
        
        # Fetch and cache each endpoint
        for name, fetch_func in endpoints.items():
            file_path = os.path.join(data_dir, f"{name}.json")
            
            # Skip if file exists and is recent (less than 1 day old)
            if os.path.exists(file_path) and (datetime.now().timestamp() - os.path.getmtime(file_path)) < 86400:
                logger.info(f"Using existing cached data for {name}")
                continue
                
            try:
                logger.info(f"Fetching data for {name}...")
                data = await fetch_func(page_size=1000)
                
                if data:
                    # Save as JSON
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                        
                    logger.info(f"Successfully cached {name} data to {file_path}")
                else:
                    logger.warning(f"Received empty data for {name}, skipping cache")
                    failures.append(name)
            except Exception as e:
                logger.error(f"Failed to cache {name} data: {str(e)}")
                failures.append(name)
        
        if failures:
            logger.warning(f"Failed to cache the following endpoints: {', '.join(failures)}")
        else:
            logger.info("Successfully cached all API data")
                
    except Exception as e:
        logger.error(f"Error in cache_api_data: {str(e)}", exc_info=True) 

@router.get("/status", tags=["System"])
async def get_api_status():
    """
    Get current API status and check API connectivity.
    Useful for debugging when API feed is not returning results.
    """
    try:
        logger.info("Checking API status")
        
        # Create API service
        api_service = EmpowerVerseApiService()
        
        # Test creating data directory
        data_dir = os.path.join(os.getcwd(), "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # Get API configuration
        config = {
            "api_base_url": api_service.base_url,
            "timeout": api_service.timeout,
            "flic_token_exists": bool(api_service.headers.get("Flic-Token")),
            "data_directory": data_dir,
            "data_directory_exists": os.path.exists(data_dir),
            "resonance_algorithm_exists": bool(api_service.resonance_algorithm)
        }
        
        # Check for data files
        data_files = []
        if os.path.exists(data_dir):
            data_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
        
        # Ping API to check connection
        connection_status = {
            "can_connect": False,
            "error": None
        }
        
        try:
            # Make a lightweight request to check connection
            url = f"{api_service.base_url}/users/get_all"
            params = {"page": 1, "page_size": 1}
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=api_service.headers,
                    follow_redirects=True
                )
                
                connection_status["can_connect"] = 200 <= response.status_code < 300
                connection_status["status_code"] = response.status_code
                connection_status["content_type"] = response.headers.get("content-type")
        except Exception as e:
            connection_status["error"] = str(e)
        
        return {
            "status": "up",
            "timestamp": datetime.now().isoformat(),
            "api_config": config,
            "cached_data_files": data_files,
            "api_connection": connection_status
        }
    except Exception as e:
        logger.error(f"Error checking API status: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        } 