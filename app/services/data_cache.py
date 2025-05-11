import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

class DataCache:
    """Cache service to store API responses for better performance and reliability"""
    
    def __init__(self, cache_dir: str = "data_cache", ttl_hours: int = 24):
        self.cache_dir = cache_dir
        self.ttl = timedelta(hours=ttl_hours)
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            logger.info(f"Created cache directory: {cache_dir}")
    
    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache if it exists and is not expired"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if not os.path.exists(cache_file):
            return None
            
        try:
            # Check file modification time to see if cache is expired
            mod_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if datetime.now() - mod_time > self.ttl:
                logger.info(f"Cache expired for {cache_key}")
                return None
                
            # Read and parse the cache file
            with open(cache_file, 'r') as f:
                data = json.load(f)
                logger.info(f"Retrieved data from cache: {cache_key}")
                return data
        except Exception as e:
            logger.error(f"Error reading cache for {cache_key}: {str(e)}")
            return None
    
    def set(self, cache_key: str, data: Dict[str, Any]) -> bool:
        """Save data to cache"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f)
            logger.info(f"Saved data to cache: {cache_key}")
            return True
        except Exception as e:
            logger.error(f"Error saving cache for {cache_key}: {str(e)}")
            return False
    
    def clear(self, cache_key: Optional[str] = None) -> bool:
        """Clear specific cache item or all cache"""
        try:
            if cache_key:
                # Delete specific cache file
                cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
                if os.path.exists(cache_file):
                    os.remove(cache_file)
                    logger.info(f"Cleared cache for {cache_key}")
            else:
                # Delete all cache files
                for filename in os.listdir(self.cache_dir):
                    if filename.endswith(".json"):
                        os.remove(os.path.join(self.cache_dir, filename))
                logger.info("Cleared all cache")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False
            
# Create a global instance
data_cache = DataCache() 