import os
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # API Configuration - HARDCODED FOR RELIABILITY
    API_BASE_URL: str = "https://api.socialverseapp.com"
    FLIC_TOKEN: str = "flic_11d3da28e403d182c36a3530453e290add87d0b4a40ee50f17611f180d47956f"
    RESONANCE_ALGORITHM: str = "resonance_algorithm_cjsvervb7dbhss8bdrj89s44jfjdbsjd0xnjkbvuire8zcjwerui3njfbvsujc5if"
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Cache Configuration
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # Cache time-to-live in seconds
    CACHE_DIR: str = os.getenv("CACHE_DIR", "data_cache")
    
    # API Request Configuration
    REQUEST_TIMEOUT: float = float(os.getenv("REQUEST_TIMEOUT", "30.0"))  # Increased timeout for API calls
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    PAGE_SIZE: int = int(os.getenv("PAGE_SIZE", "1000"))  # Increased page size
    
    # Feature Flags - FORCE REAL API
    USE_FALLBACK: bool = False  # Never use fallbacks
    USE_MOCK_DATA: bool = False  # Never use mock data
    USE_CACHE: bool = False     # Don't use cache
    
    # Default headers for API requests
    DEFAULT_HEADERS: Dict[str, str] = {
        "Content-Type": "application/json",
        "Flic-Token": "flic_11d3da28e403d182c36a3530453e290add87d0b4a40ee50f17611f180d47956f"
    }
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        return {
            "Content-Type": "application/json",
            "Flic-Token": self.FLIC_TOKEN
        }

# Create global settings object
settings = Settings() 